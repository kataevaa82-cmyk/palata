extends CanvasLayer

@onready var prompt: Label = $Prompt
@onready var time_label: Label = $TimeLabel
@onready var document_panel: ColorRect = $DocumentPanel
@onready var document_text: Label = $DocumentPanel/DocumentText
@onready var message_label: Label = $MessageLabel
@onready var count_panel: ColorRect = $CountPanel
@onready var start_panel: ColorRect = $StartPanel
@onready var start_button: Button = $StartPanel/StartButton
@onready var loading_label: Label = $StartPanel/LoadingLabel
@onready var pause_panel: ColorRect = $PausePanel
@onready var ending_panel: ColorRect = $EndingPanel
@onready var ending_title: Label = $EndingPanel/EndingTitle
@onready var ending_text: Label = $EndingPanel/EndingText
@onready var objective_label: Label = $ObjectiveLabel
@onready var health_bar: ProgressBar = $VitalsPanel/HealthBar
@onready var health_value: Label = $VitalsPanel/HealthValue
@onready var sanity_bar: ProgressBar = $VitalsPanel/SanityBar
@onready var sanity_value: Label = $VitalsPanel/SanityValue
@onready var sanity_whiteout: ColorRect = $SanityWhiteout
@onready var mission_title: Label = $MissionPanel/MissionTitle
@onready var mission_text: Label = $MissionPanel/MissionText
@onready var inventory_text: Label = $MissionPanel/InventoryText
@onready var level_select: OptionButton = $StartPanel/LevelSelect
@onready var level_brief: Label = $StartPanel/LevelBrief
@onready var intro_label: Label = $StartPanel/Intro
@onready var count_question: Label = $CountPanel/Question
@onready var document_close_hint: Label = $DocumentPanel/CloseHint
@onready var language_button: Button = $StartPanel/LanguageButton
var pending_phone: Node
var message_tween: Tween
var message_queue: Array[Dictionary] = []
var message_busy := false
var message_showing_status := false
var pending_status: Dictionary = {}
var message_history: Array[Dictionary] = []
var loading_complete := false
var mobile_interface := false
var document_close_button: Button

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	add_to_group("hud")
	start_button.pressed.connect(_start_pressed)
	$PausePanel/ContinueButton.pressed.connect(_continue_pressed)
	$PausePanel/RestartButton.pressed.connect(_restart_pressed)
	$EndingPanel/RestartButton.pressed.connect(_restart_pressed)
	$EndingPanel/QuitButton.pressed.connect(_quit_pressed)
	start_button.disabled = true
	language_button.pressed.connect(_on_language_pressed)
	_populate_levels()
	var platform := _platform()
	if platform:
		mobile_interface = platform.is_mobile_device()
		platform.progress_changed.connect(_refresh_level_labels)
		platform.device_type_detected.connect(_on_device_type_detected)
		platform.language_detected.connect(_on_language_detected)
		LevelManager.selected_index = platform.selected_night()
		level_select.select(LevelManager.selected_index)
		_refresh_level_brief()
	_refresh_language_button()
	_configure_mobile_ui()
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	var player := get_tree().get_first_node_in_group("player")
	if player:
		player.set_frozen(true)
		player.health_changed.connect(_on_health_changed)
		player.sanity_changed.connect(_on_sanity_changed)
		_on_health_changed(player.health)
		_on_sanity_changed(player.sanity)
	var tm := get_tree().get_first_node_in_group("time_manager")
	if tm:
		tm.minute_changed.connect(_on_minute_changed)
		time_label.text = tm.formatted_time()

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if start_panel.visible and event.keycode in [KEY_ENTER, KEY_KP_ENTER] and loading_complete:
			_start_pressed()
			get_viewport().set_input_as_handled()
			return
		if ending_panel.visible and event.keycode in [KEY_ENTER, KEY_KP_ENTER]:
			_restart_pressed()
			get_viewport().set_input_as_handled()
			return
	if pending_phone and event is InputEventKey and event.pressed and not event.echo:
		var answer := -1
		if event.keycode == KEY_6:
			answer = 6
		elif event.keycode == KEY_7:
			answer = 7
		elif event.keycode == KEY_8:
			answer = 8
		if answer != -1:
			answer_patient_count(answer)
			get_viewport().set_input_as_handled()
			return
	if event.is_action_pressed("ui_cancel") and not start_panel.visible and not ending_panel.visible:
		if document_panel.visible:
			close_document()
		else:
			_set_paused(not pause_panel.visible)
		get_viewport().set_input_as_handled()

