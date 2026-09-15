class_name LevelManager
extends Node

# Ten more night shifts over the same ward. Every night is pure data: which care
# assignments are listed on the duty board,
# which story incidents belong to the night, which anomalies the random pool may
# draw, and which of the level props
# modelled in tools/build_level_props.py are physically present.
#
# Nothing here spawns geometry. Every prop for every night lives in the exported
# GLB; main.gd hides them all on load and reveals only `props` for the selected
# night. That keeps one hospital model serving eleven different shifts.
#
# `beats` below are named bundles of actions. Their old clock labels are retained
# as stable data keys, but STORY_TRIGGERS decides when they run from player
# progress. The clock never dispatches a story beat anymore.
#
# Beat actions (see _run_beat):
#   ["call", type]                 - ring the corridor phone (room4,
#                                    operator_count). Care assignments come only
#                                    from the duty board; the old per-assignment
#                                    "care_<id>" calls were never triggered and
#                                    were removed with the 2026-09-14 audit.
#   ["spawn", who]                 - orderly | hostile | nurse | violent
#   ["anomaly", id]                - anomaly_manager.activate(id)
#   ["message", text, seconds]     - HUD line
#   ["incident", id]               - one of the handlers in _run_incident

# Selection has to outlive hud.gd's reload_current_scene() restart, and the
# project has no autoloads, so the choice lives on the class, not the instance.
static var selected_index := 0

