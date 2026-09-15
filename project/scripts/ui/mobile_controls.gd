extends CanvasLayer

const JOYSTICK_RADIUS := 88.0
const KNOB_RADIUS := 38.0
const LOOK_SENSITIVITY := 0.0042

# Below this the thumb is resting, not steering: without it the 2-3 px of drift
# every thumb has walks the player slowly down the corridor while they look
# around. Above it the stick is re-normalised so the full speed range is still
# reachable, and squared so small corrections stay small.
const STICK_DEAD_ZONE := 0.16
# A touch on the look side that neither travels far nor lasts long is a tap, and
# a tap means "use what I am looking at" - on a phone that is the difference
# between a game you can play with one thumb and one you cannot.
const TAP_MAX_TRAVEL := 18.0
const TAP_MAX_MSEC := 350

var mobile_enabled := false
var movement_vector := Vector2.ZERO
var move_touch := -1
var look_touch := -1
var joystick_origin := Vector2.ZERO
var look_start_position := Vector2.ZERO
var look_start_msec := 0
var look_travelled := 0.0

var root_control: Control
var joystick_base: Panel
var joystick_knob: Panel
var interact_button: Button
var flashlight_button: Button
var pause_button: Button
var assignment_button: Button
var answer_buttons: Array[Button] = []


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	layer = 30
	add_to_group("mobile_controls")
	_build_interface()
	var platform := get_tree().get_first_node_in_group("yandex_sdk")
	if platform:
		mobile_enabled = platform.is_mobile_device()
		platform.device_type_detected.connect(_on_device_type_detected)
	else:
		mobile_enabled = DisplayServer.is_touchscreen_available() or OS.has_feature("mobile")
	_refresh_visibility()


func _build_interface() -> void:
	root_control = Control.new()
	root_control.name = "TouchInterface"
	root_control.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root_control.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root_control)

	joystick_base = _make_circle_panel(Color(0.12, 0.16, 0.14, 0.48), JOYSTICK_RADIUS)
	joystick_base.name = "MoveStickBase"
	joystick_base.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root_control.add_child(joystick_base)
	joystick_knob = _make_circle_panel(Color(0.62, 0.70, 0.63, 0.68), KNOB_RADIUS)
	joystick_knob.name = "MoveStickKnob"
	joystick_knob.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root_control.add_child(joystick_knob)

	# The Russian text is the msgid, and Control re-translates itself whenever the
	# locale changes. Baking tr() in here instead meant that a scene built while
	# the game was in English stored "ACTION", which then matched no msgid and
	# left the button stuck in English after switching back to Russian.
	interact_button = _make_action_button("ДЕЙСТВИЕ", Vector2(196.0, 88.0))
	interact_button.name = "InteractButton"
	interact_button.pressed.connect(_mobile_interact)
	root_control.add_child(interact_button)

	flashlight_button = _make_action_button("ФОНАРИК", Vector2(170.0, 76.0))
	flashlight_button.name = "FlashlightButton"
	flashlight_button.pressed.connect(_mobile_flashlight)
	root_control.add_child(flashlight_button)

	assignment_button = _make_action_button("ПОРУЧЕНИЕ", Vector2(196.0, 64.0))
	assignment_button.name = "AssignmentButton"
	assignment_button.pressed.connect(_mobile_cycle_assignment)
	root_control.add_child(assignment_button)

	pause_button = _make_action_button("II", Vector2(68.0, 64.0))
	pause_button.name = "PauseButton"
	pause_button.pressed.connect(_mobile_pause)
	root_control.add_child(pause_button)

	for answer in [6, 7, 8]:
		var button := _make_action_button(str(answer), Vector2(112.0, 82.0))
		button.name = "Answer%d" % answer
		button.pressed.connect(_mobile_answer.bind(answer))
		button.visible = false
		answer_buttons.append(button)
		root_control.add_child(button)

	get_viewport().size_changed.connect(_layout_controls)
	_layout_controls()


func _make_circle_panel(color: Color, radius: float) -> Panel:
	var panel := Panel.new()
	panel.size = Vector2.ONE * radius * 2.0
	var style := StyleBoxFlat.new()
	style.bg_color = color
	style.border_color = Color(0.72, 0.78, 0.70, color.a + 0.1)
	style.set_border_width_all(2)
	style.set_corner_radius_all(int(radius))
	panel.add_theme_stylebox_override("panel", style)
	return panel


