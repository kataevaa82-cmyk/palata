extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var failures: Array[String] = []
	var patient_scene: PackedScene = load("res://assets/models/violent_patient_v1.glb")
	if not patient_scene:
		push_error("VIOLENT_PATIENT missing model")
		quit(1)
		return
	var model := patient_scene.instantiate()
	root.add_child(model)
	await process_frame
	var skeleton: Skeleton3D
	var animation_player: AnimationPlayer
	var meshes := 0
	for node in _all_nodes(model):
		if node is Skeleton3D:
			skeleton = node
		elif node is AnimationPlayer:
			animation_player = node
		elif node is MeshInstance3D:
			meshes += 1
	if not skeleton or skeleton.get_bone_count() < 18:
		failures.append("skeleton")
	if not animation_player or animation_player.get_animation_list().is_empty():
		failures.append("animation")
	else:
		var has_locomotion_cycle := false
		for animation_name in animation_player.get_animation_list():
			var lower_name := String(animation_name).to_lower()
			if "run" in lower_name or "walk" in lower_name:
				has_locomotion_cycle = true
				break
		if not has_locomotion_cycle:
			failures.append("locomotion_cycle_name")
	# The downloaded CC0 patient is one optimized skinned mesh, unlike the old
	# procedural model which was assembled from 24+ separate primitives.
	if meshes < 1:
		failures.append("meshes")
	var bone_count := skeleton.get_bone_count() if skeleton else 0
	var animation_count := animation_player.get_animation_list().size() if animation_player else 0
	root.remove_child(model)
	model.free()

	var main_scene: PackedScene = load("res://scenes/hospital/main.tscn")
	var game := main_scene.instantiate()
	root.add_child(game)
	await process_frame
	await process_frame
	var manager := game.get_node("AnomalyManager")
	var care := game.get_node("CareManager")
	var hospital := game.get_node("HospitalModel")
	var player := game.get_node("Player")
	var state := game.get_node("HospitalState")
	if not manager.activate("violent_patient"):
		failures.append("activation")
	await process_frame
	var actor := game.get_node("HospitalModel/violent_patient")
	if not actor or not actor.is_in_group("violent_patients"):
		failures.append("actor")
	else:
		if not actor.target_prop:
			failures.append("destruction_target")
		actor.call("_break_prop")
		if not state.get_flag("violent_patient_loose", false):
			failures.append("property_damage")
		if actor.attack_damage > 16:
			failures.append("attack_too_strong_%d" % actor.attack_damage)
		actor.global_position = player.global_position + Vector3(0.5, 0.0, 0.0)
		for _hit in 3:
			actor.attack_cooldown = 0.0
			actor.call("_process_hunt")
		if player.dead or player.health < 50:
			failures.append("patient_damage_balance_%d" % player.health)
		var hud := game.get_node("HUD")
		# Damage hints now queue behind the encounter's introduction. Verify
		# that the hint was issued rather than requiring it to overwrite it.
		var restraint_hint_found := false
		for message in hud.get_message_history():
			if "ВЯЗКИ" in String(message.text):
				restraint_hint_found = true
		if not restraint_hint_found:
			failures.append("restraint_attack_hint_missing")
		var restraints := hospital.find_child("interaction_patient_restraints", true, false) as Node3D
		if not restraints:
			failures.append("restraints_missing")
		else:
			care.interact_object("patient_restraints", restraints)
			await process_frame
			if not care.has_patient_restraints or not player.held_item_copy:
				failures.append("restraints_pickup")
			actor.interact(player)
			await process_frame
			if not actor.restrained or not state.get_flag("violent_patient_restrained", false):
				failures.append("restraint_action")
			if care.has_patient_restraints or player.held_item_copy:
				failures.append("restraints_inventory_clear")
			if not restraints.visible:
				failures.append("restraints_not_restored_after_use")

	print(
		"VIOLENT_PATIENT bones=", bone_count,
		" animations=", animation_count,
		" meshes=", meshes,
		" restrained=", state.get_flag("violent_patient_restrained", false),
		" failures=", failures.size()
	)
	if not failures.is_empty():
		print("VIOLENT_FAILURES ", failures)
	quit(0 if failures.is_empty() else 1)

func _all_nodes(node: Node) -> Array[Node]:
	var result: Array[Node] = [node]
	for child in node.get_children():
		result.append_array(_all_nodes(child))
	return result
