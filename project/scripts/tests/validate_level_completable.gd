extends SceneTree

const ProgressGuard := preload("res://scripts/tests/progress_guard.gd")

# validate_levels.gd proves the night's data is consistent and
# validate_level_run.gd proves its beats fire. Neither proves a night can
# actually be *finished*: nothing in the suite ever completes a task, so
# "проходимость" was never tested. This does.
#
# For every night it plays the shift through the real runtime APIs - answers the
# phone the beats ring, collects the prescribed item, treats the named patient,
# uses the level props - then asserts main.gd's 06:00 gate hands out "dawn"
# rather than "unfinished_shift".
#
# Two deliberate cheats, both orthogonal to completability: the player is frozen
# and topped back up to full health/sanity every minute (a hostile spawn must
# not turn a task test into a survival test), and the clock is driven by hand so
# a 6-hour night takes a few hundred frames.

var game: Node
var care: Node
var state: Node
var levels: Node
var director: Node
var time_manager: Node
var hospital: Node
var player: Node
var phone: Node
var level: Dictionary
var endings: Array[String] = []
var notes: Array[String] = []
var leaked: Array[String] = []
var hud: Node
var wanted_locale := "ru"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	ProgressGuard.snapshot()
	# Optional locale argument (`-- en`). Under a non-Russian locale the run
	# doubles as the localisation sweep: it drives every message path of every
	# night, so any string that was never wrapped in tr() shows up as Cyrillic
	# in a HUD label and fails here instead of in front of a player.
	var user_args := OS.get_cmdline_user_args()
	if user_args.size() > 0:
		TranslationServer.set_locale(String(user_args[0]))
	# Remembered here: by the time a night starts, yandex_sdk has already
	# applied the saved locale over this one, so reading it back later would
	# just return "ru" and the sweep would silently test nothing.
	wanted_locale = TranslationServer.get_locale().left(2)
	var checking_translation := not TranslationServer.get_locale().begins_with("ru")
	var failures: Array[String] = []
	var report: Array[String] = []
	for index in LevelManager.level_count():
		var result: Dictionary = await _play_night(index)
		var tag := "n%d" % (index + 1)
		report.append("  %s %-14s tasks=%d/%d required=%d ending=%s" % [
			tag, String(result.id), int(result.done), int(result.total),
			int(result.required), String(result.ending)])
		if String(result.ending) != "dawn":
			failures.append("%s_ending_%s (%d/%d done, needs %d)" % [
				tag, String(result.ending), int(result.done), int(result.total), int(result.required)])
		if not result.missed.is_empty():
			report.append("      %s missed=%s" % [tag, ", ".join(result.missed)])
		if checking_translation:
			for text in result.cyrillic:
				failures.append("%s_untranslated: %s" % [tag, text.replace("\n", " / ")])
		for note in result.notes:
			report.append("      %s %s" % [tag, note])

	LevelManager.selected_index = 0
	for line in report:
		print(line)
	print("VALIDATE_LEVEL_COMPLETABLE nights=%d failures=%d" % [LevelManager.level_count(), failures.size()])
	if failures.is_empty():
		print("VALIDATE_LEVEL_COMPLETABLE OK")
	else:
		for failure in failures:
			print("  FAIL ", failure)
	ProgressGuard.restore()
	quit(0 if failures.is_empty() else 1)