func _populate_levels() -> void:
	level_select.clear()
	for index in LevelManager.level_count():
		var level: Dictionary = LevelManager.LEVELS[index]
		level_select.add_item(tr("НОЧЬ %d — %s") % [index + 1, tr(String(level.title))], index)
	# Debug exports are used for content review and must always expose every
	# night, even if release progression starts disabling entries later.
	if OS.is_debug_build():
		for index in level_select.item_count:
			level_select.set_item_disabled(index, false)
		print("DEBUG_LEVELS_UNLOCKED count=", level_select.item_count)
	# LevelManager.selected_index is a static, so the night survives the
	# reload_current_scene() restart and comes back selected here.
	level_select.select(clampi(LevelManager.selected_index, 0, LevelManager.level_count() - 1))
	# Guarded: the language switch repopulates the list, and an unguarded
	# connect() here would stack a second and third handler on every switch.
	if not level_select.item_selected.is_connected(_on_level_selected):
		level_select.item_selected.connect(_on_level_selected)
	_refresh_level_labels()
	_refresh_level_brief()

func _refresh_level_labels() -> void:
	if not level_select:
		return
	var platform := _platform()
	for index in LevelManager.level_count():
		var level: Dictionary = LevelManager.LEVELS[index]
		var completed: bool = bool(platform and platform.is_night_completed(index))
		level_select.set_item_text(index, tr("НОЧЬ %d — %s%s") % [
			index + 1, tr(String(level.title)), "  ✓" if completed else ""])

func _on_level_selected(index: int) -> void:
	LevelManager.selected_index = index
	var platform := _platform()
	if platform:
		platform.set_selected_night(index)
	_refresh_level_brief()
	# The props for every night are already in the scene; re-run the whitelist so
	# switching nights on the start screen swaps what is standing in the ward.
	var levels := get_tree().get_first_node_in_group("level_manager")
	var hospital := get_tree().get_first_node_in_group("hospital_model")
	if levels and hospital:
		levels.apply_prop_visibility(hospital)

func _refresh_level_brief() -> void:
	level_brief.text = tr(String(LevelManager.level().get("brief", "")))

# --- language -----------------------------------------------------------------
# Labels whose text sits in the scene re-translate themselves when the locale
# changes; everything this script builds by hand (the night list, the brief, the
# intro line, the loading line) has to be rebuilt, so the switch does it all here
# rather than waiting for the next reload.

func _on_language_pressed() -> void:
	var next := "en" if TranslationServer.get_locale().begins_with("ru") else "ru"
	var platform := _platform()
	if platform:
		platform.set_language(next)
	else:
		TranslationServer.set_locale(next)
	_apply_language()

func _on_language_detected(_locale: String) -> void:
	_apply_language()

func _apply_language() -> void:
	_refresh_language_button()
	_populate_levels()
	level_select.select(clampi(LevelManager.selected_index, 0, LevelManager.level_count() - 1))
	_refresh_level_brief()
	_configure_mobile_ui()
	if loading_complete:
		loading_label.text = tr("Отделение готово")
	var director := get_tree().get_first_node_in_group("game_director")
	if director and director.has_method("refresh_objective"):
		director.refresh_objective()
	var care := get_tree().get_first_node_in_group("care_manager")
	if care and care.has_method("_refresh_hud"):
		care._refresh_hud()

func _refresh_language_button() -> void:
	# The button shows the language it switches TO, not the current one.
	language_button.text = "EN" if TranslationServer.get_locale().begins_with("ru") else tr("РУС")