func _make_action_button(text_value: String, button_size: Vector2) -> Button:
	var button := Button.new()
	button.text = text_value
	button.size = button_size
	button.focus_mode = Control.FOCUS_NONE
	button.add_theme_font_size_override("font_size", 22)
	for state in ["normal", "hover", "pressed"]:
		var style := StyleBoxFlat.new()
		style.bg_color = Color(0.10, 0.14, 0.12, 0.70 if state != "pressed" else 0.92)
		style.border_color = Color(0.62, 0.70, 0.63, 0.72)
		style.set_border_width_all(2)
		style.set_corner_radius_all(16)
		button.add_theme_stylebox_override(state, style)
	return button


func _layout_controls() -> void:
	if not root_control:
		return
	var viewport_size := get_viewport().get_visible_rect().size
	joystick_origin = Vector2(145.0, viewport_size.y - 145.0)
	_set_stick_visual(joystick_origin, Vector2.ZERO)
	interact_button.position = Vector2(viewport_size.x - 222.0, viewport_size.y - 190.0)
	flashlight_button.position = Vector2(viewport_size.x - 410.0, viewport_size.y - 112.0)
	assignment_button.position = Vector2(viewport_size.x - 222.0, viewport_size.y - 268.0)
	pause_button.position = Vector2(viewport_size.x - 86.0, 18.0)
	var answer_start := viewport_size.x * 0.5 - 176.0
	for index in answer_buttons.size():
		answer_buttons[index].position = Vector2(answer_start + index * 120.0, viewport_size.y * 0.5 + 58.0)


func _input(event: InputEvent) -> void:
	if not mobile_enabled or not _gameplay_controls_visible():
		return
	if event is InputEventScreenTouch:
		var touch := event as InputEventScreenTouch
		if touch.pressed:
			if _point_on_button(touch.position):
				return
			if touch.position.x < get_viewport().get_visible_rect().size.x * 0.48 and move_touch == -1:
				move_touch = touch.index
				joystick_origin = touch.position
				_update_stick(touch.position)
			elif look_touch == -1:
				look_touch = touch.index
				look_start_position = touch.position
				look_start_msec = Time.get_ticks_msec()
				look_travelled = 0.0
		else:
			if touch.index == move_touch:
				_release_move_touch()
			elif touch.index == look_touch:
				# A short, still touch on the look side is a tap: use whatever is
				# under the crosshair. A cancelled touch (the browser or the OS
				# taking the gesture) is not a tap and must not act.
				var held := Time.get_ticks_msec() - look_start_msec
				if not touch.canceled and look_travelled <= TAP_MAX_TRAVEL and held <= TAP_MAX_MSEC:
					_mobile_interact()
				look_touch = -1
	elif event is InputEventScreenDrag:
		var drag := event as InputEventScreenDrag
		if drag.index == move_touch:
			_update_stick(drag.position)
		elif drag.index == look_touch:
			look_travelled += drag.relative.length()
			var player := get_tree().get_first_node_in_group("player")
			if player and player.has_method("apply_touch_look_delta"):
				player.apply_touch_look_delta(drag.relative, LOOK_SENSITIVITY)


func _release_move_touch() -> void:
	move_touch = -1
	movement_vector = Vector2.ZERO
	joystick_origin = Vector2(145.0, get_viewport().get_visible_rect().size.y - 145.0)
	_set_stick_visual(joystick_origin, Vector2.ZERO)


func _update_stick(position: Vector2) -> void:
	var offset := position - joystick_origin
	if offset.length() > JOYSTICK_RADIUS:
		offset = offset.normalized() * JOYSTICK_RADIUS
	var raw := offset / JOYSTICK_RADIUS
	var magnitude := raw.length()
	if magnitude <= STICK_DEAD_ZONE:
		movement_vector = Vector2.ZERO
	else:
		# Re-normalised past the dead zone so full tilt still means full speed,
		# then eased so the first half of the throw is fine control.
		var scaled := (magnitude - STICK_DEAD_ZONE) / (1.0 - STICK_DEAD_ZONE)
		movement_vector = raw.normalized() * (scaled * scaled * 0.35 + scaled * 0.65)
	_set_stick_visual(joystick_origin, offset)


