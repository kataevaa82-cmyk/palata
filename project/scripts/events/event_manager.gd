extends Node

enum Category {
	NORMAL_EVENT,
	FALSE_ALARM,
	MINOR_ANOMALY,
	SIGNAL_ANOMALY,
	PATIENT_ANOMALY,
	ENVIRONMENT_ANOMALY,
	SPATIAL_ANOMALY,
	DANGEROUS_ANOMALY
}

var events_shown := 0
var max_events_per_run := 9
var rng := RandomNumberGenerator.new()
var running := false
var next_event_task_count := 2
var idle_seconds := 0.0
var event_cooldown := 0.0

func _ready() -> void:
	add_to_group("event_manager")
	rng.randomize()

func start_events() -> void:
	running = true
	events_shown = 0
	next_event_task_count = 2
	idle_seconds = 0.0
	event_cooldown = 0.0
	var state := get_tree().get_first_node_in_group("hospital_state")
	if state and not state.task_changed.is_connected(_on_task_changed):
		state.task_changed.connect(_on_task_changed)

func stop_events() -> void:
	running = false
	idle_seconds = 0.0

func _process(delta: float) -> void:
	if not running:
		return
	event_cooldown = maxf(event_cooldown - delta, 0.0)
	idle_seconds += delta
	# Task driven beats remain the primary pacing. This fallback only prevents
	# an exploratory player from getting an unlimited silent corridor.
	if idle_seconds < 60.0 or event_cooldown > 0.0 or events_shown >= max_events_per_run:
		return
	var danger_active := not get_tree().get_nodes_in_group("violent_patients").is_empty() \
		or not get_tree().get_nodes_in_group("hostile_orderlies").is_empty()
	if danger_active:
		return # keep the opportunity; try again after the encounter leaves
	_trigger_weighted_event()
	event_cooldown = 20.0
	idle_seconds = 0.0

func _on_task_changed(_summary: String) -> void:
	idle_seconds = 0.0
	if not running or events_shown >= max_events_per_run:
		return
	var state := get_tree().get_first_node_in_group("hospital_state")
	if not state or state.task_count() < next_event_task_count:
		return
	next_event_task_count += 2
	var danger_active := not get_tree().get_nodes_in_group("violent_patients").is_empty() or not get_tree().get_nodes_in_group("hostile_orderlies").is_empty()
	if danger_active:
		return
	_trigger_weighted_event()

func _trigger_weighted_event() -> void:
	var anomaly_manager := get_tree().get_first_node_in_group("anomaly_manager")
	var state := get_tree().get_first_node_in_group("hospital_state")
	if not state or not anomaly_manager:
		return
	var required := maxi(1, int(LevelManager.level().get("required", 9)))
	var progress: float = float(state.task_count()) / float(required)
	var phase := "DOUBT"
	if progress >= 0.85:
		phase = "SILENCE"
	elif progress >= 0.55:
		phase = "PROVOCATION"
	elif progress >= 0.25:
		phase = "ESCALATION"
	var roll := rng.randf()
	if phase == "DOUBT" and roll < 0.62:
		_trigger_normal_event()
		return
	if phase == "SILENCE" and roll < 0.80:
		return
	var pool: Array[String] = anomaly_manager.pool_for_phase(phase)
	# Each night draws only from its own shortlist, so the random background
	# events stay on that night's theme instead of every anomaly appearing
	# everywhere. Falling back to the full pool keeps an empty list harmless.
	var allowed: Array = LevelManager.level().get("anomalies", [])
	if not allowed.is_empty():
		var filtered: Array[String] = []
		for id in pool:
			if id in allowed:
				filtered.append(id)
		if not filtered.is_empty():
			pool = filtered
	if pool.is_empty():
		return
	var chosen := pool[rng.randi_range(0, pool.size() - 1)]
	if anomaly_manager.activate(chosen):
		events_shown += 1

func _trigger_normal_event() -> void:
	var state := get_tree().get_first_node_in_group("hospital_state")
	if state:
		state.record_observation("normal_event", [tr("кашель пациента"), tr("щелчок реле"), tr("колёса тележки"), tr("шум воды")].pick_random())