func set_loading_complete() -> void:
	loading_complete = true
	loading_label.text = tr("Отделение готово")
	start_button.disabled = false
	start_button.grab_focus()
	var platform := _platform()
	if platform:
		platform.notify_game_ready()

func _start_pressed() -> void:
	if not loading_complete:
		return
	# The ad for moving between levels goes here, in front of the night the
	# player is about to start - never in front of their FIRST one, and never
	# during a shift. The SDK skips it and calls straight back when it is too
	# soon after the last one, so this cannot stall the start button.
	var platform := _platform()
	if platform and int(platform.progress.get("shifts_finished", 0)) > 0:
		start_button.disabled = true
		platform.show_interstitial(_begin_shift)
		return
	_begin_shift()

func _begin_shift() -> void:
	start_button.disabled = false
	start_panel.visible = false
	message_queue.clear()
	message_history.clear()
	message_busy = false
	message_showing_status = false
	pending_status = {}
	var director := get_tree().get_first_node_in_group("game_director")
	if director:
		director.start_shift()
	var platform := _platform()
	if platform:
		platform.set_selected_night(LevelManager.selected_index)
		platform.set_gameplay_active(true)
	call_deferred("_capture_mouse")

func _capture_mouse() -> void:
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if mobile_interface else Input.MOUSE_MODE_CAPTURED

func _set_paused(value: bool) -> void:
	pause_panel.visible = value
	get_tree().paused = value
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if value or mobile_interface else Input.MOUSE_MODE_CAPTURED
	var platform := _platform()
	if platform:
		platform.set_gameplay_active(not value)

func _continue_pressed() -> void:
	_set_paused(false)

func _restart_pressed() -> void:
	var platform := _platform()
	if ending_panel.visible and platform:
		platform.show_interstitial(Callable(self, "_reload_current_scene"))
	else:
		_reload_current_scene()

func _quit_pressed() -> void:
	if OS.has_feature("web"):
		var platform := _platform()
		if platform:
			platform.show_interstitial(Callable(self, "_reload_current_scene"))
		else:
			_reload_current_scene()
	else:
		get_tree().quit()

func _reload_current_scene() -> void:
	get_tree().paused = false
	get_tree().reload_current_scene()

func set_objective(value: String) -> void:
	objective_label.text = value

