extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var failures: Array[String] = []
	LevelManager.selected_index = 0
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game := packed.instantiate()
	root.add_child(game)
	for _frame in 3:
		await process_frame
	game.get_node("HUD")._start_pressed()
	for _frame in 3:
		await process_frame

	var manager := game.get_node("CareManager")
	var state := game.get_node("HospitalState")
	var player := game.get_node("Player")
	var hospital := game.get_node("HospitalModel")
	var phone := get_first_node_in_group("hospital_phone")
	if not phone:
		failures.append("missing_phone")
	elif phone.ringing or phone.ring_count != 0:
		failures.append("phone_rang_before_board")

	var board := hospital.find_child("interaction_assignment_board", true, false) as Node3D
	manager.interact_object("assignment_board", board)
	if manager.active_assignment != "medication":
		failures.append("board_did_not_start_assignment")
	if not "vitals" in manager.assignment_queue:
		failures.append("board_did_not_queue_assignments")

	var aminazine := hospital.find_child("interaction_med_aminazine", true, false) as Node3D
	manager.interact_object("med_aminazine", aminazine)
	var patient: Node3D
	for candidate in get_nodes_in_group("care_patients"):
		if candidate.get("patient_id") == "saveliev":
			patient = candidate as Node3D
			break
	if not patient:
		failures.append("missing_saveliev")
	else:
		manager.interact_patient("saveliev", "Saveliev", 4, 1, patient)
	if not state.tasks.get("care_medication", false):
		failures.append("task_not_completed_without_phone")
	# Story calls (night 1's room-4 call, for example) may ring while the board
	# assignment is underway. Only a care_* call here would mean the board path
	# still depends on answering the phone.
	if phone and phone.ringing and String(phone.call_type).begins_with("care_"):
		failures.append("care_phone_used_during_task_%s" % phone.call_type)

	print("PHONE_OPTIONAL completed=", state.tasks.get("care_medication", false),
		" rings=", phone.ring_count if phone else -1, " failures=", failures.size())
	if not failures.is_empty():
		print("PHONE_OPTIONAL_FAILURES ", failures)
	quit(0 if failures.is_empty() else 1)
