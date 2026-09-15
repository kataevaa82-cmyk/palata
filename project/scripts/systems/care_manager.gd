extends Node

const ASSIGNMENTS := {
	"medication": {
		"task": "care_medication", "patient": "saveliev", "patient_name": "Савельев П. М.",
		"room": "палата 4, кровать 1", "item": "aminazine", "item_name": "Аминазин",
		"action": "medication", "verb": "Дайте назначенный препарат"
	},
	"vitals": {
		"task": "care_vitals", "patient": "levchenko", "patient_name": "Левченко А. Н.",
		"room": "палата 2, кровать 1", "item": "thermometer", "item_name": "Термометр",
		"action": "vitals", "verb": "Измерьте температуру"
	},
	"pulse": {
		"task": "care_pulse", "patient": "orlova", "patient_name": "Орлова Н. Д.",
		"room": "палата 3, кровать 1", "item": "stethoscope", "item_name": "Стетоскоп",
		"action": "pulse", "verb": "Проверьте пульс"
	},
	"linen": {
		"task": "care_linen", "patient": "morozov", "patient_name": "Морозов И. П.",
		"room": "палата 1, кровать 1", "item": "clean_linen", "item_name": "Чистое бельё",
		"action": "linen", "verb": "Смените постельное бельё"
	},
	"iv": {
		"task": "care_iv", "patient": "yudin", "patient_name": "Юдин С. К.",
		"room": "палата 6, кровать 1", "item": "saline", "item_name": "Физраствор",
		"action": "iv", "verb": "Замените пакет капельницы"
	},
	"dressing": {
		"task": "care_dressing", "patient": "demina", "patient_name": "Демина В. Р.",
		"room": "палата 5, кровать 1", "item": "bandage", "item_name": "Стерильный бинт",
		"action": "dressing", "verb": "Смените повязку"
	},
	"identity": {
		"task": "care_identity", "patient": "klimova", "patient_name": "Климова Т. С.",
		"room": "палата 6, кровать 2", "item": "", "item_name": "",
		"action": "identity", "verb": "Сверьте браслет и карточку"
	},
	# --- assignments introduced by the ten extra nights (level_manager.gd) ---
	"oxygen": {
		"task": "care_oxygen", "patient": "yudin", "patient_name": "Юдин С. К.",
		"room": "палата 6, кровать 1", "item": "oxygen_pillow", "item_name": "Кислородная подушка",
		"action": "oxygen", "verb": "Подключите кислородную подушку"
	},
	"quarantine_meds": {
		"task": "care_quarantine_meds", "patient": "yudin", "patient_name": "Юдин С. К.",
		"room": "палата 6, кровать 1", "item": "mask", "item_name": "Марлевая маска",
		"action": "quarantine_meds", "verb": "Войдите в карантин в маске"
	},
	"sputum": {
		"task": "care_sputum", "patient": "klimova", "patient_name": "Климова Т. С.",
		"room": "палата 6, кровать 2", "item": "sample_tube", "item_name": "Пробирка",
		"action": "sputum", "verb": "Возьмите мазок"
	},
	"pronounce": {
		"task": "care_pronounce", "patient": "demina", "patient_name": "Демина В. Р.",
		"room": "палата 5, кровать 1", "item": "stethoscope", "item_name": "Стетоскоп",
		"action": "pronounce", "verb": "Констатируйте смерть"
	},
	"shroud": {
		"task": "care_shroud", "patient": "demina", "patient_name": "Демина В. Р.",
		"room": "палата 5, кровать 1", "item": "body_bag", "item_name": "Транспортный мешок",
		"action": "shroud", "verb": "Упакуйте тело"
	},
	"transfusion": {
		"task": "care_transfusion", "patient": "saveliev", "patient_name": "Савельев П. М.",
		"room": "палата 4, кровать 1", "item": "blood_second", "item_name": "Кровь II(A)",
		"action": "transfusion", "verb": "Подключите переливание"
	},
	"warm_blanket": {
		"task": "care_warm_blanket", "patient": "morozov", "patient_name": "Морозов И. П.",
		"room": "палата 1, кровать 1", "item": "blanket", "item_name": "Второе одеяло",
		"action": "warm_blanket", "verb": "Укройте вторым одеялом"
	},
	"hot_tea": {
		"task": "care_hot_tea", "patient": "levchenko", "patient_name": "Левченко А. Н.",
		"room": "палата 2, кровать 1", "item": "hot_tea", "item_name": "Горячий чай",
		"action": "hot_tea", "verb": "Дайте горячий чай"
	},
	"return_patient": {
		"task": "care_return_patient", "patient": "morozov", "patient_name": "Морозов И. П.",
		"room": "лестничная площадка", "item": "", "item_name": "",
		"action": "return_patient", "verb": "Верните пациента в палату"
	},
	"prep_surgery": {
		"task": "care_prep_surgery", "patient": "saveliev", "patient_name": "Савельев П. М.",
		"room": "палата 4, кровать 1", "item": "surgical_gown", "item_name": "Стерильный халат",
		"action": "prep_surgery", "verb": "Подготовьте к операции"
	}
}

# Props the extra nights let you pick up. Keyed by the care_id main.gd binds
# from LEVEL_PROP_IDS, valued by the inventory item it becomes.
const LEVEL_SUPPLY_ITEMS := {
	"spare_fuses": "fuse",
	"oxygen_pillow": "oxygen_pillow",
	"mask_box": "mask",
	"sample_tube": "sample_tube",
	"body_bag": "body_bag",
	"blood_bag_first": "blood_first",
	"blood_bag_second": "blood_second",
	"blood_bag_third": "blood_third",
	"radiator_key": "radiator_key",
	"blanket_stack": "blanket",
	"tea_kettle": "hot_tea",
	"fire_extinguisher": "extinguisher",
	"surgical_gown": "surgical_gown",
	"zero_key": "zero_key"
}