const LEVELS: Array[Dictionary] = [
{
	"id": "night_1",
	"title": "ПАЛАТА 0",
	"brief": "Обычная ночь. Семь пациентов, журнал, доска назначений.\nСверяйте браслеты и доживите до 06:00.",
	"assignments": ["medication", "vitals", "pulse", "linen", "iv", "dressing", "identity"],
	"tasks": ["journal_checked", "assignment_board_read", "room4_call", "patient_count", "final_call",
		"care_medication", "care_vitals", "care_pulse", "care_linen", "care_iv", "care_dressing",
		"care_identity", "spill_cleanup", "exit_check", "elevator_check"],
	"required": 9,
	"props": [],
	"anomalies": ["extra_patient", "room6_television", "wrong_bucket", "elevator_minus_one",
		"reverse_clock", "extra_chair", "moving_wheelchair", "anatomy_poster", "wrong_reflection",
		"copied_footsteps", "mannequin", "wrong_door_label", "wrong_door", "long_corridor",
		"extra_window", "wrong_patient", "empty_bed", "false_note"],
	"beats": {
		"00:35": [["spawn", "orderly"], ["message", "В коридоре заскрипели колёса синего ведра.", 3.5]],
		"00:57": [["call", "room4"]],
		"01:57": [["call", "operator_count"]],
		"02:59": [["anomaly", "violent_patient"]],
		"04:49": [["spawn", "hostile"]]
	}
},
{
	"id": "night_2",
	"title": "ОБЕСТОЧЕНО",
	"brief": "Подстанция села. Отделение на аварийном питании, свет гаснет секциями.\nКомпрессор кислорода встал — Юдин дышит сам.",
	"assignments": ["oxygen", "vitals", "medication"],
	"tasks": ["journal_checked", "assignment_board_read", "final_call", "care_oxygen", "care_vitals",
		"care_medication", "obj_fuse_box", "obj_emergency_light", "elevator_check"],
	"required": 6,
	"props": ["interaction_fuse_box", "interaction_spare_fuses", "interaction_emergency_lamp",
		"interaction_oxygen_pillow"],
	"anomalies": ["elevator_minus_one", "reverse_clock", "copied_footsteps", "wrong_reflection",
		"long_corridor", "moving_wheelchair", "self_phone_call"],
	"beats": {
		"00:22": [["message", "Щиток западного крыла щёлкнул. Свет в палатах 1–3 погас.", 4.5],
			["incident", "blackout_west"]],
		"02:10": [["incident", "elevator_call"], ["message", "Лифт поехал сам. Индикатор показывает −1.", 4.0]],
		"03:30": [["spawn", "hostile"]],
		"04:20": [["incident", "blackout_all"],
			["message", "Генератор заглох. Остался только ваш фонарик.", 5.0]],
		"05:05": [["anomaly", "copied_footsteps"]]
	}
},
{
	"id": "night_3",
	"title": "КАРАНТИН",
	"brief": "Палата 6 закрыта плёночным пологом. Вход только в маске,\nна выходе — обработка рук. Мазок у Климовой к утру.",
	"assignments": ["quarantine_meds", "sputum", "linen"],
	"tasks": ["journal_checked", "assignment_board_read", "final_call", "care_quarantine_meds",
		"care_sputum", "care_linen", "obj_disinfect", "obj_quarantine_curtain", "patient_count"],
	"required": 6,
	"props": ["interaction_quarantine_curtain", "interaction_mask_box", "interaction_hand_sanitizer",
		"interaction_sample_tube"],
	"anomalies": ["extra_patient", "wrong_patient", "room6_television", "false_note",
		"wrong_door_label", "anatomy_poster", "mannequin"],
	"beats": {
		"00:20": [["message", "Полог на палате 6 запаян. Маски — в процедурной.", 4.0]],
		"01:05": [["incident", "curtain_torn"],
			["message", "Полог разорван изнутри. Кто-то вышел.", 4.5]],
		"02:40": [["anomaly", "extra_patient"],
			["message", "В палате 6 три силуэта. Коек по-прежнему две.", 4.5]],
		"03:20": [["call", "operator_count"]],
		"04:15": [["anomaly", "violent_patient"]]
	}
},
{
	"id": "night_4",
	"title": "КАТАЛКА",
	"brief": "Демина не переживёт эту ночь. Констатировать, оформить\nсвидетельство, упаковать и свезти вниз на лифте.",
	"assignments": ["pronounce", "shroud", "iv"],
	"tasks": ["journal_checked", "final_call", "care_pronounce", "care_shroud", "care_iv",
		"obj_death_certificate", "obj_gurney", "elevator_check"],
	"required": 6,
	"props": ["interaction_gurney", "interaction_body_bag", "interaction_death_certificate"],
	# No empty_bed here: that anomaly hides Demina, on whom this whole night's
	# pronounce/shroud work is performed, and the story already empties her bed.
	"anomalies": ["wrong_patient", "elevator_minus_one", "reverse_clock",
		"wrong_reflection", "false_note", "mannequin"],
	"beats": {
		"01:20": [["incident", "patient_dies"],
			["message", "Из палаты 5 — длинный ровный писк. Демина В. Р.", 5.0]],
		"03:20": [["incident", "body_missing"],
			["message", "Каталка в коридоре. Мешок расстёгнут и пуст.", 4.5]],
		"04:00": [["incident", "body_returned"],
			["message", "Демина снова в своей кровати. Одеяло подоткнуто.", 4.5]],
		"05:00": [["spawn", "nurse"]]
	}
},
{
	"id": "night_5",
	"title": "ПЕРЕЛИВАНИЕ",
	"brief": "Савельеву назначено переливание. Группа II(A).\nХолодильник в процедурной, этикетки сверять дважды.",
	"assignments": ["transfusion", "pulse", "dressing"],
	"tasks": ["journal_checked", "assignment_board_read", "final_call", "care_transfusion",
		"care_pulse", "care_dressing", "obj_blood_chart"],
	"required": 6,
	"props": ["interaction_blood_fridge", "interaction_blood_bag_first", "interaction_blood_bag_second",
		"interaction_blood_bag_third", "interaction_blood_chart"],
	"anomalies": ["wrong_patient", "player_name_journal", "false_note", "anatomy_poster",
		"wrong_reflection", "copied_footsteps", "room6_television"],
	"beats": {
		"00:30": [["message", "Холодильник с кровью в процедурной. Сверьте таблицу групп.", 4.0]],
		"01:30": [["incident", "labels_swapped"],
			["message", "Этикетки на пакетах перепутаны местами.", 4.5]],
		"03:00": [["incident", "all_labels_same"],
			["message", "На всех пакетах теперь одна группа. Ваша.", 5.0]],
		"04:20": [["spawn", "hostile"]],
		"05:10": [["anomaly", "player_name_journal"]]
	}
},
{
	"id": "night_6",
	"title": "ХОЛОД",
	"brief": "Котельная встала, за окном минус пять. Батареи ледяные.\nСтравить воздух, раздать одеяла, закрыть форточки.",
	"assignments": ["warm_blanket", "hot_tea", "vitals"],
	"tasks": ["journal_checked", "assignment_board_read", "final_call", "care_warm_blanket",
		"care_hot_tea", "care_vitals", "obj_radiator_valve", "obj_window_latch"],
	"required": 6,
	"props": ["interaction_radiator_key", "interaction_blanket_stack", "interaction_radiator_valve",
		"interaction_window_latch", "interaction_tea_kettle"],
	"anomalies": ["extra_window", "wrong_reflection", "long_corridor", "moving_wheelchair",
		"extra_chair", "copied_footsteps", "empty_bed"],
	"beats": {
		"00:25": [["message", "Батареи холодные. Ключ для стравливания — в служебной.", 4.0]],
		"00:50": [["incident", "window_opens"],
			["message", "Форточка в палате 3 открылась сама. Тянет снегом.", 4.5]],
		"02:20": [["incident", "cold_snap"],
			["message", "Изо рта идёт пар. В отделении минус.", 4.5]],
		"03:45": [["incident", "all_windows_open"],
			["message", "Все форточки распахнуты одновременно.", 4.5]],
		"05:10": [["anomaly", "violent_patient"]]
	}
},
{
	"id": "night_7",
	"title": "ПОБЕГ",
	"brief": "Кровать Морозова пуста, тапки стоят у пожарной двери.\nНайти пациента и вернуть в палату до пересменки.",
	"assignments": ["return_patient", "identity"],
	"tasks": ["journal_checked", "final_call", "patient_count", "care_return_patient", "care_identity",
		"obj_slippers", "obj_footprints", "obj_bed_note", "exit_check"],
	"required": 6,
	"props": ["interaction_hospital_slippers", "interaction_muddy_trail", "interaction_bed_note",
		"interaction_escaped_patient"],
	"anomalies": ["empty_bed", "extra_patient", "copied_footsteps", "long_corridor", "wrong_door",
		"wrong_reflection", "false_note"],
	"beats": {
		"00:30": [["incident", "patient_escapes"],
			["message", "Кровать 1 в палате 1 пуста. Одеяло откинуто.", 5.0]],
		"01:10": [["call", "operator_count"]],
		"01:40": [["incident", "reveal_trail"],
			["message", "По линолеуму тянутся мокрые следы к пожарной двери.", 4.5]],
		"03:10": [["incident", "figure_at_end"],
			["message", "В конце коридора кто-то стоит. Вы моргнули — никого.", 4.5]],
		"04:00": [["incident", "reveal_escapee"],
			["message", "На лестничной площадке сидит человек в больничном.", 5.0]],
		"05:15": [["spawn", "hostile"]]
	}
},
{
	"id": "night_8",
	"title": "КОМИССИЯ",
	"brief": "В 05:00 обход главной медсестры. Коридор должен быть чист,\nжурнал заполнен, пломбы целы. Она видит всё.",
	"assignments": ["identity", "medication"],
	"tasks": ["journal_checked", "assignment_board_read", "final_call", "care_identity", "care_medication",
		"obj_duty_journal", "obj_misplaced_chair", "obj_floor_dirt", "exit_check"],
	"required": 7,
	"props": ["interaction_duty_journal_form", "interaction_misplaced_chair", "interaction_floor_dirt"],
	"anomalies": ["extra_chair", "moving_wheelchair", "player_name_journal", "wrong_door_label",
		"anatomy_poster", "false_note", "wrong_reflection"],
	"beats": {
		"00:20": [["message", "Обход в 05:00. Уберите коридор и заполните журнал дежурства.", 4.5]],
		"01:00": [["incident", "things_return"],
			["message", "Стул снова стоит поперёк прохода. Вы его убирали.", 4.5]],
		"02:30": [["anomaly", "player_name_journal"],
			["message", "В журнале чужой почерк. Буквы ваши.", 4.5]],
		"04:10": [["incident", "things_return"]],
		"05:00": [["spawn", "nurse"]]
	}
},
{
	"id": "night_9",
	"title": "ДЫМ",
	"brief": "Из щитовой тянет гарью. Найти очаг, сбить огонь,\nвскрыть пожарный выход и доложить по телефону.",
	"assignments": ["oxygen", "pulse"],
	"tasks": ["journal_checked", "final_call", "care_oxygen", "care_pulse", "obj_extinguish",
		"obj_fire_alarm", "exit_check", "elevator_check"],
	"required": 6,
	# The oxygen pillow rides along from night 2: the smoke round prescribes it
	# for Юдин, and without the prop present that assignment cannot be finished.
	"props": ["interaction_fire_extinguisher", "interaction_smoke_source", "interaction_fire_alarm_panel",
		"interaction_oxygen_pillow"],
	"anomalies": ["long_corridor", "wrong_door", "copied_footsteps", "reverse_clock",
		"elevator_minus_one", "wrong_reflection", "self_phone_call"],
	"beats": {
		"01:15": [["message", "Пахнет горелой изоляцией. Тянет из щитовой.", 4.0]],
		"01:45": [["incident", "smoke_starts"],
			["message", "Дым пошёл по потолку коридора.", 4.5]],
		"03:00": [["incident", "alarm_sounds"],
			["message", "Сирена. Панель мигает: западное крыло.", 4.5]],
		"04:15": [["anomaly", "wrong_door"]],
		"04:40": [["incident", "smoke_clears"],
			["message", "Дым втянуло обратно в решётку. Гарью больше не пахнет.", 5.0]],
		"05:20": [["spawn", "hostile"]]
	}
},
{
	"id": "night_10",
	"title": "ОПЕРАЦИЯ",
	"brief": "В 04:00 экстренная операция. Прокипятить инструменты,\nвскрыть бикс, поднять лампу и подготовить Савельева.",
	"assignments": ["prep_surgery", "medication"],
	"tasks": ["journal_checked", "assignment_board_read", "final_call", "care_prep_surgery",
		"care_medication", "obj_sterile_bix", "obj_surgical_lamp", "elevator_check"],
	"required": 6,
	"props": ["interaction_sterile_bix", "interaction_surgical_lamp", "interaction_surgical_gown"],
	"anomalies": ["mannequin", "wrong_patient", "room6_television", "false_note",
		"anatomy_poster", "elevator_minus_one", "wrong_reflection"],
	"beats": {
		"00:30": [["message", "Операция в 04:00. Бикс и лампа — в процедурной.", 4.0]],
		"02:10": [["incident", "bix_used"],
			["message", "Бикс вскрыт до вас. Инструменты внутри в бурых разводах.", 5.0]],
		"03:30": [["incident", "surgeon_absent"],
			["message", "Лифт пришёл пустой. Хирурга нет.", 4.5]],
		"04:00": [["incident", "operation_starts"],
			["message", "В процедурной работают. Дверь приоткрыта, но внутри никого.", 5.5]],
		"04:50": [["anomaly", "mannequin"]],
		"05:20": [["spawn", "nurse"]]
	}
},
{
	"id": "night_11",
	"title": "ДВЕРЬ БЕЗ НОМЕРА",
	"brief": "Между палатами 3 и 4 появилась дверь, которой нет на плане.\nВ журнале за неё расписана ваша фамилия.",
	"assignments": ["identity", "vitals"],
	"tasks": ["journal_checked", "final_call", "patient_count", "care_identity", "care_vitals",
		"obj_zero_card", "obj_zero_door", "exit_check"],
	"required": 7,
	"props": ["interaction_zero_door", "interaction_zero_key", "interaction_zero_card"],
	"anomalies": ["room_zero", "player_name_journal", "wrong_door", "long_corridor", "extra_patient",
		"wrong_reflection", "copied_footsteps", "false_note", "empty_bed"],
	"beats": {
		"00:25": [["incident", "zero_door_appears"],
			["message", "В простенке между палатами 3 и 4 стоит дверь. Без номера.", 5.5]],
		"02:00": [["anomaly", "player_name_journal"],
			["message", "Журнал: палата 0, ваша фамилия, время поступления — сегодня.", 5.0]],
		"02:45": [["call", "operator_count"]],
		"03:40": [["incident", "patients_watch"],
			["message", "Все семеро лежат с открытыми глазами и смотрят на вас.", 5.0]],
		"04:30": [["anomaly", "room_zero"]],
		"05:00": [["spawn", "hostile"]],
		"05:25": [["spawn", "nurse"]]
	}
}
]

