extends Node

signal shift_started

var started := false
var reverse_clock_elapsed := 0.0

func _ready() -> void:
	add_to_group("game_director")
	var state := get_tree().get_first_node_in_group("hospital_state")
	if state:
		state.task_changed.connect(_on_task_changed)

func start_shift() -> void:
	if started:
		return
	started = true
	var state := get_tree().get_first_node_in_group("hospital_state")
	var time_manager := get_tree().get_first_node_in_group("time_manager")
	var event_manager := get_tree().get_first_node_in_group("event_manager")
	var player := get_tree().get_first_node_in_group("player")
	var levels := get_tree().get_first_node_in_group("level_manager")
	var anomalies := get_tree().get_first_node_in_group("anomaly_manager")
	if levels:
		levels.reset()
	if anomalies and anomalies.has_method("reset_shift"):
		anomalies.reset_shift()
	if state:
		state.reset_shift()
	if time_manager:
		time_manager.reset_clock()
		time_manager.start_clock()
	if event_manager:
		event_manager.start_events()
	if player:
		player.set_frozen(false)
	var mobile_controls := get_tree().get_first_node_in_group("mobile_controls")
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if mobile_controls and mobile_controls.mobile_enabled else Input.MOUSE_MODE_CAPTURED
	shift_started.emit()
	_update_objective()
	var hud := get_tree().get_first_node_in_group("hud")
	if hud:
		var level: Dictionary = LevelManager.level()
		hud.set_objective(tr("%s — выполните обязательные задачи смены.") % tr(String(level.title)))
		hud.show_message("00:00. %s." % tr(String(level.title)).capitalize(), 4.5)
	if levels:
		levels.start_progression()

func _on_task_changed(_summary: String) -> void:
	_update_objective()

func _update_objective() -> void:
	var state := get_tree().get_first_node_in_group("hospital_state")
	var hud := get_tree().get_first_node_in_group("hud")
	if not state or not hud:
		return
	var level: Dictionary = LevelManager.level()
	var required := int(level.get("required", 9))
	var done: int = state.task_count()
	var levels := get_tree().get_first_node_in_group("level_manager")
	var story_ready: bool = not levels or levels.completion_requirements_met(state)
	var next := tr("Работа завершена. Сдайте смену на посту.")
	if done < required or not story_ready:
		next = _next_hint(state)
	else:
		# The handoff can be held back after the last task; say by what, instead
		# of announcing an ending that is not coming.
		match String(state.get_flag("handoff_waiting", "")):
			"flood": next = tr("Уберите воду в душевой, затем сдайте смену на посту.")
			"danger": next = tr("Переждите опасность, затем сдайте смену на посту.")
	hud.set_objective(tr("%s   %s (нужно %d) — %s") % [tr(String(level.title)), state.task_summary(), required, next])

func _next_hint(state: Node) -> String:
	# Names the first unfinished task of the running night rather than night 1's
	# fixed journal-board-room4 chain.
	const HINTS := {
		"journal_checked": "Сверьте журнал пациентов.",
		"assignment_board_read": "Прочитайте доску назначений на посту.",
		"room4_call": "Ответьте на звонок из палаты №4.",
		"patient_count": "Назовите оператору правильное число пациентов.",
		"spill_cleanup": "Уберите воду в душевой.",
		"exit_check": "Проверьте пломбу пожарного выхода.",
		"elevator_check": "Осмотрите индикатор лифта.",
		"obj_fuse_box": "Замените пробки в щитке западного крыла.",
		"obj_emergency_light": "Включите аварийный фонарь.",
		"obj_disinfect": "Обработайте руки после карантина.",
		"obj_quarantine_curtain": "Осмотрите полог карантина.",
		"obj_death_certificate": "Заполните свидетельство на посту.",
		"obj_gurney": "Откатите каталку к лифту.",
		"obj_blood_chart": "Сверьте таблицу групп крови.",
		"obj_radiator_valve": "Стравите воздух из батареи в палате 3.",
		"obj_window_latch": "Закройте форточку.",
		"obj_slippers": "Осмотрите тапки у пожарной двери.",
		"obj_footprints": "Осмотрите следы в коридоре.",
		"obj_bed_note": "Прочитайте записку на кровати.",
		"obj_duty_journal": "Заполните журнал дежурства.",
		"obj_misplaced_chair": "Уберите стул с прохода.",
		"obj_floor_dirt": "Вымойте пол в коридоре.",
		"obj_extinguish": "Сбейте огонь в кабельном коробе.",
		"obj_fire_alarm": "Осмотрите панель сигнализации.",
		"obj_sterile_bix": "Вскройте стерильный бикс.",
		"obj_surgical_lamp": "Опустите и включите бестеневую лампу.",
		"obj_zero_card": "Прочитайте карточку палаты 0.",
		"obj_zero_door": "Отоприте дверь без номера."
	}
	for id in LevelManager.level().get("tasks", []):
		# final_call is the handoff itself and stays open until the very end;
		# naming it first used to pin the hint on it for the whole night.
		if id == "final_call" or state.tasks.get(id, false):
			continue
		if HINTS.has(id):
			return tr(String(HINTS[id]))
		if String(id).begins_with("care_"):
			if not bool(state.get_flag("assignment_board_opened", false)):
				return tr("Прочитайте доску назначений на посту.")
			return tr("Выполните назначение с доски дежурств.")
	return tr("Завершите обязательные задачи смены.")

func refresh_objective() -> void:
	_update_objective()

func _process(delta: float) -> void:
	if not started:
		return
	var time_manager := get_tree().get_first_node_in_group("time_manager")
	if not time_manager or not time_manager.reverse:
		reverse_clock_elapsed = 0.0
		return
	reverse_clock_elapsed += delta
	if reverse_clock_elapsed >= 7.0:
		time_manager.set_reverse(false)
		var audio := get_tree().get_first_node_in_group("audio_manager")
		if audio:
			audio.set_silence(false)
		var hud := get_tree().get_first_node_in_group("hud")
		if hud:
			hud.show_message(tr("Часы снова идут вперёд."), 3.0)