# Items that serve an object task rather than a patient, so unlike a drug they
# may be picked up with no assignment running.
const FREE_ITEMS := ["fuse", "radiator_key", "extinguisher", "zero_key"]

# Props a story beat can put back after the player dealt with them (the chair on
# night 8, the window on night 6). The task stays ticked, but the returned prop
# must still be clearable instead of answering "already done" forever.
const REPEATABLE_OBJECT_TASKS := {
	"misplaced_chair": "Стул снова отставлен к стене.",
	"window_latch": "Форточка снова закрыта на шпингалет."
}

# Fixed installations stay where they are after use. Hiding a fuse box, a wall
# chart or a lamp that the result text says is now burning contradicted the text,
# and the blood chart has to remain readable for the label incident.
const FIXED_INSTALLATIONS := ["fuse_box", "emergency_lamp", "blood_chart", "radiator_valve",
	"fire_alarm_panel", "surgical_lamp"]

# One-shot prop interactions. `item` (when set) must be in hand; `mop` requires
# the mop instead. Completing one ticks its task in the night's own task list.
const LEVEL_OBJECT_TASKS := {
	"fuse_box": {"task": "obj_fuse_box", "item": "fuse", "prompt": "[E] Заменить пробки",
		"text": "Пробки заменены. Свет в западном крыле вернулся.", "lights": true},
	"emergency_lamp": {"task": "obj_emergency_light", "item": "", "prompt": "[E] Включить аварийный фонарь",
		"text": "Аварийный фонарь горит. Коридор снова видно.",
		"lamp": {"color": Color(1.0, 0.78, 0.52), "energy": 1.6, "range": 8.0, "height": 0.5}},
	"hand_sanitizer": {"task": "obj_disinfect", "item": "", "prompt": "[E] Обработать руки",
		"text": "Руки обработаны. Спирт щиплет трещины на костяшках."},
	"quarantine_curtain": {"task": "obj_quarantine_curtain", "item": "", "prompt": "[E] Осмотреть полог карантина",
		"text": "Плёнка разрезана изнутри, ровно, от пола до замка."},
	"death_certificate": {"task": "obj_death_certificate", "item": "", "prompt": "[E] Заполнить свидетельство",
		"text": "Свидетельство заполнено. Графу «причина» вы оставили пустой."},
	"gurney": {"task": "obj_gurney", "item": "", "prompt": "[E] Откатить каталку к лифту",
		"text": "Каталка у лифта. Кнопка вызова уже нажата — не вами."},
	"blood_chart": {"task": "obj_blood_chart", "item": "", "prompt": "[E] Сверить таблицу групп",
		"text": "Савельев П. М. — вторая группа, II(A). Записано в карточке."},
	"radiator_valve": {"task": "obj_radiator_valve", "item": "radiator_key", "prompt": "[E] Стравить воздух из батареи",
		"text": "Воздух вышел с шипением. Батарея понемногу теплеет."},
	"window_latch": {"task": "obj_window_latch", "item": "", "prompt": "[E] Закрыть форточку",
		"text": "Форточка закрыта на шпингалет. Снег на подоконнике не тает."},
	"hospital_slippers": {"task": "obj_slippers", "item": "", "prompt": "[E] Осмотреть тапки",
		"text": "Тапки Морозова. Поставлены ровно, носками к двери."},
	"muddy_trail": {"task": "obj_footprints", "item": "", "prompt": "[E] Осмотреть следы",
		"text": "Следы босых ног. Ведут к пожарной двери и обратно."},
	"bed_note": {"task": "obj_bed_note", "item": "", "prompt": "[E] Прочитать записку",
		"text": "На листке одна строка: «Меня переводят в нулевую»."},
	"duty_journal_form": {"task": "obj_duty_journal", "item": "", "prompt": "[E] Заполнить журнал дежурства",
		"text": "Журнал заполнен до 06:00. Почерк ровный, ваш."},
	"misplaced_chair": {"task": "obj_misplaced_chair", "item": "", "prompt": "[E] Убрать стул с прохода",
		"text": "Стул отставлен к стене. Проход свободен."},
	"floor_dirt": {"task": "obj_floor_dirt", "item": "", "mop": true, "prompt": "[E] Вымыть пол",
		"text": "Пол вымыт. Разводы сходятся к палате 0."},
	"smoke_source": {"task": "obj_extinguish", "item": "extinguisher", "prompt": "[E] Сбить огонь в кабельном коробе",
		"text": "Пена сбила тление. В коробе оплавленная изоляция и ничего больше."},
	"fire_alarm_panel": {"task": "obj_fire_alarm", "item": "", "prompt": "[E] Осмотреть панель сигнализации",
		"text": "Панель показывает западное крыло. Сирену вы отключили."},
	"sterile_bix": {"task": "obj_sterile_bix", "item": "", "prompt": "[E] Вскрыть стерильный бикс",
		"text": "Бикс вскрыт. Индикаторная лента не изменила цвет — его не кипятили."},
	"surgical_lamp": {"task": "obj_surgical_lamp", "item": "", "prompt": "[E] Опустить и включить лампу",
		"text": "Бестеневая лампа горит над кушеткой. Под ней уже расстелена клеёнка.",
		"lamp": {"color": Color(0.92, 0.96, 1.0), "energy": 2.2, "range": 4.0, "height": -0.3}},
	"zero_card": {"task": "obj_zero_card", "item": "", "prompt": "[E] Прочитать карточку",
		"text": "Карточка: палата 0, койка 1. Фамилия ваша. Дата поступления — сегодня."},
	"zero_door": {"task": "obj_zero_door", "item": "zero_key", "prompt": "[E] Отпереть дверь без номера",
		"text": "Ключ подошёл. За дверью — тот же коридор, и в его конце снова эта дверь."}
}

