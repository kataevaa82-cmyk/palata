extends SceneTree

const ProgressGuard := preload("res://scripts/tests/progress_guard.gd")

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	ProgressGuard.snapshot()
	var failures: Array[String] = []
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game := packed.instantiate()
	root.add_child(game)
	for _frame in 3:
		await process_frame
	var hud := game.get_node("HUD")
	var platform := game.get_node_or_null("YandexSDK")
	# This regression describes night 1. Do not inherit the user's selected
	# night or an interstitial requirement from a previous test run.
	LevelManager.selected_index = 0
	if platform:
		platform.progress["selected_night"] = 0
		platform.progress["shifts_finished"] = 0
	hud._start_pressed()
	# Starting a night hops through the between-levels interstitial once the
	# player has finished a shift before, so the shift begins on the ad's
	# callback a frame later rather than inside the button press.
	for _frame in 3:
		await process_frame
	var manager := game.get_node("CareManager")
	var state := game.get_node("HospitalState")
	var player := game.get_node("Player")
	var hospital := game.get_node("HospitalModel")

	var care_nodes := get_nodes_in_group("care_interactables")
	var patients := get_nodes_in_group("care_patients")
	if care_nodes.size() < 15:
		failures.append("care_props_%d" % care_nodes.size())
	if patients.size() != 7:
		failures.append("patients_%d" % patients.size())
	if hospital.find_child("interaction_old_wall_clock", true, false):
		failures.append("second_clock_present")
	if game.has_node("RuleManager") or game.has_node("HUD/RulesPanel"):
		failures.append("rules_present")
	for procedure_prop in [
		"procedure_syringe", "procedure_surgical_scissors", "procedure_hemostatic_clamp",
		"procedure_scalpel", "procedure_kidney_dish", "procedure_ampoule_rack",
		"procedure_gauze_jar_0", "procedure_wall_sphygmomanometer", "procedure_sterilizer_drum"
	]:
		if not hospital.find_child(procedure_prop, true, false):
			failures.append("missing_%s" % procedure_prop)
	_check_mount(hospital, "interaction_assignment_board", Vector3(4.50, 1.84, -1.505), failures)
	_check_mount(hospital, "interaction_emergency_button", Vector3(-1.0, 1.34, -1.405), failures)
	_check_mount(hospital, "interaction_fire_exit_seal", Vector3(20.365, 1.35, -1.10), failures)
	var room_signs := 0
	for node in _all_nodes(hospital):
		if "sign_text" in String(node.name).to_lower():
			room_signs += 1
	if room_signs < 12:
		failures.append("room_signs_%d" % room_signs)

	var phone := get_first_node_in_group("hospital_phone")
	if not phone:
		failures.append("hospital_phone")
	else:
		# Reading the board must make care tasks playable even if the phone has
		# never rung. Calls remain narrative notifications, not a progression lock.
		var assignment_board := hospital.find_child("interaction_assignment_board", true, false) as Node3D
		manager.interact_object("assignment_board", assignment_board)
		if manager.active_assignment != "medication" or not "vitals" in manager.assignment_queue:
			failures.append("care_requires_phone_ring")
		# Keep the remainder of this broad regression test on its original,
		# phone-by-phone setup after proving the optional-phone path above.
		manager.active_assignment = ""
		manager.assignment_queue.clear()
		manager.completed_assignments.clear()
		manager.stage = "idle"
		# Reading the board legitimately starts night 1's room-4 story call. End
		# that narrative call before exercising the care-call path in isolation.
		phone.call_queue.clear()
		phone._stop_call()
		phone.start_call("care_medication")
		phone.interact(player)
		if manager.active_assignment != "medication":
			failures.append("phone_care_assignment")
	var aminazine := hospital.find_child("interaction_med_aminazine", true, false) as Node3D
	manager.interact_object("med_aminazine", aminazine)
	await process_frame
	if not aminazine or aminazine.visible or not player.held_item_copy:
		failures.append("visible_inventory_pickup")
	elif _mesh_count(player.held_item_copy) < 1:
		failures.append("visible_inventory_mesh")
	var restraints_source := hospital.find_child("interaction_patient_restraints", true, false) as Node3D
	manager.interact_object("patient_restraints", restraints_source)
	await process_frame
	if not aminazine.visible or not manager.carried_item.is_empty() or not manager.has_patient_restraints:
		failures.append("medicine_not_restored_for_restraints")
	manager.interact_object("med_aminazine", aminazine)
	await process_frame
	if not restraints_source.visible or manager.has_patient_restraints or manager.carried_item != "aminazine":
		failures.append("restraints_not_restored_for_medicine")
	var saveliev := _patient_by_id(patients, "saveliev")
	manager.interact_patient("saveliev", "Савельев П. М.", 4, 1, saveliev)
	if not state.tasks.get("care_medication", false):
		failures.append("medication_mission")
	if not aminazine.visible:
		failures.append("medicine_not_restored_after_use")

	manager.accept_phone_assignment("vitals")
	var sanity_before: int = player.sanity
	var cordiamin := hospital.find_child("interaction_med_cordiamin", true, false) as Node3D
	manager.interact_object("med_cordiamin", cordiamin)
	var levchenko := _patient_by_id(patients, "levchenko")
	manager.interact_patient("levchenko", "Левченко А. Н.", 2, 1, levchenko)
	if player.sanity >= sanity_before:
		failures.append("wrong_medicine_sanity")
	await process_frame
	var head_nurses := get_nodes_in_group("head_nurse_inspectors")
	if head_nurses.size() != 1:
		failures.append("head_nurse_not_spawned_%d" % head_nurses.size())
	else:
		var inspector := head_nurses[0] as Node3D
		var inspector_model := inspector.get_node_or_null("Model") as Node3D
		if not inspector_model or inspector_model.scale.x < 1.15 or inspector.get("beam_color").b < 0.9:
			failures.append("head_nurse_size_or_blue_beam")
		if inspector.get("health_damage") != 0 or inspector.get("max_sanity_damage_total") > 20 or not inspector.get("recovery_hint_on_exit"):
			failures.append("head_nurse_nonlethal_balance")
		var health_before_inspection: int = player.health
		player.sanity = 12
		for _tick in 4:
			inspector.call("_apply_sanity_damage")
		if player.dead or player.sanity < 5 or player.health != health_before_inspection:
			failures.append("head_nurse_attack_became_lethal")
		for part in _all_nodes(inspector):
			if part is Node3D and "bucket" in String(part.name).to_lower() and (part as Node3D).visible:
				failures.append("head_nurse_bucket_visible")
				break
		player.global_position = Vector3(7.5, 0.08, -3.8)
		if not player.is_in_doctors_room() or inspector.call("_has_clear_sight"):
			failures.append("head_nurse_doctors_room_safety")
		inspector.queue_free()
		await process_frame
	# The inspector scenario deliberately leaves sanity at five. Restore it
	# before unrelated task triggers: otherwise their initial pressure kills
	# the player and every later healing/computer/combat assertion is invalid.
	player.restore_sanity(player.max_sanity)
	manager.interact_object("med_thermometer", hospital.find_child("interaction_med_thermometer", true, false))
	manager.interact_patient("levchenko", "Левченко А. Н.", 2, 1, levchenko)
	if not state.tasks.get("care_vitals", false):
		failures.append("vitals_mission")

	manager.accept_phone_assignment("linen")
	manager.interact_object("clean_linen", null)
	var morozov := _patient_by_id(patients, "morozov")
	manager.interact_patient("morozov", "Морозов И. П.", 1, 1, morozov)
	manager.interact_object("laundry_basket", null)
	if not state.tasks.get("care_linen", false):
		failures.append("linen_mission")

	manager.trigger_water_spill()
	manager.interact_object("water_spill", null)
	if not manager.spill_active:
		failures.append("spill_cleaned_without_mop")
	manager.interact_object("mop_bucket", null)
	manager.interact_object("water_spill", null)
	if manager.spill_active or not state.tasks.get("spill_cleanup", false):
		failures.append("spill_cleanup")

	# A free tool (fuses, radiator key, extinguisher, zero key) may be picked up
	# with no assignment running, and swapping it for the mop must stay clean:
	# both paths used to index ASSIGNMENTS[""] and throw mid-pickup, leaving the
	# item in hand but the HUD and the held-item model un-refreshed.
	var fuses := hospital.find_child("interaction_spare_fuses", true, false)
	manager.interact_object("spare_fuses", fuses)
	if manager.carried_item != "fuse":
		failures.append("free_tool_pickup_%s" % manager.carried_item)
	if manager.active_assignment.is_empty() and manager.stage != "idle":
		failures.append("free_tool_stage_%s" % manager.stage)
	manager.interact_object("mop_bucket", null)
	if not manager.has_mop or not manager.carried_item.is_empty():
		failures.append("free_tool_to_mop_%s_mop=%s" % [manager.carried_item, manager.has_mop])
	if not fuses.visible:
		failures.append("free_tool_source_not_restored")

	player.health = 40
	player.global_position = Vector3(7.5, 0.08, -3.8)
	player.call("_update_doctors_room_healing", 1.6)
	if player.health < 49:
		failures.append("doctors_room_health_%d" % player.health)
	player.sanity = 25
	player.sanity_changed.emit(player.sanity)
	await process_frame
	if hud.sanity_whiteout.color.a <= 0.05:
		failures.append("sanity_whiteout")
	player.sanity = 94
	player.sanity_changed.emit(player.sanity)
	manager.interact_object("doctors_computer", hospital.find_child("interaction_doctors_computer", true, false))
	await create_timer(0.7).timeout
	if player.sanity != player.max_sanity:
		failures.append("computer_sanity_%d" % player.sanity)

	var anomaly_manager := game.get_node("AnomalyManager")
	var before_anomaly: int = player.sanity
	anomaly_manager.activate("anatomy_poster")
	if player.sanity >= before_anomaly:
		failures.append("anomaly_sanity")

	# Completing five night-1 tasks now fires the violent-patient story beat.
	# Remove that danger before testing hostile-orderly spawning in isolation;
	# production correctly refuses to run two lethal encounters at once.
	for violent in get_nodes_in_group("violent_patients"):
		violent.queue_free()
	await process_frame
	var orderly: Node3D = anomaly_manager.spawn_hostile_orderly()
	await physics_frame
	if not orderly or not orderly.is_in_group("hostile_orderlies"):
		failures.append("hostile_orderly")
	else:
		orderly.global_position = Vector3(3.0, 0.05, 0.0)
		player.global_position = Vector3(3.0, 0.08, 2.6)
		if orderly.call("_has_clear_sight"):
			failures.append("orderly_hits_inside_room")
		player.global_position = Vector3(0.0, 0.08, 0.0)
		await physics_frame
		var health_before: int = player.health
		orderly.call("_physics_process", 1.2)
		if player.health >= health_before:
			failures.append("orderly_eye_damage")

	# Open the procedure door and physically move a player capsule through its doorway.
	var procedure_door := hospital.find_child("pivot_hospital_door_N_4", true, false)
	if not procedure_door:
		failures.append("procedure_door")
	else:
		if not procedure_door.opened:
			procedure_door.interact(player)
		await create_timer(0.9).timeout
		player.set_physics_process(false)
		player.global_position = Vector3(-2.5, 0.08, -0.15)
		for _step in 105:
			player.velocity = Vector3(0.0, 0.0, -2.1)
			player.move_and_slide()
			await physics_frame
		if player.global_position.z > -2.15:
			for collision_index in player.get_slide_collision_count():
				var collision_info: KinematicCollision3D = player.get_slide_collision(collision_index)
				var collider := collision_info.get_collider() as Node
				print("PROCEDURE_COLLIDER ", collider.get_path() if collider else "none", " normal=", collision_info.get_normal())
			failures.append("procedure_blocked_%.2f" % player.global_position.z)

	print("CARE_GAMEPLAY props=", care_nodes.size(), " patients=", patients.size(), " signs=", room_signs, " failures=", failures.size())
	if not failures.is_empty():
		print("CARE_FAILURES ", failures)
	ProgressGuard.restore()
	quit(0 if failures.is_empty() else 1)

func _patient_by_id(patients: Array[Node], id: String) -> Node3D:
	for patient in patients:
		if patient.get("patient_id") == id:
			return patient as Node3D
	return null

func _all_nodes(node: Node) -> Array[Node]:
	var result: Array[Node] = [node]
	for child in node.get_children():
		result.append_array(_all_nodes(child))
	return result

func _mesh_count(node: Node) -> int:
	var count := 0
	for child in _all_nodes(node):
		if child is MeshInstance3D:
			count += 1
	return count

func _check_mount(hospital: Node, name: String, expected: Vector3, failures: Array[String]) -> void:
	var object := hospital.find_child(name, true, false) as Node3D
	if not object:
		failures.append("mount_missing_%s" % name)
	elif object.global_position.distance_to(expected) > 0.08:
		failures.append("mount_%s_%s" % [name, object.global_position])