# Story progression is deliberately semantic rather than clock-driven. A night
# can now be completed at the player's pace: doing the whole round quickly still
# runs every prerequisite incident and reaches the ending.
const STORY_TRIGGERS := {
	"night_1": [
		{"id": "orderly_round", "all": ["journal_checked"], "beat": "00:35"},
		{"id": "room4_call", "all": ["assignment_board_read"], "beat": "00:57"},
		{"id": "operator_count", "count": 3, "beat": "01:57"},
		{"id": "violent_patient", "count": 5, "beat": "02:59"},
		{"id": "late_hostile", "count": 8, "beat": "04:49"},
	],
	"night_2": [
		{"id": "west_blackout", "start": true, "beat": "00:22"},
		{"id": "elevator_moves", "all": ["obj_fuse_box"], "beat": "02:10"},
		{"id": "hostile_after_oxygen", "all": ["care_oxygen"], "beat": "03:30"},
		{"id": "generator_stops", "all": ["care_vitals"], "beat": "04:20"},
		{"id": "copied_steps", "count": 5, "beat": "05:05"},
	],
	"night_3": [
		{"id": "quarantine_notice", "start": true, "beat": "00:20"},
		{"id": "curtain_torn", "all": ["obj_quarantine_curtain"], "beat": "01:05"},
		{"id": "extra_patient", "all": ["care_sputum"], "beat": "02:40"},
		{"id": "operator_count", "count": 3, "beat": "03:20"},
		{"id": "violent_patient", "count": 5, "beat": "04:15"},
	],
	"night_4": [
		{"id": "patient_dies", "start": true, "beat": "01:20"},
		{"id": "body_missing", "all": ["care_shroud"], "beat": "03:20"},
		{"id": "body_returned", "all": ["care_shroud", "obj_gurney"], "beat": "04:00"},
		{"id": "nurse_arrives", "all": ["care_iv"], "beat": "05:00"},
	],
	"night_5": [
		{"id": "transfusion_notice", "start": true, "beat": "00:30"},
		{"id": "labels_swapped", "all": ["obj_blood_chart"], "beat": "01:30"},
		{"id": "labels_become_same", "all": ["care_transfusion"], "beat": "03:00"},
		{"id": "hostile_after_pulse", "all": ["care_pulse"], "beat": "04:20"},
		{"id": "name_in_journal", "count": 5, "beat": "05:10"},
	],
	"night_6": [
		{"id": "cold_notice", "start": true, "beat": "00:25"},
		{"id": "window_opens", "all": ["obj_radiator_valve"], "beat": "00:50"},
		{"id": "cold_snap", "all": ["care_warm_blanket"], "beat": "02:20"},
		{"id": "all_windows_open", "all": ["care_hot_tea"], "beat": "03:45"},
		{"id": "violent_patient", "all": ["obj_window_latch"], "beat": "05:10"},
	],
	"night_7": [
		{"id": "patient_escapes", "start": true, "beat": "00:30"},
		{"id": "operator_count", "all": ["journal_checked"], "beat": "01:10"},
		{"id": "corridor_figure", "all": ["journal_checked"], "beat": "03:10"},
		{"id": "muddy_trail", "any": ["obj_slippers", "obj_bed_note"], "beat": "01:40"},
		{"id": "escaped_patient_found", "all": ["obj_footprints"], "beat": "04:00"},
		{"id": "hostile_after_return", "all": ["care_return_patient"], "beat": "05:15"},
	],
	"night_8": [
		{"id": "inspection_notice", "start": true, "beat": "00:20"},
		{"id": "chair_returns", "all": ["obj_misplaced_chair"], "beat": "01:00"},
		{"id": "name_in_journal", "all": ["obj_duty_journal"], "beat": "02:30"},
		{"id": "things_return_again", "all": ["obj_floor_dirt"], "beat": "04:10"},
		{"id": "nurse_arrives", "count": 6, "beat": "05:00"},
	],
	"night_9": [
		{"id": "smoke_notice", "start": true, "beat": "01:15"},
		{"id": "smoke_starts", "all": ["journal_checked"], "beat": "01:45"},
		# The siren follows the smoke by one more action; inspecting the panel is
		# what silences it, so the panel task cannot be the thing that starts it.
		{"id": "alarm_sounds", "all": ["journal_checked"], "count": 2, "beat": "03:00"},
		{"id": "wrong_door", "count": 3, "beat": "04:15"},
		{"id": "smoke_clears", "all": ["obj_extinguish"], "beat": "04:40"},
		{"id": "late_hostile", "count": 5, "beat": "05:20"},
	],
	"night_10": [
		{"id": "operation_notice", "start": true, "beat": "00:30"},
		# The damaged kit is discovered before it can be used. This keeps the
		# recovery interaction meaningful instead of marking a completed bix as
		# contaminated after the fact.
		{"id": "bix_was_used", "start": true, "beat": "02:10"},
		{"id": "surgeon_absent", "all": ["care_prep_surgery"], "beat": "03:30"},
		{"id": "operation_starts", "all": ["care_prep_surgery", "care_medication", "obj_sterile_bix", "obj_surgical_lamp"], "beat": "04:00"},
		{"id": "mannequin", "count": 5, "beat": "04:50"},
		{"id": "nurse_arrives", "count": 5, "beat": "05:20"},
	],
	"night_11": [
		{"id": "zero_door_appears", "start": true, "beat": "00:25"},
		{"id": "name_in_journal", "all": ["journal_checked"], "beat": "02:00"},
		{"id": "operator_count", "all": ["obj_zero_card"], "beat": "02:45"},
		{"id": "patients_watch", "all": ["care_identity"], "beat": "03:40"},
		{"id": "room_zero", "all": ["obj_zero_door"], "beat": "04:30"},
		{"id": "hostile", "count": 6, "beat": "05:00"},
		{"id": "nurse_arrives", "count": 7, "beat": "05:25"},
	],
}