func _set_stick_visual(origin: Vector2, offset: Vector2) -> void:
	if joystick_base:
		joystick_base.position = origin - Vector2.ONE * JOYSTICK_RADIUS
	if joystick_knob:
		joystick_knob.position = origin + offset - Vector2.ONE * KNOB_RADIUS


func _process(_delta: float) -> void:
	_refresh_visibility()


func _refresh_visibility() -> void:
	if not root_control:
		return
	root_control.visible = mobile_enabled
	var show_gameplay := mobile_enabled and _gameplay_controls_visible()
	joystick_base.visible = show_gameplay
	joystick_knob.visible = show_gameplay
	interact_button.visible = show_gameplay
	flashlight_button.visible = show_gameplay
	assignment_button.visible = show_gameplay
	var care := get_tree().get_first_node_in_group("care_manager")
	assignment_button.disabled = not care or care.assignment_queue.is_empty() or care.active_assignment.is_empty() or care.stage == "return"
	pause_button.visible = mobile_enabled and _shift_has_started() and not _ending_visible()
	var show_answers := mobile_enabled and _count_question_visible()
	for button in answer_buttons:
		button.visible = show_answers
	if show_gameplay:
		_refresh_interact_hint()
	elif movement_vector != Vector2.ZERO or move_touch != -1 or look_touch != -1:
		# A panel opened mid-stride: drop the fingers, or the player keeps
		# walking behind the pause menu.
		_release_move_touch()
		look_touch = -1


func _refresh_interact_hint() -> void:
	# Mirrors the prompt the player's raycast already fills in every physics
	# frame - deliberately NOT a second raycast of our own. Dim means pressing
	# does nothing, so the button stops being a guess.
	var hud := get_tree().get_first_node_in_group("hud")
	var has_target: bool = hud and not String(hud.prompt.text).is_empty()
	interact_button.modulate = Color(1.0, 1.0, 1.0, 1.0) if has_target else Color(1.0, 1.0, 1.0, 0.45)


func _gameplay_controls_visible() -> bool:
	var hud := get_tree().get_first_node_in_group("hud")
	return hud and hud.has_method("mobile_gameplay_controls_visible") and hud.mobile_gameplay_controls_visible()


func _shift_has_started() -> bool:
	var state := get_tree().get_first_node_in_group("hospital_state")
	return state and bool(state.shift_started)


func _ending_visible() -> bool:
	var hud := get_tree().get_first_node_in_group("hud")
	return hud and bool(hud.ending_panel.visible)


func _count_question_visible() -> bool:
	var hud := get_tree().get_first_node_in_group("hud")
	return hud and bool(hud.count_panel.visible)


func _point_on_button(point: Vector2) -> bool:
	for button in [interact_button, flashlight_button, pause_button, assignment_button]:
		if button and button.visible and button.get_global_rect().has_point(point):
			return true
	for button in answer_buttons:
		if button.visible and button.get_global_rect().has_point(point):
			return true
	return false


func _mobile_interact() -> void:
	var player := get_tree().get_first_node_in_group("player")
	if player and player.has_method("mobile_interact"):
		player.mobile_interact()


func _mobile_flashlight() -> void:
	var player := get_tree().get_first_node_in_group("player")
	if player and player.has_method("mobile_toggle_flashlight"):
		player.mobile_toggle_flashlight()


func _mobile_pause() -> void:
	var hud := get_tree().get_first_node_in_group("hud")
	if hud and hud.has_method("toggle_pause_from_mobile"):
		hud.toggle_pause_from_mobile()


func _mobile_cycle_assignment() -> void:
	if not _gameplay_controls_visible():
		return
	var care := get_tree().get_first_node_in_group("care_manager")
	if care:
		care.cycle_assignment()


func _mobile_answer(value: int) -> void:
	var hud := get_tree().get_first_node_in_group("hud")
	if hud and hud.has_method("answer_patient_count"):
		hud.answer_patient_count(value)


func _on_device_type_detected(value: String) -> void:
	mobile_enabled = value in ["mobile", "tablet"] or DisplayServer.is_touchscreen_available()
	_layout_controls()
	_refresh_visibility()


func set_mobile_enabled_for_test(value: bool) -> void:
	mobile_enabled = value
	_layout_controls()
	_refresh_visibility()
