extends CharacterBody3D

enum Behaviour { BREAKING_PROP, HUNTING }

@export var break_speed := 2.35
@export var chase_speed := 3.20
@export var attack_damage := 16

var model: Node3D
var behaviour := Behaviour.BREAKING_PROP
var target_prop: Node3D
var player: CharacterBody3D
var break_timer := 0.0
var attack_cooldown := 0.0
var patient_shader: Shader
var material_cache: Dictionary = {}
var restrained := false
var restraint_hint_cooldown := 0.0

func _ready() -> void:
	add_to_group("violent_patients")
	player = get_tree().get_first_node_in_group("player") as CharacterBody3D
	if not model:
		model = get_node_or_null("Model") as Node3D
	if model:
		model.rotation_degrees.y = 180.0
	_apply_materials()
	_play_animation()
	call_deferred("_choose_prop")

func setup(imported_model: Node3D) -> void:
	model = imported_model
	model.rotation_degrees.y = 180.0
	_apply_materials()
	_play_animation()

func _physics_process(delta: float) -> void:
	if restrained:
		velocity = Vector3.ZERO
		return
	restraint_hint_cooldown = maxf(restraint_hint_cooldown - delta, 0.0)
	attack_cooldown = maxf(attack_cooldown - delta, 0.0)
	if not player or not is_instance_valid(player):
		player = get_tree().get_first_node_in_group("player") as CharacterBody3D
	if not player:
		return
	if not is_on_floor():
		velocity.y -= 18.0 * delta
	if behaviour == Behaviour.BREAKING_PROP:
		_process_breaking(delta)
	else:
		_process_hunt()
	move_and_slide()

func _process_breaking(delta: float) -> void:
	break_timer += delta
	if not target_prop or not is_instance_valid(target_prop):
		_choose_prop()
	if not target_prop:
		_break_prop()
		return
	var corridor_target := Vector3(target_prop.global_position.x, global_position.y, clampf(target_prop.global_position.z, -0.75, 0.75))
	var distance := _move_towards(corridor_target, break_speed)
	if distance < 1.25 or break_timer > 6.5:
		_break_prop()

func _process_hunt() -> void:
	var target := player.global_position
	var horizontal_distance := Vector2(target.x - global_position.x, target.z - global_position.z).length()
	if horizontal_distance <= 1.22 and attack_cooldown <= 0.0:
		attack_cooldown = 1.80
		velocity.x = 0.0
		velocity.z = 0.0
		if player.has_method("take_damage"):
			player.take_damage(attack_damage, tr("буйный пациент"), "patient")
		_show_restraints_hint(true)
		return

	# First reach the matching doorway through the corridor, then enter the ward.
	var destination := target
	if absf(target.z) > 1.35 and absf(target.x - global_position.x) > 0.85:
		destination = Vector3(target.x, target.y, 0.0)
	_move_towards(destination, chase_speed)

func interaction_text() -> String:
	var care := get_tree().get_first_node_in_group("care_manager")
	if care and bool(care.get("has_patient_restraints")):
		return tr("[E] Связать буйного пациента вязками")
	return tr("[E] Нужны вязки из настенного шкафа в медскладе")

func interact(_actor: Node) -> void:
	if restrained:
		return
	var care := get_tree().get_first_node_in_group("care_manager")
	var hud := get_tree().get_first_node_in_group("hud")
	if not care or not care.use_patient_restraints():
		if hud:
			hud.show_message(tr("Нужны вязки. Они лежат в открытом настенном шкафу в МЕДСКЛАДЕ."), 3.2)
		return
	restrained = true
	velocity = Vector3.ZERO
	set_physics_process(false)
	collision_layer = 0
	collision_mask = 0
	var interaction_area := get_node_or_null("RestraintInteractionArea") as Area3D
	if interaction_area:
		interaction_area.collision_layer = 0
	var state := get_tree().get_first_node_in_group("hospital_state")
	if state:
		state.set_flag("violent_patient_restrained", true)
		state.set_flag("violent_patient_loose", false)
		state.record_observation("violent_patient_restrained", "returned_to_ward_4")
	if hud:
		hud.show_message(tr("Пациент связан. Он возвращается в палату №4."), 4.0)
	var corridor_point := Vector3(global_position.x, 0.05, 0.0)
	var ward_door := Vector3(-17.5, 0.05, 0.0)
	var ward_inside := Vector3(-17.5, 0.05, 2.45)
	var return_to_ward := create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	return_to_ward.tween_property(self, "global_position", corridor_point, 0.8)
	return_to_ward.tween_property(self, "global_position", ward_door, maxf(absf(corridor_point.x - ward_door.x) / 2.4, 0.8))
	return_to_ward.tween_property(self, "global_position", ward_inside, 1.0)
	return_to_ward.tween_callback(queue_free)

