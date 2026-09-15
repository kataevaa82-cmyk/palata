extends SceneTree

const ProgressGuard := preload("res://scripts/tests/progress_guard.gd")

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	ProgressGuard.snapshot()
	var failures: Array[String] = []
	LevelManager.selected_index = 4
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game := packed.instantiate()
	root.add_child(game)
	for _frame in 3:
		await process_frame
	var state := game.get_node("HospitalState")
	var care := game.get_node("CareManager")
	var hospital := game.get_node("HospitalModel")

	# A swapped label cannot be bypassed by picking a bag before inspecting the
	# independent chart; the correct bag also leaves an explicit confirmation.
	state.reset_shift()
	care.start_shift()
	care.active_assignment = "transfusion"
	care.stage = "collect"
	state.set_flag("blood_labels_unreliable", true)
	var bag := hospital.find_child("interaction_blood_bag_second", true, false) as Node3D
	var chart := hospital.find_child("interaction_blood_chart", true, false) as Node3D
	if not bag or not chart:
		failures.append("blood_props_missing")
	else:
		care.interact_object("blood_bag_second", bag)
		if not care.carried_item.is_empty():
			failures.append("blood_taken_without_chart")
		care.interact_object("blood_chart", chart)
		care.interact_object("blood_bag_second", bag)
		if care.carried_item != "blood_second" or not bool(state.get_flag("blood_batch_confirmed", false)):
			failures.append("blood_batch_not_confirmed")

	# In a live shift an already-open bix needs a recovery action, then a second
	# interaction with the replacement kit. It must not complete in one click.
	LevelManager.selected_index = 9
	state.reset_shift()
	care.start_shift()
	var clock := game.get_node("TimeManager")
	clock.running = true
	state.set_flag("bix_used", true)
	var bix := hospital.find_child("interaction_sterile_bix", true, false) as Node3D
	if not bix:
		failures.append("bix_prop_missing")
	else:
		care.interact_object("sterile_bix", bix)
		if not bool(state.get_flag("bix_replaced", false)) or bool(state.tasks.get("obj_sterile_bix", false)):
			failures.append("bix_recovery_step")
		care.interact_object("sterile_bix", bix)
		if not bool(state.tasks.get("obj_sterile_bix", false)):
			failures.append("bix_replacement_not_usable")
	clock.running = false

	print("SAFETY_GATES failures=", failures.size())
	if not failures.is_empty():
		print("SAFETY_GATE_FAILURES ", failures)
	ProgressGuard.restore()
	quit(0 if failures.is_empty() else 1)