func _play_night(index: int) -> Dictionary:
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	game = packed.instantiate()
	root.add_child(game)
	for _frame in 4:
		await process_frame

	# hud.gd's _ready() overwrites LevelManager.selected_index with the saved
	# progress night, so the choice only sticks if it is made after the scene is
	# in the tree - the same order the level dropdown produces.
	LevelManager.selected_index = index
	hospital = game.get_node("HospitalModel")
	levels = game.get_node("LevelManager")
	care = game.get_node("CareManager")
	state = game.get_node("HospitalState")
	director = game.get_node("GameDirector")
	time_manager = game.get_node("TimeManager")
	player = game.get_node("Player")
	hud = game.get_node("HUD")
	# yandex_sdk applies the saved/platform locale while the scene is coming up,
	# so a locale set before instantiation is overwritten. Go through the same
	# API the menu button uses instead - that also exercises persistence, which
	# ProgressGuard rolls back afterwards.
	var platform := get_first_node_in_group("yandex_sdk")
	if platform and platform.has_method("set_language"):
		platform.set_language(wanted_locale)
	level = LevelManager.level()
	levels.apply_prop_visibility(hospital)
	endings = []
	notes = []
	leaked = []
	state.ending_requested.connect(func(id: String) -> void: endings.append(id))

	director.start_shift()
	player.set_frozen(true)
	time_manager.pause_clock(true)
	phone = get_first_node_in_group("hospital_phone")
	# The duty board, rather than the optional narrative phone calls, is the
	# authoritative source of every night's care assignments. Read it on every
	# night even when assignment_board_read is not itself a scored task.
	var assignment_board := _interactable("assignment_board")
	if assignment_board:
		assignment_board.interact(player)
	else:
		_note("no_assignment_board")

	for _minute in 360:
		time_manager.advance_minute(1)
		player.health = 100
		player.sanity = 100
		player.dead = false
		_answer_phone()
		_step_assignment()
		_do_pending_task()
		await process_frame
		_sample_hud_text()

	var result := {
		"id": String(level.get("id", "?")),
		"done": state.task_count(),
		"total": state.task_total(),
		"required": int(level.get("required", 9)),
		"ending": endings[0] if not endings.is_empty() else "<none>",
		"missed": _missed_tasks(),
		"notes": notes.duplicate(),
		"cyrillic": leaked.duplicate(),
	}
	game.free()
	await process_frame
	return result

# --- phone -------------------------------------------------------------------

func _answer_phone() -> void:
	if not phone or not phone.ringing:
		return
	match phone.call_type:
		"operator_count":
			phone.interact(player)
			phone.answer_count(state.patient_count)
		"room4":
			# The task only ticks from the third ring; the ring timer is real
			# seconds, so ring it by hand instead of stalling the test 7 s.
			while phone.ring_count < 3:
				phone._on_ring()
			phone.interact(player)
		_:
			if phone.call_type.begins_with("care_") and not care.active_assignment.is_empty():
				return  # let the running assignment finish before queueing more
			phone.interact(player)

# --- care assignments --------------------------------------------------------

func _step_assignment() -> void:
	if care.active_assignment.is_empty():
		return
	var mission: Dictionary = care.ASSIGNMENTS[care.active_assignment]
	match String(care.stage):
		"collect":
			var source := _supply_source(String(mission.item))
			if not source:
				_note("no_source_for_item_%s (%s)" % [mission.item, care.active_assignment])
				care.stage = "treat"  # keep going so the rest of the night is still graded
				return
			source.interact(player)
		"treat":
			if String(mission.action) == "return_patient":
				var escaped := _interactable("escaped_patient")
				if escaped and escaped.visible:
					escaped.interact(player)
				elif not escaped:
					_note("no_escaped_patient_node")
				return
			var patient := _patient(String(mission.patient))
			if not patient:
				_note("no_patient_node_%s (%s)" % [mission.patient, care.active_assignment])
				return
			patient.interact(player)
		"return":
			var basket := _interactable("laundry_basket")
			if basket:
				basket.interact(player)
			else:
				_note("no_laundry_basket")

# --- everything that is not a phoned-in assignment ---------------------------

