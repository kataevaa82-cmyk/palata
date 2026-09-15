extends CharacterBody3D

@export var patrol_speed := 1.65
@export var corridor_min_x := -18.0
@export var corridor_max_x := 18.0
@export var beam_color := Color(1.0, 0.0, 0.0)
# Stored untranslated: it is the msgid the damage messages translate at the
# moment they are shown, so a language switch mid-shift still reads correctly.
@export var enemy_title := tr("санитарки")
# Which ending this enemy's kill maps to. Kept separate from enemy_title so the
# title can be translated without changing what happens when it kills you.
@export var enemy_kind := "orderly"
@export var safe_in_doctors_room := false
@export var corridor_only_damage := true
@export var sight_distance := 13.5
@export var lifetime_limit := 72.0
@export var sanity_damage := 3
@export var health_damage := 8
@export var eye_height := 1.68
@export var max_sanity_damage_total := 0
@export var minimum_sanity_after_attack := 0
@export var recovery_hint_on_exit := false

var model: Node3D
var player: CharacterBody3D
var direction := -1.0
var sanity_tick := 0.0
var damage_tick := 0.0
var lifetime := 0.0
var sanity_damage_inflicted := 0
var departing := false
var left_beam: MeshInstance3D
var right_beam: MeshInstance3D

func _ready() -> void:
	add_to_group("hostile_orderlies")
	player = get_tree().get_first_node_in_group("player") as CharacterBody3D
	if not model:
		model = get_node_or_null("Model") as Node3D
	_create_beams()
	_play_animation()

func setup(imported_model: Node3D) -> void:
	model = imported_model
	_play_animation()

func _physics_process(delta: float) -> void:
	if departing:
		return
	lifetime += delta
	if lifetime > lifetime_limit:
		if recovery_hint_on_exit:
			_begin_departure()
		else:
			queue_free()
		return
	if not player or not is_instance_valid(player):
		player = get_tree().get_first_node_in_group("player") as CharacterBody3D
	if not player:
		return
	if not is_on_floor():
		velocity.y -= 18.0 * delta
	var sees_player := _has_clear_sight()
	if sees_player:
		velocity.x = 0.0
		velocity.z = 0.0
		look_at(Vector3(player.global_position.x, global_position.y, player.global_position.z), Vector3.UP)
		_update_beams(true)
		sanity_tick += delta
		damage_tick += delta
		if sanity_tick >= 0.42:
			sanity_tick = 0.0
			_apply_sanity_damage()
		if damage_tick >= 1.15 and health_damage > 0:
			damage_tick = 0.0
			if player.has_method("take_damage"):
				player.take_damage(health_damage, tr("лучи %s") % tr(enemy_title), enemy_kind)
	else:
		_update_beams(false)
		sanity_tick = 0.0
		damage_tick = 0.0
		velocity.x = direction * patrol_speed
		velocity.z = move_toward(velocity.z, 0.0, 5.0 * delta)
		look_at(global_position + Vector3(direction, 0.0, 0.0), Vector3.UP)
		if global_position.x <= corridor_min_x:
			direction = 1.0
		elif global_position.x >= corridor_max_x:
			direction = -1.0
	move_and_slide()

func _apply_sanity_damage() -> void:
	if not player or not player.has_method("take_sanity_damage"):
		return
	var amount := sanity_damage
	if max_sanity_damage_total > 0:
		amount = mini(amount, maxi(max_sanity_damage_total - sanity_damage_inflicted, 0))
	if minimum_sanity_after_attack > 0:
		amount = mini(amount, maxi(int(player.get("sanity")) - minimum_sanity_after_attack, 0))
	if amount > 0:
		player.take_sanity_damage(amount, tr("%s взгляд %s") % [
			tr("синий") if beam_color.b > beam_color.r else tr("красный"), tr(enemy_title)], enemy_kind)
		sanity_damage_inflicted += amount
	if recovery_hint_on_exit and (amount <= 0 or (max_sanity_damage_total > 0 and sanity_damage_inflicted >= max_sanity_damage_total)):
		_begin_departure()

