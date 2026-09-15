extends Node3D

const OPERATOR_RETRY_SECONDS := 45.0

var ringing := false
var ring_count := 0
var call_type := ""
var ring_timer: Timer
var call_queue: Array[String] = []

func setup_from_import() -> void:
	add_to_group("hospital_phone")
	ring_timer = Timer.new()
	ring_timer.wait_time = 2.4
	ring_timer.timeout.connect(_on_ring)
	add_child(ring_timer)

func interaction_text() -> String:
	return tr("[E] Ответить на звонок") if ringing else tr("[E] Телефон")

func start_call(type: String) -> void:
	if ringing:
		if type != call_type and not type in call_queue:
			call_queue.append(type)
		return
	call_type = type
	ring_count = 0
	ringing = true
	ring_timer.start()
	_on_ring()

func _on_ring() -> void:
	if not ringing:
		return
	ring_count += 1
	var audio := get_tree().get_first_node_in_group("audio_manager")
	if audio:
		audio.play_phone_ring()
	var state := get_tree().get_first_node_in_group("hospital_state")
	if state:
		state.record_observation("phone_ring", "%s:%d" % [call_type, ring_count])

func interact(_actor: Node) -> void:
	var hud := get_tree().get_first_node_in_group("hud")
	if not ringing:
		if hud:
			hud.show_message(tr("Старая линия. Гудка нет."), 2.0)
		return
	if call_type == "room4":
		var room_state := get_tree().get_first_node_in_group("hospital_state")
		if room_state:
			room_state.complete_task("room4_call")
			room_state.set_flag("room4_call_answered_after_rings", ring_count)
	if call_type == "operator_count":
		ring_timer.stop()
		if hud:
			hud.begin_count_question(self)
		return
	if call_type.begins_with("care_"):
		var assignment_id := call_type.trim_prefix("care_")
		_stop_call()
		var care_manager := get_tree().get_first_node_in_group("care_manager")
		if care_manager:
			care_manager.accept_phone_assignment(assignment_id)
		return
	if call_type == "final":
		var final_state := get_tree().get_first_node_in_group("hospital_state")
		if final_state:
			final_state.complete_task("final_call")
			final_state.set_flag("final_call_answered", true)
		if hud:
			hud.show_message(tr("Дежурство окончено. Можете уходить."), 4.5)
	elif call_type == "self":
		if hud:
			hud.show_message(tr("На линии слышен ваш собственный голос: «Не отвечай». "), 3.5)
	else:
		if hud:
			hud.show_message(tr("В трубке слышно дыхание. Затем линия обрывается."), 3.0)
	_stop_call()

func answer_count(value: int) -> void:
	var state := get_tree().get_first_node_in_group("hospital_state")
	var hud := get_tree().get_first_node_in_group("hud")
	if not state:
		_stop_call()
		return
	if value == state.patient_count:
		if hud:
			hud.show_message(tr("Оператор молча отключился."), 2.5)
		state.record_observation("correct_patient_count", str(value))
		state.complete_task("patient_count")
	else:
		if hud:
			hud.show_message(tr("«Тогда один лишний». Линия оборвалась."), 3.5)
		var anomalies := get_tree().get_first_node_in_group("anomaly_manager")
		if anomalies:
			anomalies.activate("extra_patient")
		_schedule_operator_retry()
	_stop_call()

func _schedule_operator_retry() -> void:
	# The count call is story-triggered exactly once, and on nights with no spare
	# tasks (night 11) the patient count is mandatory. A single wrong answer must
	# not silently make the shift unfinishable, so the operator rings back.
	var state := get_tree().get_first_node_in_group("hospital_state")
	if not state or not state.tasks.has("patient_count"):
		return
	# Paused with the game: the retry is measured in play time, not menu time.
	get_tree().create_timer(OPERATOR_RETRY_SECONDS, false).timeout.connect(_retry_operator_call)

func _retry_operator_call() -> void:
	if not is_inside_tree():
		return
	var state := get_tree().get_first_node_in_group("hospital_state")
	if not state or bool(state.get_flag("ending_requested", false)) or bool(state.tasks.get("patient_count", true)):
		return
	start_call("operator_count")

func _stop_call() -> void:
	ringing = false
	call_type = ""
	if ring_timer:
		ring_timer.stop()
	if not call_queue.is_empty():
		var next_call: String = call_queue.pop_front()
		call_deferred("start_call", next_call)