const HIDDEN_STORY_PROPS := {
	"night_4": ["interaction_gurney"],
	"night_6": ["interaction_window_latch"],
	"night_7": ["interaction_muddy_trail", "interaction_bed_note", "interaction_escaped_patient"],
	"night_9": ["interaction_smoke_source"],
	"night_11": ["interaction_zero_door"],
}

# The numeric pass mark allows optional tasks, while these requirements prevent
# a player from bypassing the central action of a story night with side checks.
const ENDING_REQUIREMENTS := {
	"night_1": ["care_identity"],
	"night_2": ["care_medication", "obj_fuse_box"],
	"night_3": ["care_linen", "obj_disinfect"],
	"night_4": ["care_iv", "care_shroud", "obj_gurney"],
	"night_5": ["care_dressing", "obj_blood_chart"],
	"night_6": ["care_vitals", "obj_window_latch"],
	"night_7": ["care_return_patient", "care_identity"],
	"night_8": ["care_medication", "obj_duty_journal"],
	"night_9": ["care_pulse", "obj_extinguish"],
	"night_10": ["care_medication", "care_prep_surgery", "obj_surgical_lamp"],
	"night_11": ["care_vitals", "obj_zero_door"],
}

var fired: Dictionary = {}
var progression_started := false
var finishing := false
var evaluating := false

