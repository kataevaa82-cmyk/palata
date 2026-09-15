extends SceneTree

# Regression checks for the 2026-09-14 game-logic audit (AUDIT_2026-09-14.md).
# Every scenario drives the real runtime API in the order a player could choose,
# which is exactly what validate_level_completable.gd does not do: it always
# finishes prescriptions before object tasks and forces the flood.

const ProgressGuard := preload("res://scripts/tests/progress_guard.gd")

var failures: Array[String] = []
var game: Node
var hospital: Node3D
var levels: Node
var care: Node
var state: Node
var director: Node
var clock: Node
var player: Node
var hud: Node
var anomalies: Node
var endings: Array[String] = []
var scenario_finished := false

func _initialize() -> void:
	call_deferred("_run")

const SCENARIOS := ["night5_chart_first", "night5_bag_before_chart", "night11_operator_retry",
	"linen_second_press", "free_tool_during_assignment", "night4_order_and_inspection_text",
	"empty_bed", "long_corridor_keeps_geometry", "room_zero_door", "extra_patient_in_ward6",
	"status_lines_do_not_queue", "flood_blocks_then_releases_handoff", "exit_door_after_work",
	"night8_chair_returns", "hostile_beat_waits_for_danger", "objective_hint_night4", "objective_hint_night5",
	"night9_alarm_order"]

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.is_empty():
		_run_all_in_child_processes()
		return
	# One scenario per process. Headless Godot 4.7.1 segfaults intermittently when
	# main.tscn is instantiated and freed several times in one process (seen with
	# the pre-fix scripts too), so a single-process run of all scenarios is not a
	# reliable signal. The result line is printed before quitting, so a crash on
	# exit does not lose it.
	var scenario := String(args[0])
	ProgressGuard.snapshot()
	await _run_scenario(scenario)
	# A runtime script error aborts a scenario coroutine without failing it; this
	# flag is only set by the scenario's final teardown.
	if not scenario_finished:
		failures.append("scenario_aborted_before_teardown")
	LevelManager.selected_index = 0
	print("AUDIT_SCENARIO ", scenario, " failures=", failures.size(), " ", failures)
	ProgressGuard.restore()
	quit(0 if failures.is_empty() else 1)

func _run_all_in_child_processes() -> void:
	var all_failures: Array[String] = []
	for scenario in SCENARIOS:
		var output: Array = []
		var code := OS.execute(OS.get_executable_path(), ["--headless", "--path",
			ProjectSettings.globalize_path("res://"), "--script", get_script().resource_path,
			"--", scenario], output, true)
		var text := "\n".join(output)
		var result_line := ""
		for line in text.split("\n"):
			if line.begins_with("AUDIT_SCENARIO "):
				result_line = line.strip_edges()
		if result_line.is_empty():
			all_failures.append("%s_no_result_exit_%d" % [scenario, code])
		elif not " failures=0 " in result_line:
			all_failures.append(result_line.trim_prefix("AUDIT_SCENARIO "))
		print("  ", result_line if not result_line.is_empty() else "%s: no result (exit %d)" % [scenario, code])
	print("AUDIT_2026_09_14 scenarios=", SCENARIOS.size(), " failures=", all_failures.size(), " ", all_failures)
	quit(0 if all_failures.is_empty() else 1)