const SUPPLY_ITEMS := {
	"med_aminazine": "aminazine",
	"med_cordiamin": "cordiamin",
	"med_bandage": "bandage",
	"med_saline": "saline",
	"med_stethoscope": "stethoscope",
	"med_thermometer": "thermometer",
	"clean_linen": "clean_linen"
}

const ITEM_NAMES := {
	"aminazine": "Аминазин",
	"cordiamin": "Кордиамин",
	"bandage": "Стерильный бинт",
	"saline": "Физраствор",
	"stethoscope": "Стетоскоп",
	"thermometer": "Термометр",
	"clean_linen": "Чистое бельё",
	"dirty_linen": "Грязное бельё",
	"fuse": "Запасные пробки",
	"oxygen_pillow": "Кислородная подушка",
	"mask": "Марлевая маска",
	"sample_tube": "Пробирка для мазка",
	"body_bag": "Транспортный мешок",
	"blood_first": "Кровь I(0)",
	"blood_second": "Кровь II(A)",
	"blood_third": "Кровь III(B)",
	"radiator_key": "Ключ для батарей",
	"blanket": "Второе одеяло",
	"hot_tea": "Горячий чай",
	"extinguisher": "Огнетушитель",
	"surgical_gown": "Стерильный халат",
	"zero_key": "Ключ без бирки"
}

var active_assignment := ""
var assignment_queue: Array[String] = []
var completed_assignments: Array[String] = []
var stage := "idle"
var carried_item := ""
var has_mop := false
var has_patient_restraints := false
var carried_source_node: Node3D
var mop_source_node: Node3D
var restraints_source_node: Node3D
var spill_active := false
var resting_at_computer := false
var rest_sessions := 0
var water_spill: Node3D
var started := false

func _ready() -> void:
	add_to_group("care_manager")
	var director := get_tree().get_first_node_in_group("game_director")
	if director:
		director.shift_started.connect(start_shift)
	call_deferred("_find_water_spill")

func start_shift() -> void:
	started = true
	active_assignment = ""
	assignment_queue.clear()
	completed_assignments.clear()
	stage = "idle"
	carried_item = ""
	has_mop = false
	has_patient_restraints = false
	carried_source_node = null
	mop_source_node = null
	restraints_source_node = null
	spill_active = false
	rest_sessions = 0
	_find_water_spill()
	if water_spill:
		water_spill.visible = false
	_refresh_hud()
	_sync_held_item()

func register_interactable(care_id: String, node: Node3D) -> void:
	if care_id == "water_spill":
		water_spill = node
		node.visible = spill_active

func _activate_scheduled_assignments() -> void:
	# The duty board is a complete source of the night's prescriptions. Phone
	# calls may still announce them, but a missed or delayed call must never lock
	# the player out of ordinary care tasks.
	for value in LevelManager.level().get("assignments", []):
		var assignment_id := String(value)
		if not ASSIGNMENTS.has(assignment_id) or assignment_id in completed_assignments:
			continue
		if assignment_id == active_assignment or assignment_id in assignment_queue:
			continue
		if active_assignment.is_empty():
			_start_assignment(assignment_id)
		else:
			assignment_queue.append(assignment_id)
	_refresh_hud()

func accept_phone_assignment(assignment_id: String) -> void:
	if not ASSIGNMENTS.has(assignment_id) or assignment_id in completed_assignments:
		return
	if assignment_id == active_assignment or assignment_id in assignment_queue:
		return
	if active_assignment.is_empty():
		_start_assignment(assignment_id)
	else:
		assignment_queue.append(assignment_id)
		_message(tr("Новое поручение записано в очередь. Сначала завершите текущее."), 3.5)
	_refresh_hud()

func cycle_assignment() -> void:
	# Let the player change priority without losing a partially collected task.
	# The active task moves to the back of the same queue; completed tasks are
	# never reintroduced.
	if active_assignment.is_empty() or assignment_queue.is_empty() or stage == "return":
		_message(tr("Сейчас нет другого доступного поручения."), 2.0)
		return
	_restore_world_item(carried_source_node)
	carried_source_node = null
	carried_item = ""
	assignment_queue.append(active_assignment)
	var next := String(assignment_queue.pop_front())
	_start_assignment(next)
	_sync_held_item()
	_message(tr("Приоритет изменён. Текущее поручение: %s.") % tr(String(ASSIGNMENTS[next].verb)), 2.8)

func _start_assignment(assignment_id: String) -> void:
	active_assignment = assignment_id
	var mission: Dictionary = ASSIGNMENTS[assignment_id]
	stage = "treat" if String(mission.item).is_empty() else "collect"
	carried_item = ""
	_message(tr("Получено поручение: %s — %s.") % [tr(String(mission.patient_name)), tr(String(mission.verb))], 4.0)
	_refresh_hud()