func _ready() -> void:
	add_to_group("level_manager")

static func level() -> Dictionary:
	return LEVELS[clampi(selected_index, 0, LEVELS.size() - 1)]

static func level_count() -> int:
	return LEVELS.size()

func reset() -> void:
	fired.clear()
	progression_started = false
	finishing = false
	evaluating = false

func start_progression() -> void:
	progression_started = true
	var state := get_tree().get_first_node_in_group("hospital_state")
	if state and not state.task_changed.is_connected(_on_task_changed):
		state.task_changed.connect(_on_task_changed)
	_evaluate_story_triggers()

func _on_task_changed(_summary: String) -> void:
	if progression_started:
		_evaluate_story_triggers()

func _process(_delta: float) -> void:
	# A last encounter can outlive the task that spawned it, and the shower can
	# still be flooded when the last task is done. Neither clears through a task
	# signal (spill_cleanup is not scored on every night), so while the handoff
	# waits on one of them it is re-checked here until it goes through.
	var state := get_tree().get_first_node_in_group("hospital_state")
	if not state or String(state.get_flag("handoff_waiting", "")).is_empty():
		return
	_try_finish_shift()

func _evaluate_story_triggers() -> void:
	if evaluating or finishing:
		return
	evaluating = true
	var state := get_tree().get_first_node_in_group("hospital_state")
	var level_id := String(level().get("id", ""))
	if state:
		for trigger in STORY_TRIGGERS.get(level_id, []):
			var trigger_id := String(trigger.get("id", ""))
			if trigger_id.is_empty() or fired.has(trigger_id):
				continue
			if not _trigger_condition_met(trigger, state):
				continue
			fired[trigger_id] = true
			_run_beat_group(String(trigger.get("beat", "")))
	evaluating = false
	_try_finish_shift()