func show_ending(id: String, success: bool) -> void:
	ending_panel.visible = true
	ending_title.text = "06:00" if success else tr("СМЕНА НЕ ОКОНЧЕНА")
	match id:
		"lost_mind":
			ending_title.text = tr("РАССУДОК УТРАЧЕН")
			ending_text.text = tr("Вы перестали отличать пациентов от тех, кого нет в журнале.\n\nУтром на посту нашли аккуратно заполненную карточку: ваша фамилия, палата 0.")
		"killed_by_orderly":
			ending_title.text = tr("КРАСНЫЙ ВЗГЛЯД")
			ending_text.text = tr("Вы слишком долго оставались на линии взгляда санитарки.\n\nНужно было закрыть дверь и спрятаться в помещении.")
		"killed_by_head_nurse":
			ending_title.text = tr("СИНИЙ ВЗГЛЯД")
			ending_text.text = tr("Главная медсестра нашла ошибку в назначении.\n\nОт её синего взгляда можно было укрыться только в ординаторской.")
		"medical_error":
			ending_title.text = tr("ОШИБКА НАЗНАЧЕНИЯ")
			ending_text.text = tr("Вы перепутали пациента или препарат. Ночная смена закончилась до рассвета.")
		"killed_by_patient":
			ending_title.text = tr("ВЫ ПОГИБЛИ")
			ending_text.text = tr("Буйный пациент догнал вас в коридоре.\n\nУтром тележку нашли опрокинутой, а в журнале дежурств появилась новая строка.")
		"dawn":
			var dawn_epilogues := [
				"Серое утро заполнило коридор. Журнал принят, но под подписью появилась лишняя строка.",
				"Питание вернулось. Один индикатор всё ещё показывает этаж −1.",
				"Полог опечатан. След на плёнке остался со стороны пустого коридора.",
				"Свидетельство подписано. Демина снова числится в палате.",
				"Проверенный код партии появился на документе с вашей фамилией.",
				"В палате тепло, но один след инея на окне не исчез.",
				"Морозов вернулся в кровать. Мокрые следы продолжаются за дверью.",
				"В акте комиссии уже стоит подпись, которой вы не ставили.",
				"Короб сухой. Изнутри всё ещё слышно тихое тление.",
				"В журнале операции перечислены действия, которых никто не видел.",
				"Карточка палаты 0 подшита к вашему личному делу."
			]
			var index := clampi(LevelManager.selected_index, 0, dawn_epilogues.size() - 1)
			var result_suffix := ""
			var outcome_state := get_tree().get_first_node_in_group("hospital_state")
			if outcome_state and int(outcome_state.get_flag("medical_errors", 0)) > 0:
				result_suffix = tr("\n\nВ журнале отмечена медицинская ошибка; исправление принято дежурным врачом.")
			if outcome_state:
				result_suffix += tr("\n\nЗадачи смены: %d/%d. Пациентов осмотрено: %d.") % [outcome_state.task_count(), outcome_state.task_total(), outcome_state.observed_patient_count()]
			ending_text.text = tr("%s%s\n\nДневная медсестра посмотрела на вас:\n«А вы кто?»\n\nВаша фамилия снова появилась в журнале.") % [tr(dawn_epilogues[index]), result_suffix]
		"room_zero":
			ending_text.text = tr("За дверью не было палаты.\nТолько ещё один коридор и табличка: «ПАЛАТА 0».")
		"early_exit":
			ending_text.text = tr("За пожарной дверью оказался тот же коридор.\nПотом ещё один. Часы всё ещё показывают 05:53.")
		"unfinished_shift":
			ending_text.text = tr("Смена не принята.\n\nВы не закрыли журнал дежурства до 06:00.\nВ коридоре снова зазвонил телефон.")
		_:
			ending_text.text = tr("Ночная смена закончилась раньше рассвета.\nВ журнале появилась новая строка.")
	get_tree().paused = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	var platform := _platform()
	if platform:
		platform.set_gameplay_active(false)
	$EndingPanel/RestartButton.grab_focus()

func set_interaction_prompt(value: String) -> void:
	prompt.text = value.replace("[E]", tr("[ДЕЙСТВИЕ]")) if mobile_interface else value

func set_mission(title: String, detail: String, inventory: String) -> void:
	mission_title.text = title
	mission_text.text = detail
	inventory_text.text = inventory

func _on_health_changed(value: int) -> void:
	health_bar.value = value
	health_value.text = str(value)
	if value <= 30:
		health_value.modulate = Color(1.0, 0.22, 0.16)
	else:
		health_value.modulate = Color.WHITE

func _on_sanity_changed(value: int) -> void:
	sanity_bar.value = value
	sanity_value.text = str(value)
	if value <= 30:
		sanity_value.modulate = Color(0.75, 0.32, 1.0)
	else:
		sanity_value.modulate = Color.WHITE
	var whiteout_strength := clampf((30.0 - float(value)) / 30.0, 0.0, 1.0) * 0.58
	sanity_whiteout.color.a = whiteout_strength

func is_blocking_gameplay() -> bool:
	return start_panel.visible or pause_panel.visible or ending_panel.visible or document_panel.visible or count_panel.visible

func _on_minute_changed(_hour: int, _minute: int, formatted: String) -> void:
	time_label.text = formatted

func open_document(text: String) -> void:
	document_text.text = text
	document_panel.visible = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	var platform := _platform()
	if platform:
		platform.set_gameplay_active(false)

func close_document() -> void:
	document_panel.visible = false
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if mobile_interface else Input.MOUSE_MODE_CAPTURED
	var platform := _platform()
	if platform and not pause_panel.visible and not ending_panel.visible:
		platform.set_gameplay_active(true)