func _move_towards(target: Vector3, speed: float) -> float:
	var flat := target - global_position
	flat.y = 0.0
	var distance := flat.length()
	if distance > 0.05:
		var direction := flat / distance
		velocity.x = direction.x * speed
		velocity.z = direction.z * speed
		look_at(global_position + direction, Vector3.UP)
	else:
		velocity.x = 0.0
		velocity.z = 0.0
	return distance

func _choose_prop() -> void:
	var hospital := get_tree().get_first_node_in_group("hospital_model")
	if not hospital:
		return
	for wanted in ["interaction_medical_cart", "nurse_chair_v2", "wheelchair_v2"]:
		var found := hospital.find_child(wanted, true, false) as Node3D
		if found and not found.get_meta("destroyed_by_patient", false):
			target_prop = found
			return

func _break_prop() -> void:
	if behaviour == Behaviour.HUNTING:
		return
	behaviour = Behaviour.HUNTING
	if target_prop and is_instance_valid(target_prop):
		target_prop.set_meta("destroyed_by_patient", true)
		var tipped := target_prop.rotation_degrees
		tipped.z += 67.0
		var destruction := target_prop.create_tween().set_parallel(true)
		destruction.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		destruction.tween_property(target_prop, "rotation_degrees", tipped, 0.55)
		destruction.tween_property(target_prop, "position:y", target_prop.position.y + 0.14, 0.25)
	var state := get_tree().get_first_node_in_group("hospital_state")
	if state:
		state.set_flag("violent_patient_loose", true)
		state.record_observation("damaged_property", "violent_patient")
	_show_restraints_hint(true)
	var care_manager := get_tree().get_first_node_in_group("care_manager")
	if care_manager:
		care_manager.trigger_water_spill()

func _show_restraints_hint(force := false) -> void:
	if not force and restraint_hint_cooldown > 0.0:
		return
	var hud := get_tree().get_first_node_in_group("hud")
	if not hud:
		return
	var care := get_tree().get_first_node_in_group("care_manager")
	if care and bool(care.get("has_patient_restraints")):
		hud.show_message(tr("БУЙНЫЙ ПАЦИЕНТ НАПАЛ! Вязки уже у вас — подойдите ближе и нажмите E."), 5.0)
	else:
		hud.show_message(tr("БУЙНЫЙ ПАЦИЕНТ НАПАЛ! Возьмите ВЯЗКИ в открытом настенном шкафу в МЕДСКЛАДЕ."), 6.0)
	restraint_hint_cooldown = 7.5

func _play_animation() -> void:
	if not model:
		return
	for node in _all_nodes(model):
		if node is AnimationPlayer:
			var animation_player := node as AnimationPlayer
			var fallback: StringName = &""
			var walk_fallback: StringName = &""
			for animation_name in animation_player.get_animation_list():
				if animation_name == &"RESET":
					continue
				if fallback == &"":
					fallback = animation_name
				var lower_name := String(animation_name).to_lower()
				if "walk" in lower_name and walk_fallback == &"":
					walk_fallback = animation_name
				if "run" not in lower_name:
					continue
				var animation := animation_player.get_animation(animation_name)
				if animation:
					animation.loop_mode = Animation.LOOP_LINEAR
				animation_player.play(animation_name)
				animation_player.speed_scale = 1.15
				return
			if walk_fallback != &"":
				var walk_animation := animation_player.get_animation(walk_fallback)
				if walk_animation:
					walk_animation.loop_mode = Animation.LOOP_LINEAR
				animation_player.play(walk_fallback)
				animation_player.speed_scale = 1.15
				return
			if fallback != &"":
				var animation := animation_player.get_animation(fallback)
				if animation:
					animation.loop_mode = Animation.LOOP_LINEAR
				animation_player.play(fallback)
				animation_player.speed_scale = 1.15
				return