func _trigger_condition_met(trigger: Dictionary, state: Node) -> bool:
	if bool(trigger.get("start", false)):
		return true
	if trigger.has("count") and state.task_count() < int(trigger.count):
		return false
	for task_id in trigger.get("all", []):
		if not state.tasks.get(String(task_id), false):
			return false
	var any_tasks: Array = trigger.get("any", [])
	if not any_tasks.is_empty():
		var matched := false
		for task_id in any_tasks:
			if state.tasks.get(String(task_id), false):
				matched = true
				break
		if not matched:
			return false
	return trigger.has("count") or trigger.has("all") or trigger.has("any")

func _run_beat_group(key: String) -> void:
	var beats: Dictionary = level().get("beats", {})
	if not beats.has(key):
		push_error("Unknown story beat %s for %s" % [key, level().get("id", "?")])
		return
	for beat in beats[key]:
		_run_beat(beat)

func completion_requirements_met(state: Node) -> bool:
	for task_id in ENDING_REQUIREMENTS.get(String(level().get("id", "")), []):
		if not state.tasks.get(String(task_id), false):
			return false
	return true

func _try_finish_shift() -> void:
	if not progression_started or finishing:
		return
	var state := get_tree().get_first_node_in_group("hospital_state")
	if not state or state.get_flag("ending_requested", false):
		return
	var required := int(level().get("required", 9))
	if state.task_count() < required or not completion_requirements_met(state):
		return
	if bool(state.get_flag("shower_flooded", false)):
		_wait_for_handoff(state, "flood")
		return
	# A task completion can also spawn the shift's final inspector/hostile. Do
	# not cut the encounter off with the dawn screen in the same signal callback.
	# The player must get a chance to resolve the active danger first.
	var clock := get_tree().get_first_node_in_group("time_manager")
	# Headless completion tests pause the clock and drive state transitions
	# synchronously; keep those deterministic. During a real active shift an
	# encounter must be resolved before the handoff can finish.
	if clock and clock.running and (not get_tree().get_nodes_in_group("hostile_orderlies").is_empty() \
		or not get_tree().get_nodes_in_group("violent_patients").is_empty()):
		state.set_flag("handoff_ready_pending_danger", true)
		_wait_for_handoff(state, "danger")
		return
	state.set_flag("handoff_waiting", "")
	state.set_flag("handoff_ready_pending_danger", false)
	finishing = true
	state.set_flag("shift_complete", true)
	var active_clock := get_tree().get_first_node_in_group("time_manager")
	if active_clock and active_clock.running:
		# In a real shift the final task prepares the handoff; the player must
		# consciously submit the journal at the post instead of being frozen by
		# the exact interaction that spawned the last threat.
		state.set_flag("handoff_ready", true)
		var hud := get_tree().get_first_node_in_group("hud")
		if hud:
			hud.set_objective(tr("Работа завершена. Сдайте смену на посту."))
			hud.show_message(tr("Все обязательные задачи выполнены. Сдайте смену на посту."), 5.0)
	else:
		# Deterministic headless completion path retains the old direct ending.
		state.complete_task("final_call")
		state.request_ending("dawn")

