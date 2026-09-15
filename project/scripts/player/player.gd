extends CharacterBody3D

signal health_changed(value: int)
signal sanity_changed(value: int)

@export var walk_speed := 3.15
@export var acceleration := 14.0
@export var mouse_sensitivity := 0.0018
@export var gravity := 18.0
@export var max_health := 100
@export var max_sanity := 100

@onready var head: Node3D = $Head
@onready var camera: Camera3D = $Head/Camera3D
@onready var ray: RayCast3D = $Head/Camera3D/InteractionRay
@onready var flashlight: SpotLight3D = $Head/Camera3D/Flashlight
@onready var held_item_anchor: Node3D = $Head/Camera3D/HeldItemAnchor

var can_move := true
var step_distance := 0.0
var safe_spawn := Vector3.ZERO
var health := 100
var sanity := 100
var dead := false
var doctors_room_heal_tick := 0.0
var was_in_doctors_room := false
var held_item_copy: Node3D
# long_corridor anomaly: 0 = normal, 1 = the corridor visibly stretches away.
var corridor_stretch_target := 0.0
var corridor_stretch := 0.0

func _ready() -> void:
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	add_to_group("player")
	safe_spawn = global_position
	health = max_health
	sanity = max_sanity

func _input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED and not _ui_blocking():
		apply_look_delta(event.relative)

func apply_look_delta(relative: Vector2) -> void:
	rotate_y(-relative.x * mouse_sensitivity)
	head.rotate_x(-relative.y * mouse_sensitivity)
	head.rotation.x = clamp(head.rotation.x, deg_to_rad(-82.0), deg_to_rad(82.0))

func apply_touch_look_delta(relative: Vector2, sensitivity: float) -> void:
	if _ui_blocking():
		return
	rotate_y(-relative.x * sensitivity)
	head.rotate_x(-relative.y * sensitivity)
	head.rotation.x = clamp(head.rotation.x, deg_to_rad(-82.0), deg_to_rad(82.0))

func mobile_interact() -> void:
	if not _ui_blocking():
		_interact()

func mobile_toggle_flashlight() -> void:
	if not _ui_blocking():
		flashlight.visible = not flashlight.visible

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("interact"):
		if not _ui_blocking():
			_interact()
	elif event.is_action_pressed("flashlight"):
		if not _ui_blocking():
			flashlight.visible = not flashlight.visible
	elif event is InputEventKey and event.pressed and event.keycode == KEY_HOME:
		return_to_safe_spawn()
	elif event is InputEventKey and event.pressed and event.keycode == KEY_TAB:
		var care := get_tree().get_first_node_in_group("care_manager")
		if care and care.has_method("cycle_assignment") and not _ui_blocking():
			care.cycle_assignment()
			get_viewport().set_input_as_handled()

func _physics_process(delta: float) -> void:
	var sanity_pressure := 1.0 - float(sanity) / float(max_sanity)
	# The stretch only acts in the corridor and eases in and out, so walking into
	# a ward during the anomaly does not snap the camera.
	var stretch_goal := corridor_stretch_target if is_in_corridor() else 0.0
	corridor_stretch = move_toward(corridor_stretch, stretch_goal, delta * 0.6)
	camera.fov = 78.0 + sanity_pressure * (4.0 + sin(Time.get_ticks_msec() * 0.004) * 1.6) - corridor_stretch * 26.0
	if global_position.y < -2.0:
		return_to_safe_spawn()
	if not is_on_floor():
		velocity.y -= gravity * delta
	if can_move:
		var input_vec := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
		var mobile_controls := get_tree().get_first_node_in_group("mobile_controls")
		if mobile_controls and mobile_controls.mobile_enabled:
			var touch_input: Vector2 = mobile_controls.movement_vector
			if touch_input.length_squared() > input_vec.length_squared():
				input_vec = touch_input
		var direction := (transform.basis * Vector3(input_vec.x, 0.0, input_vec.y)).normalized()
		var target := direction * walk_speed * (1.0 - 0.45 * corridor_stretch)
		velocity.x = move_toward(velocity.x, target.x, acceleration * delta)
		velocity.z = move_toward(velocity.z, target.z, acceleration * delta)
	else:
		velocity.x = move_toward(velocity.x, 0.0, acceleration * delta)
		velocity.z = move_toward(velocity.z, 0.0, acceleration * delta)
	move_and_slide()
	_update_doctors_room_healing(delta)
	if is_on_floor() and Vector2(velocity.x, velocity.z).length() > 0.3:
		step_distance += Vector2(velocity.x, velocity.z).length() * delta
		if step_distance >= 1.65:
			step_distance = 0.0
			var audio := get_tree().get_first_node_in_group("audio_manager")
			if audio and audio.has_method("player_step"):
				audio.player_step(global_position)
	_update_prompt()
	if held_item_anchor:
		held_item_anchor.rotation.z = 0.04 + sin(Time.get_ticks_msec() * 0.0025) * 0.018