func _do_pending_task() -> void:
	# Reading the board can queue the whole care round before its phone beats.
	# Do not replace a prescribed item with a free object-task tool between the
	# collect and treat steps; finish the active care assignment first.
	if not care.active_assignment.is_empty() and care.active_assignment != "return_patient":
		return
	for task_id in level.get("tasks", []):
		var id := String(task_id)
		if state.tasks.get(id, false) or id.begins_with("care_"):
			continue
		match id:
			"journal_checked":
				var journal := get_first_node_in_group("documents")
				if journal:
					journal.interact(player)
					return
			"assignment_board_read":
				if _use("assignment_board"):
					return
			"exit_check":
				if _use("fire_exit_seal"):
					return
			"elevator_check":
				if _use("elevator_inspection"):
					return
			"spill_cleanup":
				# The flood is not scheduled: it only happens when the violent
				# patient actually reaches the player and tips a prop, which a
				# frozen test player never provokes. Force it late in the night
				# so the mop-and-clean path is still proven to complete.
				if not care.spill_active and int(time_manager.hour) >= 5:
					_note("spill forced (violent patient never reached the player)")
					care.trigger_water_spill()
				if care.spill_active:
					if not care.has_mop:
						if _use("mop_bucket"):
							return
					elif _use("water_spill"):
						return
			"room4_call", "patient_count", "final_call":
				continue  # driven by _answer_phone when the beat rings
			_:
				if id.begins_with("obj_") and _do_object_task(id):
					return

func _do_object_task(task_id: String) -> bool:
	for care_id in care.LEVEL_OBJECT_TASKS:
		var spec: Dictionary = care.LEVEL_OBJECT_TASKS[care_id]
		if String(spec.task) != task_id:
			continue
		var node := _interactable(String(care_id))
		if not node:
			_note("no_prop_for_%s" % task_id)
			return false
		if bool(spec.get("mop", false)) and not care.has_mop:
			return _use("mop_bucket")
		var item := String(spec.get("item", ""))
		if not item.is_empty() and care.carried_item != item:
			var source := _supply_source(item)
			if not source:
				_note("no_source_for_%s (%s)" % [item, task_id])
				return false
			source.interact(player)
			return true
		node.interact(player)
		return true
	return false

# --- lookups -----------------------------------------------------------------

func _use(care_id: String) -> bool:
	var node := _interactable(care_id)
	if not node:
		return false
	node.interact(player)
	return true

func _interactable(care_id: String) -> Node:
	for node in get_nodes_in_group("care_interactables"):
		if String(node.care_id) == care_id:
			return node
	return null

func _patient(patient_id: String) -> Node:
	for node in get_nodes_in_group("care_patients"):
		if String(node.patient_id) == patient_id:
			return node
	return null

func _supply_source(item: String) -> Node:
	if item.is_empty():
		return null
	for care_id in care.SUPPLY_ITEMS:
		if String(care.SUPPLY_ITEMS[care_id]) == item:
			var node := _interactable(String(care_id))
			if node:
				return node
	for care_id in care.LEVEL_SUPPLY_ITEMS:
		if String(care.LEVEL_SUPPLY_ITEMS[care_id]) == item:
			var node := _interactable(String(care_id))
			if node:
				return node
	return null

func _sample_hud_text() -> void:
	# Everything the player reads goes through one of these labels, so polling
	# them once per simulated minute catches any message, prompt, objective or
	# document that was never wrapped in tr().
	if not hud:
		return
	for path in ["MessageLabel", "ObjectiveLabel", "Prompt", "DocumentPanel/DocumentText",
			"MissionPanel/MissionTitle", "MissionPanel/MissionText", "MissionPanel/InventoryText",
			"EndingPanel/EndingTitle", "EndingPanel/EndingText"]:
		var label := hud.get_node_or_null(path) as Label
		if not label:
			continue
		# atr(), not .text: a Label authored in the scene keeps its Russian
		# source in `text` and translates on the way to the screen, so reading
		# the property would report every scene label as a leak.
		var shown := label.atr(label.text)
		if _has_cyrillic(shown) and not shown in leaked:
			leaked.append(shown)

func _has_cyrillic(text: String) -> bool:
	for index in text.length():
		var code := text.unicode_at(index)
		if code >= 0x0400 and code <= 0x04FF:
			return true
	return false

func _missed_tasks() -> PackedStringArray:
	var out := PackedStringArray()
	for id in state.tasks:
		if not state.tasks[id]:
			out.append(String(id))
	return out

func _note(text: String) -> void:
	if not text in notes:
		notes.append(text)