func _run_scenario(scenario: String) -> void:
	match scenario:
		"night5_chart_first": await _night5_chart_first()
		"night5_bag_before_chart": await _night5_bag_before_chart()
		"night11_operator_retry": await _night11_operator_retry()
		"linen_second_press": await _linen_second_press()
		"free_tool_during_assignment": await _free_tool_during_assignment()
		"night4_order_and_inspection_text": await _night4_order_and_inspection_text()
		"empty_bed": await _empty_bed()
		"long_corridor_keeps_geometry": await _long_corridor_keeps_geometry()
		"room_zero_door": await _room_zero_door()
		"extra_patient_in_ward6": await _extra_patient_in_ward6()
		"status_lines_do_not_queue": await _status_lines_do_not_queue()
		"flood_blocks_then_releases_handoff": await _flood_blocks_then_releases_handoff()
		"exit_door_after_work": await _exit_door_after_work()
		"night8_chair_returns": await _night8_chair_returns()
		"hostile_beat_waits_for_danger": await _hostile_beat_waits_for_danger()
		"objective_hint_night4": await _objective_hint_skips_final_call(3)
		"objective_hint_night5": await _objective_hint_skips_final_call(4)
		"night9_alarm_order": await _night9_alarm_order()
		_: failures.append("unknown_scenario_" + scenario)

func check(condition: bool, label: String) -> void:
	if not condition:
		failures.append(label)

# --- harness ------------------------------------------------------------------

func _setup(index: int, live_clock := true) -> void:
	game = load("res://scenes/hospital/main.tscn").instantiate()
	root.add_child(game)
	while not game.prepared:
		await process_frame
	LevelManager.selected_index = index
	hospital = game.get_node("HospitalModel")
	levels = game.get_node("LevelManager")
	care = game.get_node("CareManager")
	state = game.get_node("HospitalState")
	director = game.get_node("GameDirector")
	clock = game.get_node("TimeManager")
	player = game.get_node("Player")
	hud = game.get_node("HUD")
	anomalies = game.get_node("AnomalyManager")
	endings = []
	state.ending_requested.connect(func(id: String) -> void: endings.append(id))
	levels.apply_prop_visibility(hospital)
	director.start_shift()
	game.get_node("EventManager").stop_events()
	hud.start_panel.visible = false
	player.set_frozen(true)
	if not live_clock:
		clock.pause_clock(true)
	await process_frame

func _teardown() -> void:
	paused = false
	game.queue_free()
	for _i in 4:
		await process_frame
	scenario_finished = true

func _node(care_id: String) -> Node:
	for node in get_nodes_in_group("care_interactables"):
		if String(node.care_id) == care_id:
			return node
	return null

func _patient(patient_id: String) -> Node:
	for node in get_nodes_in_group("care_patients"):
		if String(node.patient_id) == patient_id:
			return node
	return null

func _use(care_id: String) -> void:
	_node(care_id).interact(player)
	if hud.document_panel.visible:
		hud.close_document()

func _focus(assignment_id: String) -> void:
	for _i in 10:
		if care.active_assignment == assignment_id:
			return
		care.cycle_assignment()

func _layer(node: Node) -> int:
	var area := node.get_node_or_null("CareInteractionArea") as Area3D
	return area.collision_layer if area else -1

func _history_has(fragment: String) -> bool:
	for entry in hud.get_message_history():
		if fragment in String(entry.text):
			return true
	return false

func _clear_danger() -> void:
	for group in ["hostile_orderlies", "violent_patients"]:
		for node in get_nodes_in_group(group):
			node.queue_free()
	await process_frame

# --- P1 -----------------------------------------------------------------------

func _night5_chart_first() -> void:
	await _setup(4)
	check(not state.tasks.has("spill_cleanup"), "n5_unreachable_spill_task_still_scored")
	_use("assignment_board")
	_use("blood_chart")
	var chart := _node("blood_chart")
	check(chart.visible and _layer(chart) == 1, "n5_chart_hidden_after_reading")
	_use("blood_bag_second")
	check(care.carried_item == "blood_second", "n5_bag_refused_after_chart")
	_patient("saveliev").interact(player)
	check(bool(state.tasks.care_transfusion), "n5_transfusion_blocked_after_chart")
	check(int(state.get_flag("medical_errors", 0)) == 0, "n5_chart_first_medical_error")
	_use("blood_chart")
	check(_history_has("B2-041"), "n5_chart_reread_has_no_batch_code")
	await _teardown()

