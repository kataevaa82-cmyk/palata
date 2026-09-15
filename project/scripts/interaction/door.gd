extends Node3D

@export var open_angle := 88.0
@export var open_time := 0.75
@export var locked := false

var opened := false
var closed_rotation := Vector3.ZERO
var configured := false
var tween: Tween

func setup_from_import() -> void:
	if configured:
		return
	configured = true
	closed_rotation = rotation
	if has_meta("open_angle_degrees"):
		open_angle = float(get_meta("open_angle_degrees"))
	if has_meta("locked"):
		locked = bool(get_meta("locked"))
	add_to_group("interactive_doors")

func interaction_text() -> String:
	if locked:
		return tr("[E] Заперто")
	return tr("[E] Закрыть дверь") if opened else tr("[E] Открыть дверь")

func interact(_actor: Node) -> void:
	if locked:
		# A story scene may lock a door while it is still open. Allow the
		# transition to close safely; only opening remains blocked.
		if opened:
			opened = false
			if tween and tween.is_running():
				tween.kill()
			tween = create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
			tween.tween_property(self, "rotation", closed_rotation, open_time)
			return
		var state := get_tree().get_first_node_in_group("hospital_state")
		if state:
			state.record_observation("locked_door", name)
		return
	opened = not opened
	if opened and has_meta("room_zero"):
		var state := get_tree().get_first_node_in_group("hospital_state")
		if state:
			state.request_ending("room_zero")
	if tween and tween.is_running():
		tween.kill()
	tween = create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	var target := closed_rotation
	if opened:
		target.y += deg_to_rad(open_angle)
	tween.tween_property(self, "rotation", target, open_time)

func force_close() -> void:
	if opened:
		interact(null)