func _begin_departure() -> void:
	if departing:
		return
	departing = true
	_update_beams(false)
	velocity = Vector3.ZERO
	collision_layer = 0
	collision_mask = 0
	set_physics_process(false)
	var exit_x := corridor_min_x - 1.5 if global_position.x < 0.0 else corridor_max_x + 1.5
	var exit_position := Vector3(exit_x, global_position.y, 0.0)
	var direction_to_exit := exit_position - global_position
	direction_to_exit.y = 0.0
	if direction_to_exit.length() > 0.05:
		look_at(global_position + direction_to_exit.normalized(), Vector3.UP)
	var hud := get_tree().get_first_node_in_group("hud")
	if hud:
		hud.show_message(tr("Главная медсестра закончила проверку и уходит."), 3.5)
	var departure := create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
	departure.tween_property(self, "global_position", exit_position, clampf(direction_to_exit.length() / maxf(patrol_speed, 0.5), 1.2, 7.0))
	departure.tween_callback(_finish_departure)

func _finish_departure() -> void:
	if recovery_hint_on_exit:
		var hud := get_tree().get_first_node_in_group("hud")
		if hud:
			hud.set_objective(tr("Восстановите рассудок за компьютером в ОРДИНАТОРСКОЙ."))
			hud.show_message(tr("Главная медсестра ушла. Восстановите рассудок за компьютером в ОРДИНАТОРСКОЙ."), 7.0)
	queue_free()

func _has_clear_sight() -> bool:
	if safe_in_doctors_room and player.has_method("is_in_doctors_room") and player.is_in_doctors_room():
		return false
	if corridor_only_damage and player.has_method("is_in_corridor") and not player.is_in_corridor():
		return false
	var origin := global_position + Vector3(0.0, eye_height - 0.10, 0.0)
	var target := player.global_position + Vector3(0.0, 1.42, 0.0)
	if origin.distance_to(target) > sight_distance:
		return false
	var query := PhysicsRayQueryParameters3D.create(origin, target, 1)
	query.exclude = [get_rid()]
	query.collide_with_areas = false
	query.collide_with_bodies = true
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	return not hit.is_empty() and hit.get("collider") == player

func _create_beams() -> void:
	var material := StandardMaterial3D.new()
	material.albedo_color = Color(beam_color.r, beam_color.g, beam_color.b, 0.78)
	material.emission_enabled = true
	material.emission = beam_color
	material.emission_energy_multiplier = 9.0
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	for index in 2:
		var beam := MeshInstance3D.new()
		beam.name = "EyeBeam%d" % index
		var box := BoxMesh.new()
		box.size = Vector3(0.022, 0.022, 1.0)
		beam.mesh = box
		beam.material_override = material
		beam.visible = false
		beam.top_level = true
		add_child(beam)
		if index == 0:
			left_beam = beam
		else:
			right_beam = beam

func _update_beams(enabled: bool) -> void:
	if not left_beam or not right_beam or not left_beam.is_inside_tree() or not right_beam.is_inside_tree():
		return
	left_beam.visible = enabled
	right_beam.visible = enabled
	if not enabled:
		return
	var target := player.global_position + Vector3(0.0, 1.42, 0.0)
	var right := global_transform.basis.x.normalized()
	for beam_data in [[left_beam, -0.045], [right_beam, 0.045]]:
		var beam := beam_data[0] as MeshInstance3D
		var origin := global_position + Vector3(0.0, eye_height, 0.0) + right * float(beam_data[1])
		var distance := origin.distance_to(target)
		(beam.mesh as BoxMesh).size.z = distance
		beam.global_position = (origin + target) * 0.5
		beam.look_at(target, Vector3.UP)

func _play_animation() -> void:
	if not model:
		return
	for node in _all_nodes(model):
		if node is AnimationPlayer:
			var player_node := node as AnimationPlayer
			for animation_name in player_node.get_animation_list():
				if animation_name == &"RESET":
					continue
				var animation := player_node.get_animation(animation_name)
				if animation:
					animation.loop_mode = Animation.LOOP_LINEAR
				player_node.play(animation_name)
				return

func _all_nodes(root: Node) -> Array[Node]:
	var result: Array[Node] = [root]
	for child in root.get_children():
		result.append_array(_all_nodes(child))
	return result