func _night5_bag_before_chart() -> void:
	await _setup(4)
	_use("assignment_board")
	_use("blood_bag_second")
	_use("blood_chart")
	_patient("saveliev").interact(player)
	check(bool(state.tasks.care_transfusion), "n5_bag_before_chart_blocked")
	await _teardown()

func _night11_operator_retry() -> void:
	await _setup(10)
	_use("zero_card")
	var phone := get_first_node_in_group("hospital_phone")
	check(phone.ringing and phone.call_type == "operator_count", "n11_operator_call_missing")
	phone.interact(player)
	var wrong: int = 8 if int(state.patient_count) != 8 else 6
	hud.answer_patient_count(wrong)
	check(not bool(state.tasks.patient_count), "n11_wrong_answer_counted")
	# The retry is a play-time timer; fire its callback instead of waiting 45 s.
	# Checked explicitly: calling a missing method only aborts this coroutine.
	check(phone.has_method("_retry_operator_call"), "n11_no_operator_retry")
	if not phone.has_method("_retry_operator_call"):
		await _teardown()
		return
	phone._retry_operator_call()
	check(phone.ringing and phone.call_type == "operator_count", "n11_operator_does_not_call_back")
	phone.interact(player)
	hud.answer_patient_count(int(state.patient_count))
	check(bool(state.tasks.patient_count), "n11_retry_answer_not_counted")
	await _teardown()

# --- P2 -----------------------------------------------------------------------

func _linen_second_press() -> void:
	await _setup(0)
	_use("assignment_board")
	_focus("linen")
	_use("clean_linen")
	_patient("morozov").interact(player)
	var health: int = player.health
	_patient("morozov").interact(player)
	check(care.stage == "return" and care.carried_item == "dirty_linen", "linen_second_press_reset_%s" % care.stage)
	check(int(state.get_flag("medical_errors", 0)) == 0 and player.health == health, "linen_second_press_punished")
	_use("laundry_basket")
	check(bool(state.tasks.care_linen), "linen_not_completed_after_second_press")
	await _teardown()

func _free_tool_during_assignment() -> void:
	await _setup(1)
	_use("assignment_board")
	check(care.active_assignment == "oxygen", "n2_first_assignment_%s" % care.active_assignment)
	_use("spare_fuses")
	check(care.stage == "collect", "free_tool_moved_stage_to_%s" % care.stage)
	_use("fuse_box")
	check(bool(state.tasks.obj_fuse_box), "fuse_box_not_done")
	check(care.stage == "collect", "stage_after_tool_used_%s" % care.stage)
	check(_node("fuse_box").visible, "fuse_box_vanished")
	_patient("yudin").interact(player)
	check(int(state.get_flag("medical_errors", 0)) == 0, "free_tool_led_to_medical_error")
	_use("emergency_lamp")
	check(_node("emergency_lamp").get_node_or_null("PropLight") != null, "emergency_lamp_gives_no_light")
	await _teardown()

func _night4_order_and_inspection_text() -> void:
	await _setup(3)
	_use("assignment_board")
	_use("gurney")
	check(not bool(state.tasks.obj_gurney) and not levels.fired.has("body_returned"), "n4_gurney_before_shroud_accepted")
	_use("med_stethoscope")
	_patient("demina").interact(player)
	_use("body_bag")
	_patient("demina").interact(player)
	check(levels.fired.has("body_missing") and not _patient("demina").visible, "n4_body_missing_not_run")
	_use("gurney")
	var demina := _patient("demina") as Node3D
	check(levels.fired.has("body_returned") and demina.visible and _layer(demina) == 1, "n4_body_not_returned")
	check(int(state.patient_count) == 7, "n4_patient_count_%d" % state.patient_count)
	_use("med_saline")
	_patient("yudin").interact(player)
	await process_frame
	check(hospital.get_node_or_null("head_nurse_inspector") != null, "n4_story_nurse_missing")
	check(_history_has("начала обход"), "n4_story_nurse_has_no_round_text")
	check(not _history_has("Врачебная ошибка зарегистрирована"), "n4_story_nurse_claims_medical_error")
	await _teardown()