func get_interaction_text(care_id: String) -> String:
	match care_id:
		"assignment_board": return tr("[E] Прочитать назначения и список пациентов")
		"med_aminazine": return tr("[E] Взять: Аминазин")
		"med_cordiamin": return tr("[E] Взять: Кордиамин")
		"med_bandage": return tr("[E] Взять: стерильный бинт")
		"med_saline": return tr("[E] Взять пакет физраствора")
		"med_stethoscope": return tr("[E] Взять стетоскоп")
		"med_thermometer": return tr("[E] Взять термометр")
		"clean_linen": return tr("[E] Взять комплект чистого белья")
		"laundry_basket": return tr("[E] Сдать грязное бельё")
		"mop_bucket": return tr("[E] Взять швабру и ведро")
		"patient_restraints": return tr("[E] Взять вязки для буйного пациента (медсклад)")
		"doctors_computer": return tr("[E] Отдохнуть за компьютером и восстановить рассудок")
		"water_spill": return tr("[E] Вытереть разлитую воду") if spill_active else ""
		"fire_exit_seal":
			return tr("[E] Проверить пломбу пожарного выхода")
		"elevator_inspection": return tr("[E] Осмотреть индикатор лифта")
	if LEVEL_OBJECT_TASKS.has(care_id):
		if care_id == "sterile_bix":
			var bix_state := _state()
			if bix_state and bool(bix_state.get_flag("bix_used", false)) and not bool(bix_state.get_flag("bix_replaced", false)):
				return tr("[E] Списать вскрытый бикс и подтвердить замену")
			if bix_state and bool(bix_state.get_flag("bix_replaced", false)):
				return tr("[E] Вскрыть запечатанный заменённый бикс")
		return tr(String(LEVEL_OBJECT_TASKS[care_id].prompt))
	if LEVEL_SUPPLY_ITEMS.has(care_id):
		var supply_name := String(ITEM_NAMES.get(LEVEL_SUPPLY_ITEMS[care_id], care_id))
		var state := _state()
		if state and bool(state.get_flag("blood_labels_unreliable", false)) and String(care_id).begins_with("blood_bag"):
			# After the label anomaly the visible blood group is no longer a valid
			# selector. The player must inspect the bag's independent batch code.
			supply_name = tr("пакет крови — проверьте код партии")
		return tr("[E] Взять: %s") % tr(supply_name)
	if care_id == "escaped_patient":
		return tr("[E] Увести пациента в палату")
	return tr("[E] Осмотреть")

func interact_object(care_id: String, node: Node3D) -> void:
	if care_id == "assignment_board":
		var state := _state()
		if state:
			# Not every night scores the board, but the objective hint needs to
			# know whether the prescriptions have been handed out yet.
			state.set_flag("assignment_board_opened", true)
			state.complete_task("assignment_board_read")
		_activate_scheduled_assignments()
		var hud := _hud()
		if hud:
			hud.open_document(schedule_text())
		return
	if care_id == "mop_bucket":
		if stage == "return":
			_message(tr("Сначала сдайте грязное бельё в санитарной комнате."), 2.8)
			return
		_return_carried_supply_to_source()
		if has_patient_restraints:
			_restore_world_item(restraints_source_node)
			has_patient_restraints = false
			restraints_source_node = null
		has_mop = true
		mop_source_node = node
		_hide_world_item(node)
		_message(tr("Вы взяли швабру и ведро из служебной комнаты."), 2.8)
		_refresh_hud()
		_sync_held_item()
		return
	if care_id == "patient_restraints":
		if stage == "return":
			_message(tr("Сначала сдайте грязное бельё в санитарной комнате."), 2.8)
			return
		_return_carried_supply_to_source()
		if has_mop:
			_restore_world_item(mop_source_node)
			has_mop = false
			mop_source_node = null
		has_patient_restraints = true
		restraints_source_node = node
		_hide_world_item(node)
		_message(tr("Взяты вязки из настенного шкафа в медскладе. Подойдите к буйному пациенту и нажмите E."), 4.0)
		_refresh_hud()
		_sync_held_item()
		return
	if care_id == "doctors_computer":
		_rest_at_computer()
		return
	if care_id == "water_spill":
		_clean_water()
		return
	if care_id == "laundry_basket":
		_return_dirty_linen()
		return
	if care_id == "fire_exit_seal":
		_complete_optional("exit_check", tr("Пломба пожарного выхода цела. За дверью тихо."))
		return
	if care_id == "elevator_inspection":
		_complete_optional("elevator_check", tr("Индикатор лифта не горит. Вы не нажимали кнопку вызова."))
		return
	if LEVEL_OBJECT_TASKS.has(care_id):
		_do_object_task(care_id, node)
		return
	if care_id == "escaped_patient":
		_return_escaped_patient(node)
		return
	if LEVEL_SUPPLY_ITEMS.has(care_id):
		_pick_supply(String(LEVEL_SUPPLY_ITEMS[care_id]), node)
		return
	if SUPPLY_ITEMS.has(care_id):
		_pick_supply(String(SUPPLY_ITEMS[care_id]), node)