func show_message(text: String, duration := 3.0) -> void:
	var payload := {"text": text, "duration": maxf(float(duration), 1.5)}
	_remember_message(text)
	if message_busy and not message_showing_status:
		# Keep the result already on screen readable. The next assignment or
		# ambience line is queued instead of replacing it in the same frame.
		if message_queue.is_empty() or String(message_queue.back().text) != text:
			message_queue.append(payload)
		return
	# Nothing on screen, or only a damage/sanity status line: a status is never
	# worth making a story line wait for.
	_show_queued_message(payload)

func show_status(text: String, duration := 1.4) -> void:
	# Damage and sanity ticks arrive several times a second while an enemy looks
	# at the player. Queued like story lines they built a backlog of half a minute
	# of stale numbers in front of hints and story beats; instead only the latest
	# one is kept, and it never waits behind or delays another message.
	_remember_message(text)
	var payload := {"text": text, "duration": maxf(float(duration), 1.0), "status": true,
		"time": Time.get_ticks_msec()}
	if not message_busy or message_showing_status:
		_show_queued_message(payload)
	else:
		pending_status = payload

func _remember_message(text: String) -> void:
	message_history.append({"text": text, "time": Time.get_ticks_msec()})
	if message_history.size() > 50:
		message_history.pop_front()

func _show_queued_message(payload: Dictionary) -> void:
	message_busy = true
	message_showing_status = bool(payload.get("status", false))
	var text_value := String(payload.get("text", ""))
	message_label.text = text_value.replace(tr("нажмите E"), tr("нажмите ДЕЙСТВИЕ")).replace("[E]", tr("[ДЕЙСТВИЕ]")) if mobile_interface else text_value
	message_label.modulate.a = 1.0
	if message_tween and message_tween.is_running():
		message_tween.kill()
	var duration := float(payload.get("duration", 3.0))
	if message_queue.size() >= 3:
		# A long backlog is read faster rather than left to fall minutes behind.
		duration = minf(duration, 2.0)
	message_tween = create_tween()
	message_tween.tween_interval(duration)
	message_tween.tween_property(message_label, "modulate:a", 0.0, 0.8 if message_queue.is_empty() else 0.3)
	message_tween.tween_callback(_finish_message)

func _finish_message() -> void:
	message_busy = false
	message_showing_status = false
	if not message_queue.is_empty():
		var next: Dictionary = message_queue.pop_front()
		_show_queued_message(next)
		return
	if not pending_status.is_empty():
		var status := pending_status
		pending_status = {}
		# A status that waited behind a story line is only shown while current.
		if Time.get_ticks_msec() - int(status.get("time", 0)) <= 2500:
			_show_queued_message(status)

func get_message_history() -> Array[Dictionary]:
	return message_history.duplicate()

func begin_count_question(phone: Node) -> void:
	pending_phone = phone
	count_panel.visible = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	if mobile_interface:
		count_question.text = tr("Сколько пациентов сейчас в отделении?\n\nВыберите ответ")

func answer_patient_count(answer: int) -> void:
	if not pending_phone or answer not in [6, 7, 8]:
		return
	pending_phone.answer_count(answer)
	pending_phone = null
	count_panel.visible = false
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if mobile_interface else Input.MOUSE_MODE_CAPTURED

func toggle_pause_from_mobile() -> void:
	if not start_panel.visible and not ending_panel.visible and not document_panel.visible and not count_panel.visible:
		_set_paused(not pause_panel.visible)

func mobile_gameplay_controls_visible() -> bool:
	var state := get_tree().get_first_node_in_group("hospital_state")
	return (
		state and state.shift_started
		and not start_panel.visible
		and not pause_panel.visible
		and not ending_panel.visible
		and not document_panel.visible
		and not count_panel.visible)

func _platform() -> Node:
	return get_tree().get_first_node_in_group("yandex_sdk")