func _apply_materials() -> void:
	if not model:
		return
	for node in _all_nodes(model):
		if not node is MeshInstance3D:
			continue
		var lower := String(node.name).to_lower()
		# The downloaded CC0 human uses one textured skinned mesh.  Preserve its
		# authored skin/clothes texture instead of replacing the whole body with
		# the old procedural patient's single gown material.
		if "human_mesh" in lower:
			continue
		var key := "gown"
		var color := Color(0.12, 0.22, 0.18)
		var roughness := 0.96
		var metallic := 0.0
		var emission := Color.BLACK
		if "rust" in lower:
			key = "rust"
			color = Color(0.32, 0.045, 0.008)
			metallic = 0.12
		elif "rail" in lower:
			key = "metal"
			color = Color(0.22, 0.24, 0.20)
			metallic = 0.52
			roughness = 0.74
		elif "eye" in lower:
			key = "eye"
			color = Color(0.10, 0.045, 0.018)
			roughness = 0.38
		elif "bruise" in lower:
			key = "bruise"
			color = Color(0.20, 0.035, 0.055)
		elif "bandage" in lower:
			key = "bandage"
			color = Color(0.48, 0.43, 0.27)
		elif "fitted_shirt" in lower or "collar_trim" in lower:
			key = "shirt"
			color = Color(0.15, 0.30, 0.27)
			roughness = 0.97
		elif "fitted_pants" in lower or "trousers" in lower or "pants" in lower:
			key = "pants"
			color = Color(0.085, 0.18, 0.17)
			roughness = 0.97
		elif "gown" in lower:
			key = "gown"
			color = Color(0.12, 0.22, 0.18)
		elif "hair" in lower or "brow" in lower or "mouth" in lower or "shoe" in lower:
			key = "dark"
			color = Color(0.018, 0.014, 0.010)
		elif "skin" in lower or "head" in lower or "lid" in lower or "ear" in lower \
				or "fist" in lower or "hand" in lower or "shin" in lower or "body" in lower:
			key = "skin"
			color = Color(0.53, 0.38, 0.31)
			roughness = 0.88
		(node as MeshInstance3D).material_override = _patient_material(key, color, roughness, metallic, emission)

func _patient_material(key: String, color: Color, roughness: float, metallic: float, emission: Color) -> ShaderMaterial:
	if material_cache.has(key):
		return material_cache[key]
	if not patient_shader:
		patient_shader = Shader.new()
		patient_shader.code = """
shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
uniform vec4 base_color : source_color;
uniform vec4 stain_color : source_color;
uniform vec4 glow_color : source_color;
uniform float glow_strength = 0.0;
uniform float material_roughness = 0.95;
uniform float material_metallic = 0.0;
uniform float texture_scale = 11.0;
varying vec3 local_position;

float hash31(vec3 p) {
	p = fract(p * 0.1031);
	p += dot(p, p.yzx + 33.33);
	return fract((p.x + p.y) * p.z);
}

void vertex() {
	local_position = VERTEX;
}

void fragment() {
	float coarse = hash31(floor(local_position * texture_scale));
	float fine = hash31(floor(local_position * texture_scale * 4.7 + vec3(7.0, 3.0, 11.0)));
	float grime = smoothstep(0.58, 0.92, coarse);
	float thread = sin((local_position.y + local_position.x * 0.35) * texture_scale * 24.0) * 0.5 + 0.5;
	vec3 aged = mix(base_color.rgb, stain_color.rgb, grime * 0.62 + fine * 0.12);
	aged *= 0.92 + thread * 0.06;
	ALBEDO = aged;
	ROUGHNESS = clamp(material_roughness + coarse * 0.05, 0.05, 1.0);
	METALLIC = material_metallic;
	EMISSION = glow_color.rgb * glow_strength * (0.75 + fine * 0.25);
}
"""
	var material := ShaderMaterial.new()
	material.shader = patient_shader
	material.resource_name = "violent_patient_" + key
	material.set_shader_parameter("base_color", color)
	material.set_shader_parameter("stain_color", color.darkened(0.76))
	material.set_shader_parameter("material_roughness", roughness)
	material.set_shader_parameter("material_metallic", metallic)
	material.set_shader_parameter("glow_color", emission)
	material.set_shader_parameter("glow_strength", 4.5 if emission != Color.BLACK else 0.0)
	material.set_shader_parameter("texture_scale", 18.0 if key in ["gown", "shirt", "pants", "bandage"] else 10.0)
	material_cache[key] = material
	return material

func _all_nodes(root: Node) -> Array[Node]:
	var result: Array[Node] = [root]
	for child in root.get_children():
		result.append_array(_all_nodes(child))
	return result