func _do_object_task(care_id: String, node: Node3D) -> void:
	var spec: Dictionary = LEVEL_OBJECT_TASKS[care_id]
	var state := _state()
	if state and state.tasks.get(String(spec.task), false):
		if REPEATABLE_OBJECT_TASKS.has(care_id):
			_hide_world_item(node)
			_message(tr(String(REPEATABLE_OBJECT_TASKS[care_id])), 3.0)
			return
		if care_id == "blood_chart":
			# The chart stays on the wall: after the label incident it is the
			# only independent way to identify the right unit.
			state.set_flag("blood_chart_checked", true)
			_message(tr("Таблица: Савельев П. М. — II(A), код партии B2-041."), 4.0)
			return
		_message(tr("Уже сделано."), 2.0)
		return
	if care_id == "gurney" and state and not bool(state.tasks.get("care_shroud", true)):
		# night 4 is told in order: the body is packed, goes missing from the
		# gurney, and only then can the gurney be taken to the lift.
		_message(tr("Каталка пустая. Сначала упакуйте тело."), 3.0)
		return
	if care_id == "fire_alarm_panel" and state and not bool(state.get_flag("fire_alarm_ringing", false)):
		_message(tr("Панель молчит. Все зоны в норме."), 3.0)
		return
	# A scheduled incident may open the bix before the nurse arrives. During a
	# real shift the first interaction is a visible recovery step, so an opened
	# kit cannot be silently consumed by the operation.
	if care_id == "sterile_bix" and state and bool(state.get_flag("bix_used", false)):
		var clock := get_tree().get_first_node_in_group("time_manager")
		if clock and bool(clock.get("running")) and not bool(state.get_flag("bix_replaced", false)):
			state.set_flag("bix_replaced", true)
			_message(tr("Бикс вскрыт до вас. Старый комплект списан — подтвердите замену запечатанным набором."), 4.5)
			return
	if bool(spec.get("mop", false)) and not has_mop:
		_message(tr("Нужны швабра и ведро из служебной комнаты."), 3.0)
		return
	var required := String(spec.get("item", ""))
	if not required.is_empty() and carried_item != required:
		_message(tr("Нужно: %s.") % tr(String(ITEM_NAMES.get(required, required))), 3.0)
		return
	if not required.is_empty():
		# The consumable is spent, so its source stays hidden rather than
		# popping back onto the shelf the way a returned drug does.
		carried_item = ""
		carried_source_node = null
		if not active_assignment.is_empty():
			# Picking the tool moved a running prescription to "treat"; with the
			# tool gone the prescribed item still has to be fetched.
			stage = "treat" if String(ASSIGNMENTS[active_assignment].item).is_empty() else "collect"
	if bool(spec.get("mop", false)):
		has_mop = false
		_restore_world_item(mop_source_node)
		mop_source_node = null
	if bool(spec.get("lights", false)):
		var levels := get_tree().get_first_node_in_group("level_manager")
		if levels:
			levels._set_lights(1.45, 999.0)
	if spec.has("lamp"):
		_add_prop_light(node, spec.lamp)
	# The prop and the result line settle first. complete_task() below can run
	# story beats that show their own lines or put this very prop back, and
	# those must come after what the player just did, not before it.
	if not care_id in FIXED_INSTALLATIONS:
		_hide_world_item(node)
	_message(tr(String(spec.text)), 4.5)
	if state:
		if care_id == "blood_chart":
			state.set_flag("blood_chart_checked", true)
		elif care_id == "sterile_bix":
			state.set_flag("bix_opened", true)
		elif care_id == "surgical_lamp":
			state.set_flag("surgical_lamp_on", true)
		state.record_observation("level_task", String(spec.task))
		state.complete_task(String(spec.task))
	var player := _player()
	if player:
		player.restore_sanity(4)
	_refresh_hud()
	_sync_held_item()

func _add_prop_light(node: Node3D, settings: Dictionary) -> void:
	if not node or node.get_node_or_null("PropLight"):
		return
	var light := OmniLight3D.new()
	light.name = "PropLight"
	light.light_color = settings.get("color", Color(1.0, 0.86, 0.62))
	light.light_energy = float(settings.get("energy", 1.2))
	light.omni_range = float(settings.get("range", 6.0))
	light.shadow_enabled = false
	# Anchored to the prop's visible geometry, not its origin: level props are
	# rooted at the floor or the wall mount depending on how they were modelled.
	var center := Vector3.ZERO
	var count := 0
	var to_local := node.global_transform.affine_inverse()
	for child in _all_nodes(node):
		if child is MeshInstance3D and (child as MeshInstance3D).mesh:
			var mesh_node := child as MeshInstance3D
			center += (to_local * mesh_node.global_transform) * mesh_node.mesh.get_aabb().get_center()
			count += 1
	if count > 0:
		center /= float(count)
	light.position = center + Vector3(0.0, float(settings.get("height", 0.4)), 0.0)
	# Deliberately not in "hospital_lights": the emergency lamp exists to keep
	# burning through blackout_all, and light switches must not reach it either.
	node.add_child(light)

func _return_escaped_patient(node: Node3D) -> void:
	if active_assignment != "return_patient":
		_message(tr("Он сидит и смотрит в стену. Без указания оператора трогать его нельзя."), 3.5)
		return
	_hide_world_item(node)
	var levels := get_tree().get_first_node_in_group("level_manager")
	if levels:
		levels._set_patient_visible("ward_1_bed_1_patient_v3", true)
	var state := _state()
	if state:
		state.set_patient_count(7)
	_complete_assignment(tr("Морозов уложен обратно в палату 1. Он ни разу не моргнул."))

