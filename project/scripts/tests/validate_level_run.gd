extends SceneTree

const ProgressGuard := preload("res://scripts/tests/progress_guard.gd")

# Data consistency (validate_levels.gd) does not prove a night actually runs.
# This advances the clock without progress (which must fire nothing), then
# completes every task quickly and asserts all semantic story triggers fire and
# the successful ending arrives without waiting for 06:00.

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	ProgressGuard.snapshot()
	var failures: Array[String] = []
	var totals: Array[String] = []

	for index in LevelManager.level_count():
		var packed: PackedScene = load("res://scenes/hospital/main.tscn")
		var game: Node = packed.instantiate()
		root.add_child(game)
		for _frame in 4:
			await process_frame
		# Must come after the scene is in the tree: hud.gd's _ready() restores
		# the night from saved progress, so a choice made before add_child() is
		# overwritten and every night silently ran as night 1.
		LevelManager.selected_index = index
		game.get_node("LevelManager").apply_prop_visibility(game.get_node("HospitalModel"))

		var director := game.get_node("GameDirector")
		var levels := game.get_node("LevelManager")
		var time_manager := game.get_node("TimeManager")
		var state := game.get_node("HospitalState")
		var level: Dictionary = LevelManager.level()
		var tag := "n%d" % (index + 1)

		var endings: Array[String] = []
		state.ending_requested.connect(func(id: String) -> void: endings.append(id))
		director.start_shift()
		time_manager.pause_clock(true)
		var opening_fired: int = levels.fired.size()
		for _minute in 120:
			time_manager.advance_minute(1)
		await process_frame

		if time_manager.formatted_time() != "02:00":
			failures.append("%s_clock_%s" % [tag, time_manager.formatted_time()])
		if levels.fired.size() != opening_fired:
			failures.append("%s_clock_fired_story_%d_to_%d" % [tag, opening_fired, levels.fired.size()])

		# Keep the story's mandatory ending requirements until last. The pass
		# mark deliberately permits optional tasks, so completing a mandatory
		# requirement too early can legitimately end the shift before a later
		# optional task gets a chance to fire its own semantic beat.
		var ordered_tasks: Array = level.get("tasks", []).duplicate()
		var ending_tasks: Array = LevelManager.ENDING_REQUIREMENTS.get(String(level.id), [])
		for task_id in ending_tasks:
			ordered_tasks.erase(task_id)
			ordered_tasks.append(task_id)
		for task_id in ordered_tasks:
			state.complete_task(String(task_id))
			await process_frame

		var expected: int = LevelManager.STORY_TRIGGERS.get(String(level.id), []).size()
		var fired: int = levels.fired.size()
		if fired != expected:
			failures.append("%s_fired_%d_of_%d" % [tag, fired, expected])
		if endings.is_empty() or endings[0] != "dawn":
			failures.append("%s_fast_ending_%s" % [tag, endings[0] if not endings.is_empty() else "none"])
		if state.task_total() == 0:
			failures.append("%s_no_tasks" % tag)
		totals.append("%s triggers=%d/%d tasks=%s ending=%s" % [tag, fired, expected,
			state.task_summary(), endings[0] if not endings.is_empty() else "none"])

		game.free()
		await process_frame

	LevelManager.selected_index = 0
	for line in totals:
		print("  ", line)
	print("VALIDATE_LEVEL_RUN nights=%d failures=%d" % [LevelManager.level_count(), failures.size()])
	if failures.is_empty():
		print("VALIDATE_LEVEL_RUN OK")
	else:
		for failure in failures:
			print("  FAIL ", failure)
	ProgressGuard.restore()
	quit(0 if failures.is_empty() else 1)