func _on_device_type_detected(value: String) -> void:
	mobile_interface = value in ["mobile", "tablet"] or DisplayServer.is_touchscreen_available()
	_configure_mobile_ui()

func _configure_mobile_ui() -> void:
	if not is_node_ready():
		return
	if mobile_interface:
		intro_label.text = tr("00:00. Вы заступаете на ночную смену.\nЛевый стик — движение    Правая часть экрана — взгляд\nДЕЙСТВИЕ — взаимодействие    ФОНАРИК — свет")
		_apply_mobile_readability()
		document_close_hint.visible = false
		$EndingPanel/QuitButton.text = tr("В МЕНЮ")
		if not document_close_button:
			document_close_button = Button.new()
			document_close_button.name = "MobileCloseButton"
			document_close_button.text = tr("ЗАКРЫТЬ")
			document_close_button.position = Vector2(340.0, 518.0)
			document_close_button.size = Vector2(260.0, 72.0)
			document_close_button.add_theme_font_size_override("font_size", 22)
			document_close_button.pressed.connect(close_document)
			document_panel.add_child(document_close_button)
	else:
		intro_label.text = tr("00:00. Вы заступаете на ночную смену.\nWASD — движение    Мышь — взгляд    E — действие    F — фонарик    Esc — пауза")
		document_close_hint.visible = true
		if document_close_button:
			document_close_button.queue_free()
			document_close_button = null

func _apply_mobile_readability() -> void:
	$StartPanel/Title.add_theme_font_size_override("font_size", 46)
	$StartPanel/Subtitle.add_theme_font_size_override("font_size", 28)
	intro_label.add_theme_font_size_override("font_size", 21)
	intro_label.position = Vector2(230.0, 216.0)
	intro_label.size = Vector2(820.0, 100.0)
	$StartPanel/LevelLabel.add_theme_font_size_override("font_size", 21)
	$StartPanel/LevelLabel.position = Vector2(280.0, 322.0)
	$StartPanel/LevelLabel.size = Vector2(310.0, 56.0)
	level_select.add_theme_font_size_override("font_size", 21)
	level_select.position = Vector2(608.0, 322.0)
	level_select.size = Vector2(400.0, 56.0)
	level_brief.add_theme_font_size_override("font_size", 20)
	loading_label.add_theme_font_size_override("font_size", 19)
	start_button.add_theme_font_size_override("font_size", 23)
	start_button.position = Vector2(450.0, 510.0)
	start_button.size = Vector2(380.0, 76.0)
	$StartPanel/Warning.add_theme_font_size_override("font_size", 16)

	$VitalsPanel/HealthTitle.add_theme_font_size_override("font_size", 16)
	$VitalsPanel/HealthValue.add_theme_font_size_override("font_size", 16)
	$VitalsPanel/SanityTitle.add_theme_font_size_override("font_size", 16)
	$VitalsPanel/SanityValue.add_theme_font_size_override("font_size", 16)
	mission_title.add_theme_font_size_override("font_size", 20)
	mission_text.add_theme_font_size_override("font_size", 18)
	inventory_text.add_theme_font_size_override("font_size", 17)
	time_label.add_theme_font_size_override("font_size", 22)
	prompt.add_theme_font_size_override("font_size", 24)
	message_label.add_theme_font_size_override("font_size", 24)
	objective_label.add_theme_font_size_override("font_size", 21)
	count_question.add_theme_font_size_override("font_size", 25)
	document_text.add_theme_font_size_override("font_size", 23)
	$PausePanel/Title.add_theme_font_size_override("font_size", 36)
	$PausePanel/ContinueButton.add_theme_font_size_override("font_size", 22)
	$PausePanel/RestartButton.add_theme_font_size_override("font_size", 22)
	ending_title.add_theme_font_size_override("font_size", 40)
	ending_text.add_theme_font_size_override("font_size", 24)
	$EndingPanel/RestartButton.add_theme_font_size_override("font_size", 21)
	$EndingPanel/QuitButton.add_theme_font_size_override("font_size", 21)