func interact_patient(patient_id: String, patient_name: String, room: int, bed: int, patient_node: Node3D) -> void:
	var observation_state := _state()
	if observation_state and observation_state.has_method("record_patient_presence"):
		observation_state.record_patient_presence(patient_id, true, "patient_interaction")
	if active_assignment.is_empty():
		_message(tr("%s — палата %d, кровать %d. Браслет и карточка совпадают.") % [tr(patient_name), room, bed], 3.0)
		return
	var mission: Dictionary = ASSIGNMENTS[active_assignment]
	if stage == "collect":
		_message(tr("Сначала возьмите в указанном помещении: %s.") % tr(String(mission.item_name)), 2.8)
		return
	if stage == "return":
		# The linen is already changed. Touching a patient with the dirty set in
		# hand is not a prescription error, and pressing E again on Morozov right
		# after the change is the most natural thing a player does.
		_message(tr("Бельё уже заменено. Отнесите грязный комплект в корзину санитарной комнаты."), 3.0)
		return
	if patient_id != String(mission.patient):
		_medical_error(tr("Вы перепутали пациента. На браслете написано: %s.") % tr(patient_name), false)
		return
	var required_item := String(mission.item)
	if not required_item.is_empty() and carried_item != required_item:
		_medical_error(tr("Это не тот препарат или инструмент для %s.") % tr(patient_name), true)
		return
	if String(mission.action) == "transfusion":
		var blood_state := _state()
		if blood_state and bool(blood_state.get_flag("blood_labels_unreliable", false)) \
			and not bool(blood_state.get_flag("blood_batch_confirmed", false)):
			_message(tr("Переливание остановлено: код партии не подтверждён по таблице."), 4.0)
			return
	if String(mission.action) == "linen":
		_set_clean_linen(patient_node)
		carried_item = "dirty_linen"
		stage = "return"
		_message(tr("Бельё заменено. Отнесите грязный комплект в корзину санитарной комнаты."), 4.0)
		_refresh_hud()
		return
	var result_text: String = {
		"medication": tr("Пациент принял Аминазин. Дыхание стало ровнее."),
		"vitals": tr("Температура 37,4. Показание внесено в карточку."),
		"pulse": tr("Пульс 92. Под кроватью кто-то тихо постучал в ответ."),
		"iv": tr("Физраствор заменён, система снова капает."),
		"dressing": tr("Повязка заменена. На старом бинте нет крови."),
		"identity": tr("Браслет совпал с карточкой: Климова Т. С., палата 6."),
		"oxygen": tr("Подушка подключена. Юдин дышит через маску, глаза открыты."),
		"quarantine_meds": tr("Лекарство передано через полог. Маска не снималась."),
		"sputum": tr("Мазок взят. Климова не разжала зубы — стекло достали из-под языка."),
		"pronounce": tr("Тонов нет, зрачки не реагируют. Время смерти 01:20."),
		"shroud": tr("Тело упаковано. Молния застёгнута до конца — вы проверили дважды."),
		"transfusion": tr("Система подключена, кровь пошла. Савельев перестал дрожать."),
		"warm_blanket": tr("Второе одеяло подоткнуто. Морозов холодный на ощупь."),
		"hot_tea": tr("Левченко выпил чай до дна и попросил закрыть форточку."),
		"return_patient": tr("Пациент возвращён в палату 1."),
		"prep_surgery": tr("Савельев подготовлен: побрит, укрыт, вены отмечены.")
	}.get(String(mission.action), tr("Процедура выполнена."))
	var outcome_state := _state()
	if outcome_state:
		# Keep the medical result as structured state as well as readable text so
		# later story beats and the shift report can react to what was actually
		# done, rather than inferring it from a task counter.
		outcome_state.set_flag("patient_%s_outcome" % String(mission.patient), String(mission.action))
		if outcome_state.has_method("record_patient_outcome"):
			outcome_state.record_patient_outcome(String(mission.patient), String(mission.action))
	_complete_assignment(result_text)

func _pick_supply(item: String, source_node: Node3D) -> void:
	# Tools for the object tasks (fuses, the radiator key, the extinguisher) are
	# not prescribed to anyone, so they are exempt from the "read the board first"
	# rule that guards drugs and instruments.
	if active_assignment.is_empty() and not item in FREE_ITEMS:
		_message(tr("Без назначения брать препараты нельзя. Сначала прочитайте доску назначений на посту."), 2.8)
		return
	if item in ["blood_first", "blood_second", "blood_third"]:
		var blood_state := _state()
		if blood_state and bool(blood_state.get_flag("blood_labels_unreliable", false)) \
			and not bool(blood_state.get_flag("blood_chart_checked", false)):
			_message(tr("Этикетки ненадёжны. Сначала сверяйте таблицу групп крови."), 3.5)
			return
	if stage == "return":
		_message(tr("Сначала сдайте грязное бельё в санитарной комнате."), 2.8)
		return
	if has_patient_restraints:
		_restore_world_item(restraints_source_node)
		has_patient_restraints = false
		restraints_source_node = null
	if has_mop:
		_restore_world_item(mop_source_node)
		has_mop = false
		mop_source_node = null
	if carried_source_node and carried_source_node != source_node:
		_restore_world_item(carried_source_node)
	carried_source_node = source_node
	_hide_world_item(source_node)
	carried_item = item
	if not active_assignment.is_empty() and item in FREE_ITEMS and item != String(ASSIGNMENTS[active_assignment].item):
		# A fuse or a key serves an object task. It replaces whatever was in hand,
		# so the running prescription goes back to fetching its own item instead
		# of pointing the player at the patient with a tool.
		stage = "treat" if String(ASSIGNMENTS[active_assignment].item).is_empty() else "collect"
		_message(tr("Взято: %s.") % tr(String(ITEM_NAMES.get(item, item))), 3.0)
	elif active_assignment.is_empty():
		# A free tool belongs to an object task, not to a prescription: there is
		# no mission to compare it against, and looking one up here used to
		# throw on ASSIGNMENTS[""] - which aborted the pick-up before the hand
		# model and the HUD were updated.
		_message(tr("Взято: %s.") % tr(String(ITEM_NAMES.get(item, item))), 3.0)
	else:
		stage = "treat"
		var required := String(ASSIGNMENTS[active_assignment].item)
		if item == required:
			if item == "blood_second":
				var blood_state := _state()
				if blood_state:
					# Either picked while the labels were still true, or matched to
					# the chart after they stopped being - both identify the unit, and
					# a label incident later on cannot make the bag in hand wrong.
					blood_state.set_flag("blood_batch_confirmed", true)
				if blood_state and bool(blood_state.get_flag("blood_labels_unreliable", false)):
					_message(tr("Код партии сверён с таблицей: B2-041. Можно подключать систему."), 3.5)
					_refresh_hud()
					_sync_held_item()
					return
			_message(tr("Взято: %s. Проверьте фамилию, палату и кровать.") % tr(String(ITEM_NAMES.get(item, item))), 3.0)
		else:
			_message(tr("Взято: %s. Сверьте назначение — ошибка опасна.") % tr(String(ITEM_NAMES.get(item, item))), 3.0)
	_refresh_hud()
	_sync_held_item()

