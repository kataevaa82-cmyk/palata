extends SceneTree

const ProgressGuard := preload("res://scripts/tests/progress_guard.gd")

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	ProgressGuard.snapshot()
	var failures: Array[String] = []
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var scene := packed.instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame

	var main := scene
	var hud := scene.get_node("HUD")
	var director := scene.get_node("GameDirector")
	var time_manager := scene.get_node("TimeManager")
	var event_manager := scene.get_node("EventManager")
	var state := scene.get_node("HospitalState")
	var player := scene.get_node("Player")

	if not main.prepared:
		failures.append("hospital_not_prepared")
	if not hud.loading_complete:
		failures.append("menu_not_ready")
	if OS.is_debug_build():
		var level_select := hud.get_node("StartPanel/LevelSelect") as OptionButton
		if not level_select or level_select.item_count != LevelManager.level_count():
			failures.append("debug_level_count")
		elif range(level_select.item_count).any(func(index): return level_select.is_item_disabled(index)):
			failures.append("debug_level_locked")

	hud._start_pressed()
	# Starting a night now hops through the between-levels interstitial when the
	# player has finished a shift before, so the shift begins on the ad's
	# callback rather than inside the button press.
	for _frame in 3:
		await process_frame
	if not director.started or not time_manager.running or not event_manager.running:
		failures.append("shift_did_not_start")
	if not player.can_move:
		failures.append("player_still_frozen")
	var yaw_before: float = player.rotation.y
	var pitch_before: float = player.head.rotation.x
	player.apply_look_delta(Vector2(120.0, -60.0))
	if is_equal_approx(player.rotation.y, yaw_before) or is_equal_approx(player.head.rotation.x, pitch_before):
		failures.append("camera_look_failed")

	# The normal orderly now reacts to checking the journal; moving the clock on
	# its own must not dispatch story events.
	for _i in 35:
		time_manager.advance_minute(1)
	await process_frame
	if scene.get_node("HospitalModel").get_node_or_null("normal_orderly"):
		failures.append("orderly_fired_from_clock")
	var journal := get_first_node_in_group("documents")
	if journal:
		journal.interact(player)
	await process_frame
	if not scene.get_node("HospitalModel").get_node_or_null("normal_orderly"):
		failures.append("orderly_journal_trigger_missing")

	var phone: Node = root.get_tree().get_first_node_in_group("hospital_phone")
	if not phone:
		failures.append("phone_missing")
	else:
		phone.start_call("operator_count")
		phone.answer_count(7)
		if not state.observations.any(func(item): return item.get("kind", "") == "correct_patient_count"):
			failures.append("phone_answer_failed")

	var endings: Array[String] = []
	state.ending_requested.connect(func(id):
		endings.append(id)
	)
	time_manager.hour = 5
	time_manager.minute = 59
	time_manager.advance_minute(1)
	if not "unfinished_shift" in endings:
		failures.append("unfinished_shift_ending_missing")

	ProgressGuard.restore()
	print("SMOKE_GAME failures=", failures.size())
	if not failures.is_empty():
		print("SMOKE_FAILURES ", failures)
		quit(1)
	else:
		quit(0)