func _empty_bed() -> void:
	await _setup(0)
	anomalies.activate("empty_bed")
	var demina := _patient("demina") as Node3D
	check(not demina.visible and _layer(demina) == 0, "empty_bed_patient_still_interactive")
	check(int(state.patient_count) == 6, "empty_bed_count_%d" % state.patient_count)
	var journal := get_first_node_in_group("documents")
	journal.interact(player)
	check(not "Демина" in String(hud.document_text.text), "empty_bed_journal_lists_patient")
	hud.close_document()
	anomalies._restore_empty_bed()
	check(demina.visible and _layer(demina) == 1 and int(state.patient_count) == 7, "empty_bed_not_restored")
	check(not "empty_bed" in LevelManager.LEVELS[3].anomalies, "empty_bed_in_night4_pool")
	await _teardown()

func _long_corridor_keeps_geometry() -> void:
	await _setup(0)
	var before := _east_offsets()
	anomalies.activate("long_corridor")
	await physics_frame
	var after := _east_offsets()
	check(before == after, "long_corridor_moved_geometry")
	check(float(player.corridor_stretch_target) == 1.0, "long_corridor_no_player_effect")
	anomalies.activate("violent_patient")
	for _i in 3:
		await process_frame
	check(float(player.corridor_stretch_target) == 0.0, "long_corridor_slows_player_during_chase")
	await _clear_danger()
	player.set_corridor_stretch(1.0)
	anomalies._end_long_corridor()
	check(float(player.corridor_stretch_target) == 0.0, "long_corridor_never_ends")
	# moving_wheelchair must move its model as one piece.
	var roots: Array[Node3D] = []
	anomalies._collect_named_roots(hospital, "wheelchair", roots)
	check(roots.size() == 1, "wheelchair_roots_%d" % roots.size())
	await _teardown()

func _east_offsets() -> Array:
	var out := []
	for node in get_nodes_in_group("care_interactables"):
		var area := node.get_node_or_null("CareInteractionArea") as Area3D
		if area and (node as Node3D).global_position.x > 9.0:
			out.append(snappedf((node as Node3D).global_position.x, 0.01))
			out.append(snappedf((area.get_child(0) as Node3D).global_position.x, 0.01))
	return out

func _room_zero_door() -> void:
	await _setup(10)
	anomalies.activate("room_zero")
	var copy := hospital.find_child("ANOMALY_ROOM_ZERO", true, false)
	check(copy != null and copy.has_method("interact"), "room_zero_door_not_interactive")
	if copy and copy.has_method("interact"):
		copy.interact(player)
		check("room_zero" in endings, "room_zero_ending_not_requested_%s" % [endings])
	await _teardown()

func _extra_patient_in_ward6() -> void:
	await _setup(2)
	var count: int = state.patient_count
	anomalies.activate("extra_patient")
	var figure := hospital.find_child("anomaly_extra_patient", true, false) as Node3D
	var klimova := _patient("klimova") as Node3D
	check(figure != null and figure.visible, "extra_patient_no_figure")
	if figure:
		check(figure.global_position.distance_to(klimova.global_position) < 2.5, "extra_patient_not_in_ward6")
	check(int(state.patient_count) == count + 1, "extra_patient_count_%d" % state.patient_count)
	await _teardown()

func _status_lines_do_not_queue() -> void:
	await _setup(0)
	# Let the "00:00" shift line finish so the status path starts from idle.
	for _i in 60:
		if not hud.message_busy and hud.message_queue.is_empty():
			break
		await create_timer(0.2).timeout
	for _i in 40:
		player.take_sanity_damage(1, "test", "anomaly")
		player.take_damage(1, "test", "orderly")
	check(hud.message_queue.is_empty(), "status_lines_queued_%d" % hud.message_queue.size())
	hud.show_message("STORY_LINE", 4.0)
	check(hud.message_label.text == "STORY_LINE", "story_line_waits_behind_status")
	player.take_damage(1, "test", "orderly")
	check(hud.message_label.text == "STORY_LINE", "status_replaced_story_line")
	await _teardown()