func _medical_error(text: String, physical_harm: bool) -> void:
	_message(text, 4.0)
	var player := _player()
	if player:
		player.take_sanity_damage(12, tr("ошибка в назначении"), "medical")
		if physical_harm:
			player.take_damage(10, tr("медицинская ошибка"), "medical")
	var state := _state()
	if state:
		state.set_flag("medical_errors", int(state.get_flag("medical_errors", 0)) + 1)
		state.record_observation("medical_error", active_assignment)
	var anomalies := get_tree().get_first_node_in_group("anomaly_manager")
	if anomalies and anomalies.has_method("request_head_nurse_inspector"):
		anomalies.request_head_nurse_inspector()
	_restore_world_item(carried_source_node)
	carried_source_node = null
	carried_item = ""
	stage = "treat" if String(ASSIGNMENTS[active_assignment].item).is_empty() else "collect"
	_refresh_hud()
	_sync_held_item()

func _complete_assignment(text: String) -> void:
	var finished := active_assignment
	completed_assignments.append(finished)
	_restore_world_item(carried_source_node)
	active_assignment = ""
	stage = "idle"
	carried_item = ""
	carried_source_node = null
	# The patient's reaction is shown before complete_task(): story beats that
	# this task unlocks queue their own lines, and they belong after it.
	_message(text, 4.0)
	var state := _state()
	if state:
		state.record_observation("care_complete", finished)
		# "Round complete" is relative to the night: nights 7-11 only hand out
		# two or three assignments, so a fixed five could never be reached.
		var handed_out: int = LevelManager.level().get("assignments", []).size()
		if completed_assignments.size() >= maxi(1, handed_out):
			state.set_flag("care_round_complete", true)
		state.complete_task(String(ASSIGNMENTS[finished].task))
	var player := _player()
	if player:
		player.restore_sanity(6)
	if active_assignment.is_empty() and not assignment_queue.is_empty():
		var next: String = assignment_queue.pop_front()
		_start_assignment(next)
	else:
		_refresh_hud()
	_sync_held_item()

func _return_dirty_linen() -> void:
	if active_assignment == "linen" and stage == "return" and carried_item == "dirty_linen":
		_complete_assignment(tr("Грязное бельё сдано. Комплект Морозова заменён правильно."))
	else:
		_message(tr("Сейчас сдавать нечего."), 2.0)

func trigger_water_spill() -> void:
	if spill_active:
		return
	spill_active = true
	_find_water_spill()
	if water_spill:
		water_spill.visible = true
	var state := _state()
	if state:
		state.set_flag("shower_flooded", true)
	_message(tr("АВАРИЯ: буйный пациент сорвал кран в душевой. Возьмите швабру в служебной."), 5.0)
	_refresh_hud()

func _clean_water() -> void:
	if not spill_active:
		return
	if not has_mop:
		_message(tr("Лужа растекается. Нужны швабра и ведро из служебной комнаты."), 3.5)
		return
	spill_active = false
	has_mop = false
	_restore_world_item(mop_source_node)
	mop_source_node = null
	if water_spill:
		water_spill.visible = false
	_message(tr("Вода убрана. В сливе остался длинный чёрный волос."), 4.0)
	var state := _state()
	if state:
		# Clear the flood before ticking the task: the task signal re-evaluates the
		# handoff, which used to still see the shower flooded and stay blocked.
		state.set_flag("shower_flooded", false)
		state.complete_task("spill_cleanup")
	var player := _player()
	if player:
		player.restore_sanity(5)
	_refresh_hud()
	_sync_held_item()

func _complete_optional(task_id: String, text: String) -> void:
	_message(text, 3.0)
	var state := _state()
	if state:
		state.complete_task(task_id)

func _set_clean_linen(patient_node: Node3D) -> void:
	for node in _all_nodes(patient_node):
		if node is MeshInstance3D and "blanket" in String(node.name).to_lower():
			var material := StandardMaterial3D.new()
			material.albedo_color = Color(0.46, 0.54, 0.45)
			material.roughness = 0.98
			(node as MeshInstance3D).material_override = material

func _refresh_hud() -> void:
	var hud := _hud()
	if not hud:
		return
	var title := tr("ОЖИДАНИЕ ПОРУЧЕНИЯ")
	var detail := tr("Прочитайте доску назначений на посту.")
	if not active_assignment.is_empty():
		var mission: Dictionary = ASSIGNMENTS[active_assignment]
		title = tr(String(mission.verb)).to_upper()
		if stage == "collect":
			var source_room := tr("САНИТАРНОЙ КОМНАТЕ") if String(mission.item) == "clean_linen" else tr("ПРОЦЕДУРНОЙ")
			detail = tr("Возьмите «%s» в %s.\nПациент: %s — %s") % [tr(String(mission.item_name)), source_room, tr(String(mission.patient_name)), tr(String(mission.room))]
		elif stage == "return":
			detail = tr("Отнесите грязное бельё в корзину санитарной комнаты.")
		else:
			detail = tr("Пациент: %s — %s. Сверьте браслет перед действием.") % [tr(String(mission.patient_name)), tr(String(mission.room))]
	if spill_active:
		title = tr("АВАРИЯ В ДУШЕВОЙ")
		detail = tr("Вытерите воду. %s") % (tr("Швабра у вас.") if has_mop else tr("Швабра и ведро находятся в служебной комнате."))
	var inventory := tr("Инвентарь: %s") % tr(String(ITEM_NAMES.get(carried_item, tr("пусто"))))
	if has_mop:
		inventory += tr(" + швабра")
	if has_patient_restraints:
		inventory += tr(" + вязки для пациента")
	if not assignment_queue.is_empty():
		if bool(hud.get("mobile_interface")):
			inventory += tr("   |   поручений в очереди: %d | ПОРУЧЕНИЕ — сменить приоритет") % assignment_queue.size()
		else:
			inventory += tr("   |   поручений в очереди: %d | TAB — сменить приоритет") % assignment_queue.size()
	hud.set_mission(title, detail, inventory)

