extends SceneTree

const ProgressGuard := preload("res://scripts/tests/progress_guard.gd")
var failures: Array[String] = []

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	ProgressGuard.snapshot()
	var game = load("res://scenes/hospital/main.tscn").instantiate()
	root.add_child(game)
	while not game.prepared:
		await process_frame
	var sdk = game.get_node("YandexSDK")
	var cloud := {"night_1": {"ending": "dawn", "recorded_at": 100}}
	var merged: Dictionary = sdk._merge_results_by_night({}, cloud, 200, 100)
	check(merged.has("night_1"), "cloud_only_result_lost")
	merged = sdk._merge_results_by_night({"night_1": {"ending": "lost_mind", "recorded_at": 300}}, cloud, 300, 100)
	check(merged.night_1.ending == "lost_mind", "newer_local_result_overwritten")
	merged = sdk._merge_results_by_night({"night_1": {"ending": "lost_mind", "recorded_at": 50}}, cloud, 300, 100)
	check(merged.night_1.ending == "dawn", "newer_cloud_result_ignored")
	var state = game.get_node("HospitalState")
	var care = game.get_node("CareManager")
	var player = game.get_node("Player")
	var hospital = game.get_node("HospitalModel")
	var hud = game.get_node("HUD")
	var mobile = get_first_node_in_group("mobile_controls")
	var levels = get_first_node_in_group("level_manager")
	var clock = game.get_node("TimeManager")
	LevelManager.selected_index = 0
	state.reset_shift()
	care.start_shift()
	care.accept_phone_assignment("medication")
	care.accept_phone_assignment("vitals")
	var source = hospital.find_child("interaction_med_aminazine", true, false)
	care.interact_object("med_aminazine", source)
	await process_frame
	check(is_instance_valid(player.held_item_copy), "pickup_model_missing")
	hud.start_panel.hide()
	hud.mobile_interface = true
	mobile.set_mobile_enabled_for_test(true)
	mobile.assignment_button.pressed.emit()
	await process_frame
	check(care.active_assignment == "vitals", "touch_did_not_change_assignment")
	check(care.carried_item.is_empty() and source.visible, "touch_did_not_return_supply")
	check(not is_instance_valid(player.held_item_copy), "stale_held_model_after_cycle")
	care.stage = "return"
	mobile._refresh_visibility()
	check(mobile.assignment_button.disabled, "linen_return_can_be_skipped")
	var journal = get_first_node_in_group("documents")
	# Exercise the live-clock handoff branch for every night, including the
	# real journal and fire-exit interactions. No direct headless dawn shortcut.
	for index in LevelManager.level_count():
		LevelManager.selected_index = index
		state.reset_shift()
		levels.reset()
		clock.running = true
		levels.progression_started = true
		for task in state.tasks:
			state.tasks[task] = true
		levels._try_finish_shift()
		check(bool(state.get_flag("handoff_ready", false)), "night_%d_handoff_not_ready" % index)
		check(not bool(state.get_flag("ending_requested", false)), "night_%d_ended_without_handoff" % index)
		care.interact_object("fire_exit_seal", null)
		check(not bool(state.get_flag("ending_requested", false)), "fire_exit_still_finishes_shift")
		journal.interact(player)
		check(bool(state.get_flag("ending_requested", false)), "night_%d_journal_did_not_finish" % index)
		check(sdk.progress.last_ending == "dawn", "night_%d_wrong_ending" % index)
	clock.running = false
	print("AUDIT_FIXES nights=11 failures=", failures.size(), " ", failures)
	game.queue_free()
	await process_frame
	ProgressGuard.restore()
	quit(0 if failures.is_empty() else 1)

func check(condition: bool, label: String) -> void:
	if not condition:
		failures.append(label)
