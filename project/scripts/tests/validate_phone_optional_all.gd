extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var failures: Array[String] = []
	for level_index in LevelManager.level_count():
		var packed: PackedScene = load("res://scenes/hospital/main.tscn")
		var game := packed.instantiate()
		root.add_child(game)
		for _frame in 4:
			await process_frame

		LevelManager.selected_index = level_index
		var level: Dictionary = LevelManager.level()
		var manager := game.get_node("CareManager")
		var state := game.get_node("HospitalState")
		var player := game.get_node("Player")
		var hospital := game.get_node("HospitalModel")
		game.get_node("LevelManager").apply_prop_visibility(hospital)
		game.get_node("GameDirector").start_shift()
		var phone := get_first_node_in_group("hospital_phone")
		var tag := "night_%d" % (level_index + 1)
		if not phone:
			failures.append(tag + "_missing_phone")
		elif phone.ringing or phone.ring_count != 0:
			failures.append(tag + "_phone_rang_before_board")

		var board := hospital.find_child("interaction_assignment_board", true, false) as Node3D
		manager.interact_object("assignment_board", board)
		var scheduled: Array = level.get("assignments", [])
		var expected := String(scheduled[0]) if not scheduled.is_empty() else ""
		if manager.active_assignment != expected:
			failures.append(tag + "_board_did_not_start_" + expected)
		if manager.assignment_queue.size() != maxi(0, scheduled.size() - 1):
			failures.append(tag + "_board_queue_size_%d" % manager.assignment_queue.size())

		if not expected.is_empty():
			_finish_active_assignment(manager, player)
			var task_id := String(manager.ASSIGNMENTS[expected].task)
			if not state.tasks.get(task_id, false):
				failures.append(tag + "_task_not_completed_without_phone")
		# Narrative calls are allowed; the regression being guarded is a care
		# assignment that cannot be completed unless its care_* call is answered.
		if phone and phone.ringing and String(phone.call_type).begins_with("care_"):
			failures.append(tag + "_care_phone_used_during_task_" + String(phone.call_type))

		game.free()
		await process_frame

	LevelManager.selected_index = 0
	print("PHONE_OPTIONAL nights=", LevelManager.level_count(), " failures=", failures.size())
	if not failures.is_empty():
		print("PHONE_OPTIONAL_FAILURES ", failures)
	quit(0 if failures.is_empty() else 1)

func _finish_active_assignment(manager: Node, player: Node) -> void:
	if manager.active_assignment.is_empty():
		return
	var mission: Dictionary = manager.ASSIGNMENTS[manager.active_assignment]
	var item := String(mission.item)
	if not item.is_empty():
		for node in get_nodes_in_group("care_interactables"):
			var care_id := String(node.get("care_id"))
			if String(manager.SUPPLY_ITEMS.get(care_id, "")) == item \
			or String(manager.LEVEL_SUPPLY_ITEMS.get(care_id, "")) == item:
				node.interact(player)
				break
	if String(mission.action) == "return_patient":
		for node in get_nodes_in_group("care_interactables"):
			if String(node.get("care_id")) == "escaped_patient":
				node.interact(player)
				return
	for patient in get_nodes_in_group("care_patients"):
		if String(patient.get("patient_id")) == String(mission.patient):
			patient.interact(player)
			break
	if manager.stage == "return":
		for node in get_nodes_in_group("care_interactables"):
			if String(node.get("care_id")) == "laundry_basket":
				node.interact(player)
				break
