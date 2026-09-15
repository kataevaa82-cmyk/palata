extends Node

signal patient_count_changed(count: int)
signal observation_recorded(kind: String, detail: String)
signal ending_requested(ending_id: String)
signal task_changed(summary: String)

var patient_count := 7
var flags: Dictionary = {}
var observations: Array[Dictionary] = []
var patient_outcomes: Dictionary = {}
var patient_presence: Dictionary = {}
var shift_started := false
var tasks: Dictionary = {}

# Superset of every task any of the eleven nights can hand out. Which of them
# actually count is per-night: reset_shift() seeds `tasks` from the selected
# level's own list, so night 4 is never graded against night 1's linen round.
const TASK_NAMES := {
	"journal_checked": "journal", "assignment_board_read": "board",
	"room4_call": "room4", "patient_count": "count", "final_call": "final",
	"care_medication": "medication", "care_vitals": "vitals", "care_pulse": "pulse",
	"care_linen": "linen", "care_iv": "iv", "care_dressing": "dressing", "care_identity": "identity",
	"care_oxygen": "oxygen", "care_quarantine_meds": "quarantine", "care_sputum": "sputum",
	"care_pronounce": "pronounce", "care_shroud": "shroud", "care_transfusion": "transfusion",
	"care_warm_blanket": "blanket", "care_hot_tea": "tea", "care_return_patient": "return",
	"care_prep_surgery": "surgery",
	"spill_cleanup": "spill", "exit_check": "exit", "elevator_check": "elevator",
	"obj_fuse_box": "fuses", "obj_emergency_light": "lantern", "obj_disinfect": "disinfect",
	"obj_quarantine_curtain": "curtain", "obj_death_certificate": "certificate", "obj_gurney": "gurney",
	"obj_blood_chart": "chart", "obj_radiator_valve": "radiator", "obj_window_latch": "window",
	"obj_slippers": "slippers", "obj_footprints": "footprints", "obj_bed_note": "note",
	"obj_duty_journal": "logbook", "obj_misplaced_chair": "chair", "obj_floor_dirt": "dirt",
	"obj_extinguish": "extinguish", "obj_fire_alarm": "alarm", "obj_sterile_bix": "bix",
	"obj_surgical_lamp": "lamp", "obj_zero_card": "card", "obj_zero_door": "door"
}

func _ready() -> void:
	add_to_group("hospital_state")

func set_patient_count(value: int) -> void:
	patient_count = value
	patient_count_changed.emit(patient_count)

func set_flag(key: String, value: Variant = true) -> void:
	flags[key] = value

func get_flag(key: String, fallback: Variant = false) -> Variant:
	return flags.get(key, fallback)

func record_observation(kind: String, detail: String = "") -> void:
	observations.append({"kind": kind, "detail": detail, "time": Time.get_ticks_msec()})
	observation_recorded.emit(kind, detail)

func complete_task(id: String) -> void:
	# Tasks outside the active night are silently ignored rather than inflating
	# its denominator - the optional elevator/exit checks exist on every map.
	if not tasks.has(id) or tasks.get(id, false):
		return
	tasks[id] = true
	task_changed.emit(task_summary())

func task_count() -> int:
	var count := 0
	for value in tasks.values():
		if value:
			count += 1
	return count

func task_total() -> int:
	return tasks.size()

func task_summary() -> String:
	return "%d/%d" % [task_count(), task_total()]

func reset_shift() -> void:
	patient_count = 7
	flags.clear()
	observations.clear()
	patient_outcomes.clear()
	patient_presence.clear()
	tasks.clear()
	var level: Dictionary = LevelManager.level()
	var ids: Array = level.get("tasks", [])
	for id in ids:
		if TASK_NAMES.has(id):
			tasks[id] = false
	shift_started = true

func record_patient_outcome(patient_id: String, outcome: String, detail := "") -> void:
	patient_outcomes[patient_id] = {"outcome": outcome, "detail": detail, "time": Time.get_ticks_msec()}
	record_observation("patient_outcome", "%s:%s" % [patient_id, outcome])

func patient_outcome(patient_id: String) -> Dictionary:
	return patient_outcomes.get(patient_id, {})

func record_patient_presence(patient_id: String, present: bool, source := "observation") -> void:
	patient_presence[patient_id] = {"present": present, "source": source, "time": Time.get_ticks_msec()}

func observed_patient_count() -> int:
	var count := 0
	for value in patient_presence.values():
		if bool(value.get("present", false)):
			count += 1
	return count

func request_ending(id: String) -> void:
	if get_flag("ending_requested", false):
		return
	set_flag("ending_requested", true)
	ending_requested.emit(id)