func use_patient_restraints() -> bool:
	if not has_patient_restraints:
		return false
	_restore_world_item(restraints_source_node)
	has_patient_restraints = false
	restraints_source_node = null
	_refresh_hud()
	_sync_held_item()
	return true

func _hide_world_item(node: Node3D) -> void:
	if not node:
		return
	node.visible = false
	var area := node.get_node_or_null("CareInteractionArea") as Area3D
	if area:
		area.collision_layer = 0

func _restore_world_item(node: Node3D) -> void:
	if not node or not is_instance_valid(node):
		return
	node.visible = true
	var area := node.get_node_or_null("CareInteractionArea") as Area3D
	if area:
		area.collision_layer = 1

func _return_carried_supply_to_source() -> void:
	if carried_source_node:
		_restore_world_item(carried_source_node)
	carried_source_node = null
	carried_item = ""
	if not active_assignment.is_empty():
		stage = "treat" if String(ASSIGNMENTS[active_assignment].item).is_empty() else "collect"

func _sync_held_item() -> void:
	var player := _player()
	if not player or not player.has_method("show_held_inventory_item"):
		return
	var source: Node3D
	if has_patient_restraints:
		source = restraints_source_node
	elif not carried_item.is_empty():
		source = carried_source_node
	elif has_mop:
		source = mop_source_node
	player.show_held_inventory_item(source)

func _rest_at_computer() -> void:
	if resting_at_computer:
		return
	var player := _player()
	if not player:
		return
	var time_manager := get_tree().get_first_node_in_group("time_manager")
	var real_shift: bool = time_manager != null and bool(time_manager.get("running"))
	var target_sanity: int = int(player.max_sanity)
	if real_shift and rest_sessions >= 3:
		target_sanity = mini(player.max_sanity, 40)
	if player.sanity >= target_sanity:
		_message(tr("Вы не устали. Экран компьютера тихо гудит."), 2.2)
		return
	resting_at_computer = true
	rest_sessions += 1
	player.set_frozen(true)
	_message(tr("Вы садитесь за компьютер в ординаторской. Белая пелена понемногу отступает..."), 3.5)
	while is_instance_valid(player) and player.sanity < target_sanity:
		await get_tree().create_timer(0.18).timeout
		if not is_instance_valid(player) or player.dead:
			break
		player.restore_sanity(3)
	if is_instance_valid(player) and not player.dead:
		player.set_frozen(false)
		_message(tr("Рассудок восстановлен до безопасного уровня."), 2.5)
		var director := get_tree().get_first_node_in_group("game_director")
		if director and director.has_method("refresh_objective"):
			director.refresh_objective()
	resting_at_computer = false

func schedule_text() -> String:
	# Build the board from the selected night. The old implementation displayed
	# night 1's seven prescriptions on every shift, which made the board disagree
	# with the active mission and destroyed trust in the primary clue.
	var lines: Array[String] = [tr("НОЧНЫЕ НАЗНАЧЕНИЯ — СВЕРЯТЬ БРАСЛЕТ"), ""]
	for value in LevelManager.level().get("assignments", []):
		var id := String(value)
		if not ASSIGNMENTS.has(id):
			continue
		var mission: Dictionary = ASSIGNMENTS[id]
		var done := false
		var state := _state()
		if state:
			done = bool(state.tasks.get(String(mission.task), false))
		var marker := " ✓" if done else ""
		lines.append(tr("%s — %s — %s%s") % [tr(String(mission.room)), tr(String(mission.patient_name)), tr(String(mission.verb)), marker])
	lines.append("")
	lines.append(tr("Препараты и инструменты — в ПРОЦЕДУРНОЙ, если в задании не указано другое."))
	lines.append(tr("Чистое и грязное бельё — в САНИТАРНОЙ КОМНАТЕ."))
	lines.append(tr("Сверяйте фамилию, палату, кровать и предмет перед применением."))
	return "\n".join(lines)

func _find_water_spill() -> void:
	for node in get_tree().get_nodes_in_group("care_interactables"):
		if node.get("care_id") == "water_spill":
			water_spill = node as Node3D
			water_spill.visible = spill_active
			return

func _all_nodes(root: Node) -> Array[Node]:
	var result: Array[Node] = [root]
	for child in root.get_children():
		result.append_array(_all_nodes(child))
	return result

func _hud() -> Node:
	return get_tree().get_first_node_in_group("hud")

func _state() -> Node:
	return get_tree().get_first_node_in_group("hospital_state")

func _player() -> Node:
	return get_tree().get_first_node_in_group("player")

func _message(text: String, duration := 3.0) -> void:
	var hud := _hud()
	if hud:
		hud.show_message(text, duration)