func show_held_inventory_item(source: Node3D) -> void:
	if held_item_copy and is_instance_valid(held_item_copy):
		held_item_copy.queue_free()
	held_item_copy = null
	if not source or not is_instance_valid(source):
		return
	var copy := source.duplicate() as Node3D
	if not copy:
		return
	copy.name = "ПредметВИнвентаре"
	copy.set_script(null)
	_strip_held_collisions(copy)
	held_item_anchor.add_child(copy)
	copy.transform = Transform3D.IDENTITY
	for node in _all_nodes(copy):
		if node is Node3D:
			(node as Node3D).visible = true
		if node is MeshInstance3D:
			(node as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	held_item_copy = copy
	call_deferred("_normalize_held_item", copy)

func _strip_held_collisions(root: Node) -> void:
	for child in root.get_children():
		if child is CollisionObject3D or child is CollisionShape3D:
			root.remove_child(child)
			child.free()
		else:
			_strip_held_collisions(child)

func _normalize_held_item(copy: Node3D) -> void:
	if not is_instance_valid(copy):
		return
	var points: Array[Vector3] = []
	var to_anchor := held_item_anchor.global_transform.affine_inverse()
	for node in _all_nodes(copy):
		if node is MeshInstance3D and (node as MeshInstance3D).mesh:
			var mesh_node := node as MeshInstance3D
			var transform_to_anchor := to_anchor * mesh_node.global_transform
			for corner in range(8):
				points.append(transform_to_anchor * mesh_node.mesh.get_aabb().get_endpoint(corner))
	if points.is_empty():
		return
	var low := points[0]
	var high := points[0]
	for point in points:
		low = low.min(point)
		high = high.max(point)
	var size := high - low
	var largest := maxf(size.x, maxf(size.y, size.z))
	if largest <= 0.001:
		return
	var factor := 0.42 / largest
	copy.scale = Vector3.ONE * factor
	copy.position = -((low + high) * 0.5) * factor

func _all_nodes(root: Node) -> Array[Node]:
	var result: Array[Node] = [root]
	for child in root.get_children():
		result.append_array(_all_nodes(child))
	return result

func _ui_blocking() -> bool:
	var hud := get_tree().get_first_node_in_group("hud")
	return hud and hud.has_method("is_blocking_gameplay") and hud.is_blocking_gameplay()

func _find_interactable() -> Node:
	if not ray.is_colliding():
		return null
	var node: Node = ray.get_collider()
	while node:
		if node.has_method("interact"):
			return node
		node = node.get_parent()
	return null

func _interact() -> void:
	var target := _find_interactable()
	if target:
		var anomalies := get_tree().get_first_node_in_group("anomaly_manager")
		if anomalies and anomalies.has_method("discover_target"):
			anomalies.discover_target(target)
		target.interact(self)

func _update_prompt() -> void:
	var hud := get_tree().get_first_node_in_group("hud")
	if not hud:
		return
	var target := _find_interactable()
	if target and target.has_method("interaction_text"):
		hud.set_interaction_prompt(target.interaction_text())
	else:
		hud.set_interaction_prompt("")

func set_frozen(value: bool) -> void:
	can_move = not value

func set_corridor_stretch(value: float) -> void:
	corridor_stretch_target = clampf(value, 0.0, 1.0)

func take_damage(amount: int, source := "опасность", kind := "danger") -> void:
	if dead or amount <= 0:
		return
	health = maxi(health - amount, 0)
	health_changed.emit(health)
	var hud := get_tree().get_first_node_in_group("hud")
	if hud:
		# Status, not story: repeated hits replace each other instead of queueing
		# ahead of the lines the player actually needs to read.
		hud.show_status(tr("Удар! Здоровье: %d/%d") % [health, max_health], 1.1)
	var original_tilt := head.rotation.z
	var impact := create_tween()
	impact.tween_property(head, "rotation:z", original_tilt + deg_to_rad(8.0), 0.08)
	impact.tween_property(head, "rotation:z", original_tilt, 0.22)
	if health <= 0:
		_die(source, kind)

func take_sanity_damage(amount: int, reason := "аномалия", _kind := "anomaly") -> void:
	if dead or amount <= 0:
		return
	sanity = maxi(sanity - amount, 0)
	sanity_changed.emit(sanity)
	var hud := get_tree().get_first_node_in_group("hud")
	if hud:
		# Callers that compose a reason from parts translate those parts
		# themselves; tr() here covers the plain ones and is a no-op on text
		# that is already English.
		hud.show_status(tr("Рассудок −%d: %s") % [amount, tr(reason)], 1.4)
	var original_tilt := head.rotation.z
	var shock := create_tween()
	shock.tween_property(head, "rotation:z", original_tilt + deg_to_rad(randf_range(-3.5, 3.5)), 0.10)
	shock.tween_property(head, "rotation:z", original_tilt, 0.32)
	if sanity <= 0:
		dead = true
		can_move = false
		velocity = Vector3.ZERO
		var state := get_tree().get_first_node_in_group("hospital_state")
		if state:
			state.set_flag("sanity_broken", true)
			state.request_ending("lost_mind")

func restore_sanity(amount: int) -> void:
	if dead or amount <= 0:
		return
	sanity = mini(sanity + amount, max_sanity)
	sanity_changed.emit(sanity)

func restore_health(amount: int) -> void:
	if dead or amount <= 0 or health >= max_health:
		return
	health = mini(health + amount, max_health)
	health_changed.emit(health)

func is_in_doctors_room() -> bool:
	return global_position.x > 5.05 and global_position.x < 9.95 and global_position.z < -1.58 and global_position.z > -5.92

func is_in_corridor() -> bool:
	return absf(global_position.z) < 1.46

func _update_doctors_room_healing(delta: float) -> void:
	var inside := is_in_doctors_room()
	if inside and not was_in_doctors_room and health < max_health:
		var hud := get_tree().get_first_node_in_group("hud")
		if hud:
			hud.show_message(tr("Ординаторская: здоровье постепенно восстанавливается."), 2.8)
	was_in_doctors_room = inside
	var time_manager := get_tree().get_first_node_in_group("time_manager")
	var healing_cap := max_health
	if time_manager and bool(time_manager.get("running")):
		healing_cap = mini(max_health, 60)
	if not inside or dead or health >= healing_cap:
		doctors_room_heal_tick = 0.0
		return
	doctors_room_heal_tick += delta
	while doctors_room_heal_tick >= 0.16:
		doctors_room_heal_tick -= 0.16
		health = mini(health + 1, healing_cap)
		health_changed.emit(health)

func _die(source: String, kind := "danger") -> void:
	if dead:
		return
	dead = true
	can_move = false
	velocity = Vector3.ZERO
	var state := get_tree().get_first_node_in_group("hospital_state")
	if state:
		state.set_flag("death_source", source)
		state.record_observation("player_killed", source)
		# The ending is picked from the caller's `kind`, never from the text.
		# It used to be chosen by searching the damage source for "санитарк" /
		# "медицин", which meant translating a single message would silently
		# hand the player the wrong ending.
		const ENDINGS := {
			"head_nurse": "killed_by_head_nurse",
			"orderly": "killed_by_orderly",
			"medical": "medical_error",
			"patient": "killed_by_patient",
		}
		state.request_ending(String(ENDINGS.get(kind, "killed_by_patient")))

func return_to_safe_spawn() -> void:
	global_position = safe_spawn
	velocity = Vector3.ZERO