func _flood_blocks_then_releases_handoff() -> void:
	await _setup(2)
	care.trigger_water_spill()
	for task in state.tasks:
		if task != "final_call":
			state.tasks[task] = true
	levels._try_finish_shift()
	check(String(state.get_flag("handoff_waiting", "")) == "flood", "flood_wait_not_recorded")
	check("Уберите воду" in String(hud.objective_label.text), "flood_objective_%s" % hud.objective_label.text)
	_use("mop_bucket")
	_use("water_spill")
	for _i in 3:
		await process_frame
	# Night 3 does not score spill_cleanup, so no task signal re-runs the check.
	check(bool(state.get_flag("handoff_ready", false)), "handoff_not_offered_after_cleanup")
	await _teardown()

func _exit_door_after_work() -> void:
	await _setup(0)
	state.set_flag("handoff_ready", true)
	clock.pause_clock(true)
	clock.hour = 5
	clock.minute = 58
	get_first_node_in_group("hospital_exit").interact(player)
	check(endings.is_empty(), "exit_door_ended_finished_shift_%s" % [endings])
	await _teardown()

func _night8_chair_returns() -> void:
	await _setup(7)
	var chair := _node("misplaced_chair")
	_use("misplaced_chair")
	check(levels.fired.has("chair_returns") and chair.visible and _layer(chair) == 1, "n8_chair_return_has_no_effect")
	var messages: Array = hud.get_message_history()
	var moved_at := -1
	var returned_at := -1
	for i in messages.size():
		if "Стул отставлен к стене" in String(messages[i].text):
			moved_at = i
		if "Стул снова стоит" in String(messages[i].text):
			returned_at = i
	check(moved_at >= 0 and returned_at > moved_at, "n8_story_line_before_result")
	_use("misplaced_chair")
	check(not chair.visible, "n8_returned_chair_cannot_be_cleared")
	await _teardown()

func _hostile_beat_waits_for_danger() -> void:
	await _setup(0)
	anomalies.activate("violent_patient")
	await process_frame
	levels._run_beat(["spawn", "hostile"])
	check(hospital.get_node_or_null("hostile_orderly") == null, "hostile_overlapped_violent_patient")
	await _clear_danger()
	for _i in 3:
		await process_frame
	check(hospital.get_node_or_null("hostile_orderly") != null, "hostile_beat_dropped")
	await _teardown()

func _objective_hint_skips_final_call(index: int) -> void:
	await _setup(index)
	var journal := get_first_node_in_group("documents")
	journal.interact(player)
	hud.close_document()
	var text := String(hud.objective_label.text)
	check(not "звонок" in text, "n%d_hint_mentions_call: %s" % [index + 1, text])
	if index == 3:
		check("доску назначений" in text, "n4_hint_does_not_point_at_board: %s" % text)
	_use("med_stethoscope")
	check(not _history_has("ответьте на звонок"), "n%d_pickup_refusal_mentions_call" % (index + 1))
	await _teardown()

func _night9_alarm_order() -> void:
	await _setup(8)
	_use("fire_alarm_panel")
	check(not bool(state.tasks.obj_fire_alarm), "n9_panel_silenced_before_alarm")
	var journal := get_first_node_in_group("documents")
	journal.interact(player)
	hud.close_document()
	check(levels.fired.has("smoke_starts") and not levels.fired.has("alarm_sounds"), "n9_alarm_not_staged_after_smoke")
	_use("elevator_inspection")
	check(levels.fired.has("alarm_sounds"), "n9_alarm_missing_after_smoke")
	_use("fire_alarm_panel")
	check(bool(state.tasks.obj_fire_alarm), "n9_panel_not_done_after_alarm")
	await _teardown()