func _wait_for_handoff(state: Node, reason: String) -> void:
	if String(state.get_flag("handoff_waiting", "")) == reason:
		return
	state.set_flag("handoff_waiting", reason)
	# The objective line otherwise keeps claiming the shift is ending while it
	# is actually blocked.
	var director := get_tree().get_first_node_in_group("game_director")
	if director and director.has_method("refresh_objective"):
		director.refresh_objective()

func apply_prop_visibility(hospital: Node3D) -> void:
	# Every night's props ship in the same GLB. Anything tagged as a level prop
	# is hidden unless the selected night lists it, so night 4's gurney does not
	# stand in the corridor during night 2.
	var allowed: Array = level().get("props", [])
	var hidden: Array = HIDDEN_STORY_PROPS.get(String(level().get("id", "")), [])
	for node in hospital.get_tree().get_nodes_in_group("level_props"):
		if node is Node3D:
			var visible_now: bool = String(node.name) in allowed and not String(node.name) in hidden
			node.visible = visible_now
			_set_prop_active(node as Node3D, visible_now)

func _set_prop_active(node: Node3D, active: bool) -> void:
	# Hiding a Node3D does not disable physics, and main.gd auto-boxes any mesh
	# whose name trips _needs_collision (the zero door, the blood fridge). Left
	# alone those would stand as invisible obstacles on the other ten nights, so
	# every collider under the prop is switched with it.
	var layer := 1 if active else 0
	for descendant in _descendants(node):
		if descendant is Area3D and String(descendant.name) == "CareInteractionArea":
			(descendant as Area3D).collision_layer = layer
		elif descendant is StaticBody3D:
			(descendant as StaticBody3D).collision_layer = layer

func _descendants(node: Node) -> Array[Node]:
	var out: Array[Node] = []
	for child in node.get_children():
		out.append(child)
		out.append_array(_descendants(child))
	return out

func reveal_prop(prop_name: String) -> void:
	for node in get_tree().get_nodes_in_group("level_props"):
		if String(node.name) == prop_name and node is Node3D:
			(node as Node3D).visible = true
			_set_prop_active(node as Node3D, true)

func hide_prop(prop_name: String) -> void:
	for node in get_tree().get_nodes_in_group("level_props"):
		if String(node.name) == prop_name and node is Node3D:
			(node as Node3D).visible = false
			_set_prop_active(node as Node3D, false)

func on_reached_time(hour: int, minute: int) -> void:
	# Kept as a compatibility hook for old callers/tests. Story beats are
	# progress-triggered; advancing the ward clock must not dispatch them.
	_evaluate_story_triggers()

func _run_beat(beat: Array) -> void:
	if beat.is_empty():
		return
	var verb := String(beat[0])
	match verb:
		"call":
			var phone := get_tree().get_first_node_in_group("hospital_phone")
			if phone:
				phone.start_call(String(beat[1]))
		"anomaly":
			var anomalies := get_tree().get_first_node_in_group("anomaly_manager")
			if anomalies:
				anomalies.activate(String(beat[1]))
		"spawn":
			var manager := get_tree().get_first_node_in_group("anomaly_manager")
			if not manager:
				return
			match String(beat[1]):
				"orderly": manager.spawn_normal_orderly()
				"hostile": manager.spawn_hostile_orderly()
				"nurse": manager.request_head_nurse_inspector("inspection")
				"violent": manager.activate("violent_patient")
		"message":
			var hud := get_tree().get_first_node_in_group("hud")
			if hud:
				# Every beat line lives in the LEVELS const, where tr() cannot be
				# called, so the night's own text is translated here on its way
				# to the player.
				hud.show_message(tr(String(beat[1])), float(beat[2]) if beat.size() > 2 else 4.0)
		"incident":
			_run_incident(String(beat[1]))

func _run_incident(id: String) -> void:
	match id:
		# Wards 1-3 sit at x -17.5, -12.5 and -7.5, so the cut has to fall east
		# of -7.5 for the HUD line "свет в палатах 1-3 погас" to be true; at 9.0
		# ward 3 stayed lit and contradicted the message.
		"blackout_west": _set_lights(-1.0, 6.0)
		"blackout_all": _set_lights(-1.0, 999.0)
		"lights_restore": _set_lights(1.45, 999.0)
		"elevator_call":
			var anomalies := get_tree().get_first_node_in_group("anomaly_manager")
			if anomalies:
				anomalies.activate("elevator_minus_one")
		"curtain_torn": hide_prop("interaction_quarantine_curtain")
		"patient_dies":
			# She stays lying in the bed. care_pronounce (01:35) and care_shroud
			# (02:20) are both performed ON her, so removing the body here would
			# leave the player doing those over an empty mattress. She only goes
			# missing at body_missing, which is the point of that beat.
			reveal_prop("interaction_gurney")
			_state_count(6)
		"body_missing":
			hide_prop("interaction_body_bag")
			_set_patient_visible("ward_5_bed_1_patient_v3", false)
		"body_returned":
			_set_patient_visible("ward_5_bed_1_patient_v3", true)
			_state_count(7)
		"labels_swapped":
			var swap_state := get_tree().get_first_node_in_group("hospital_state")
			if swap_state:
				swap_state.set_flag("blood_labels_unreliable", true)
				swap_state.set_flag("blood_label_stage", 1)
		"all_labels_same":
			var same_state := get_tree().get_first_node_in_group("hospital_state")
			if same_state:
				same_state.set_flag("blood_labels_unreliable", true)
				same_state.set_flag("blood_label_stage", 2)
		"window_opens", "all_windows_open": reveal_prop("interaction_window_latch")
		"cold_snap": _set_fog(0.019)
		"patient_escapes":
			_set_patient_visible("ward_1_bed_1_patient_v3", false)
			reveal_prop("interaction_bed_note")
			_state_count(6)
		"reveal_trail": reveal_prop("interaction_muddy_trail")
		"figure_at_end":
			var manager := get_tree().get_first_node_in_group("anomaly_manager")
			if manager:
				manager.activate("wrong_reflection")
		"reveal_escapee": reveal_prop("interaction_escaped_patient")
		"things_return": reveal_prop("interaction_misplaced_chair")
		"smoke_starts":
			reveal_prop("interaction_smoke_source")
			_set_fog(0.055)
		"alarm_sounds":
			var alarm_state := get_tree().get_first_node_in_group("hospital_state")
			if alarm_state:
				alarm_state.set_flag("fire_alarm_ringing", true)
			var audio := get_tree().get_first_node_in_group("audio_manager")
			if audio and audio.has_method("play_anomaly_sting"):
				audio.play_anomaly_sting("пожарная_сирена")
		"smoke_clears": _set_fog(0.006)
		"bix_used", "surgeon_absent", "operation_starts":
			var operation_state := get_tree().get_first_node_in_group("hospital_state")
			if operation_state:
				operation_state.set_flag(id, true)
			if id == "operation_starts":
				# The procedure scene owns the door; release only its story lock so
				# unrelated locked doors keep their original reasons.
				var hospital := get_tree().get_first_node_in_group("hospital_model")
				if hospital:
					var procedure_door := hospital.find_child("pivot_hospital_door_N_4", true, false)
					if procedure_door and procedure_door.has_method("interact"):
						procedure_door.set("locked", false)
		"zero_door_appears": reveal_prop("interaction_zero_door")
		"patients_watch": _set_fog(0.013)

func _set_lights(energy: float, radius: float) -> void:
	# energy < 0 switches the fixtures off; radius limits the blackout to the
	# west wing (|x| beyond the cut stays lit) so a partial failure reads.
	for light in get_tree().get_nodes_in_group("hospital_lights"):
		if not light is Light3D:
			continue
		var node := light as Light3D
		if radius < 900.0 and node.global_position.x > -radius:
			continue
		node.light_energy = maxf(energy, 0.0)
		node.visible = energy > 0.0

func _set_fog(density: float) -> void:
	var environment_holder := get_tree().get_first_node_in_group("world_environment")
	if environment_holder and environment_holder is WorldEnvironment:
		var environment: Environment = (environment_holder as WorldEnvironment).environment
		if environment:
			environment.fog_density = density

func _set_patient_visible(object_name: String, value: bool) -> void:
	var hospital := get_tree().get_first_node_in_group("hospital_model")
	if not hospital:
		return
	var node := hospital.find_child(object_name, true, false)
	if node is Node3D:
		(node as Node3D).visible = value
		var state := get_tree().get_first_node_in_group("hospital_state")
		if state and state.has_method("record_patient_presence"):
			var patient_id := ""
			if "ward_1_bed_1" in object_name: patient_id = "morozov"
			elif "ward_5_bed_1" in object_name: patient_id = "demina"
			elif "ward_6_bed_1" in object_name: patient_id = "yudin"
			elif "ward_6_bed_2" in object_name: patient_id = "klimova"
			if not patient_id.is_empty():
				state.record_patient_presence(patient_id, value, "story_event")
		# Same trap as the props: visibility alone leaves the patient's
		# CareInteractionArea live, so the player could walk up to an empty bed
		# and finish that patient's assignment on an invisible body - which on
		# night 7 would let them "return" Morozov without ever finding him.
		_set_prop_active(node as Node3D, value)

func _state_count(value: int) -> void:
	var state := get_tree().get_first_node_in_group("hospital_state")
	if state:
		state.set_patient_count(value)
