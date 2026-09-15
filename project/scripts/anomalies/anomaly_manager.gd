extends Node

const ORDERLY_GHOST_SCENE: PackedScene = preload("res://assets/models/orderly_ghost_v6.glb")
const VIOLENT_PATIENT_SCENE: PackedScene = preload("res://assets/models/violent_patient_v1.glb")
const VIOLENT_PATIENT_SCRIPT := preload("res://scripts/anomalies/violent_patient.gd")
const ORDERLY_ENEMY_SCRIPT := preload("res://scripts/anomalies/orderly_enemy.gd")

var active: Dictionary = {}
var discovered: Dictionary = {}
var discovery_accumulator := 0.0
var activated_count := 0
var orderly_shader: Shader
var orderly_material_cache: Dictionary = {}
var head_nurse_pending := false
var head_nurse_reason := "medical_error"
var hostile_pending := false
var long_corridor_running := false

const EMPTY_BED_SECONDS := 45.0
const LONG_CORRIDOR_SECONDS := 30.0

const ANOMALY_NAMES := {
	"extra_patient": "лишний пациент",
	"room6_television": "телевизор в палате №6", "wrong_bucket": "неправильное ведро",
	"elevator_minus_one": "лифт на минус первом этаже", "operator_count_call": "звонок оператора",
	"room_zero": "палата ноль",
	"reverse_clock": "обратный ход часов", "player_name_journal": "ваша фамилия в журнале",
	"extra_chair": "лишний стул", "moving_wheelchair": "движущаяся коляска",
	"anatomy_poster": "изменившийся плакат", "wrong_reflection": "чужое отражение",
	"copied_footsteps": "повторяющиеся шаги", "self_phone_call": "звонок собственным голосом",
	"mannequin": "манекен в процедурной", "wrong_door_label": "неверная табличка",
	"wrong_door": "неправильная дверь", "long_corridor": "удлинившийся коридор",
	"extra_window": "лишнее окно", "wrong_patient": "изменившийся пациент",
	"empty_bed": "пустая кровать", "false_note": "ложная записка",
	"false_nurse": "ненастоящая санитарка", "violent_patient": "буйный пациент"
}

const DEFINITIONS := {
	"extra_patient": {"phase":"ESCALATION", "category":"PATIENT"},
	"room6_television": {"phase":"ESCALATION", "category":"SIGNAL"},
	"wrong_bucket": {"phase":"ESCALATION", "category":"SIGNAL"},
	"elevator_minus_one": {"phase":"ESCALATION", "category":"ENVIRONMENT"},
	"operator_count_call": {"phase":"DOUBT", "category":"SIGNAL"},
	"room_zero": {"phase":"PROVOCATION", "category":"DANGEROUS"},
	"reverse_clock": {"phase":"ESCALATION", "category":"ENVIRONMENT"},
	"player_name_journal": {"phase":"PROVOCATION", "category":"SIGNAL"},
	"extra_chair": {"phase":"DOUBT", "category":"ENVIRONMENT"},
	"moving_wheelchair": {"phase":"DOUBT", "category":"ENVIRONMENT"},
	"anatomy_poster": {"phase":"DOUBT", "category":"ENVIRONMENT"},
	"wrong_reflection": {"phase":"PROVOCATION", "category":"ENVIRONMENT"},
	"copied_footsteps": {"phase":"ESCALATION", "category":"ENVIRONMENT"},
	"self_phone_call": {"phase":"ESCALATION", "category":"SIGNAL"},
	"mannequin": {"phase":"ESCALATION", "category":"PATIENT"},
	"wrong_door_label": {"phase":"DOUBT", "category":"ENVIRONMENT"},
	"wrong_door": {"phase":"PROVOCATION", "category":"SPATIAL"},
	"long_corridor": {"phase":"PROVOCATION", "category":"SPATIAL"},
	"extra_window": {"phase":"PROVOCATION", "category":"SPATIAL"},
	"wrong_patient": {"phase":"ESCALATION", "category":"PATIENT"},
	"empty_bed": {"phase":"ESCALATION", "category":"PATIENT"},
	"false_note": {"phase":"ESCALATION", "category":"SIGNAL"},
	"false_nurse": {"phase":"PROVOCATION", "category":"DANGEROUS"},
	"violent_patient": {"phase":"PROVOCATION", "category":"DANGEROUS"}
}

func _ready() -> void:
	add_to_group("anomaly_manager")
	reset_shift()

func _process_discovery(delta: float) -> void:
	if active.is_empty():
		return
	discovery_accumulator += delta
	if discovery_accumulator < 0.1:
		return
	discovery_accumulator = 0.0
	var player := get_tree().get_first_node_in_group("player") as Node3D
	if not player:
		return
	# Only world anomalies with a concrete visual source can be discovered by
	# proximity. Their activation remains independent, but the specific clue and
	# discovery record wait until the player actually reaches the source.
	var sources := {
		"wrong_reflection": "window_reflection",
		"mannequin": "cpr_mannequin",
		"false_note": "anomaly_note",
		"extra_chair": "nurse_chair_v2",
		"extra_patient": "anomaly_extra_patient",
		"moving_wheelchair": "wheelchair",
		"anatomy_poster": "anatom",
		"wrong_door_label": "door"
	}
	for id in active.keys():
		var source_name := String(sources.get(String(id), ""))
		if source_name.is_empty():
			continue
		var source := _find_first(source_name) as Node3D
		if source and source.visible and player.global_position.distance_to(source.global_position) <= 8.0:
			discover(String(id))

func reset_shift() -> void:
	active.clear()
	discovered.clear()
	discovery_accumulator = 0.0
	activated_count = 0
	head_nurse_pending = false
	head_nurse_reason = "medical_error"
	hostile_pending = false
	long_corridor_running = false
	orderly_shader = Shader.new()
	orderly_shader.code = """
shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
uniform vec4 base_color : source_color;
uniform vec4 detail_color : source_color;
uniform vec4 emission_color : source_color = vec4(0.0);
uniform float emission_strength = 0.0;
uniform float texture_scale = 8.0;
uniform float material_roughness = 0.9;
uniform float material_metallic = 0.0;
varying vec3 local_pos;

float hash31(vec3 p) {
	p = fract(p * 0.1031);
	p += dot(p, p.yzx + 33.33);
	return fract((p.x + p.y) * p.z);
}

float noise3(vec3 p) {
	vec3 i = floor(p);
	vec3 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hash31(i), hash31(i + vec3(1,0,0)), f.x),
	               mix(hash31(i + vec3(0,1,0)), hash31(i + vec3(1,1,0)), f.x), f.y),
	           mix(mix(hash31(i + vec3(0,0,1)), hash31(i + vec3(1,0,1)), f.x),
	               mix(hash31(i + vec3(0,1,1)), hash31(i + vec3(1,1,1)), f.x), f.y), f.z);
}

float fbm(vec3 p) {
	float value = 0.0;
	float amplitude = 0.58;
	for (int i = 0; i < 4; i++) {
		value += noise3(p) * amplitude;
		p = p * 2.07 + vec3(4.0, 9.0, 2.0);
		amplitude *= 0.48;
	}
	return value;
}

void vertex() {
	local_pos = VERTEX;
}

void fragment() {
	float coarse = fbm(local_pos * texture_scale);
	float fine = fbm(local_pos * texture_scale * 4.0 + vec3(7.0));
	float stain = smoothstep(0.64, 0.91, coarse);
	float thread = sin((local_pos.y + local_pos.z) * texture_scale * 16.0) * 0.5 + 0.5;
	vec3 color = mix(base_color.rgb, detail_color.rgb, coarse * 0.54 + stain * 0.22);
	color *= 0.91 + thread * 0.06 + fine * 0.03;
	ALBEDO = color;
	ROUGHNESS = clamp(material_roughness + coarse * 0.09, 0.05, 1.0);
	METALLIC = material_metallic;
	EMISSION = emission_color.rgb * emission_strength * (0.72 + fine * 0.28);
}
"""

func _process(_delta: float) -> void:
	_process_discovery(_delta)
	if long_corridor_running and _danger_active():
		# The stretched corridor slows the player down; a chase must not start
		# inside it, where the violent patient would be all but unescapable.
		_end_long_corridor()
	if hostile_pending and not _danger_active():
		hostile_pending = false
		spawn_hostile_orderly()
	if head_nurse_pending and not _danger_active():
		head_nurse_pending = false
		spawn_head_nurse_inspector(head_nurse_reason)

func _orderly_material(key: String, base: Color, detail: Color, roughness := 0.92, metallic := 0.0, emission := Color.BLACK, emission_strength := 0.0) -> ShaderMaterial:
	if orderly_material_cache.has(key):
		return orderly_material_cache[key]
	var material := ShaderMaterial.new()
	material.shader = orderly_shader
	material.resource_name = "orderly_" + key
	material.set_shader_parameter("base_color", base)
	material.set_shader_parameter("detail_color", detail)
	material.set_shader_parameter("material_roughness", roughness)
	material.set_shader_parameter("material_metallic", metallic)
	material.set_shader_parameter("emission_color", emission)
	material.set_shader_parameter("emission_strength", emission_strength)
	material.set_shader_parameter("texture_scale", 10.0 if key in ["cloth", "apron", "hood"] else 6.0)
	orderly_material_cache[key] = material
	return material

func _apply_orderly_materials(orderly: Node3D, eye_color := Color(1.0, 0.015, 0.002)) -> void:
	for node in _all_nodes(orderly):
		if not node is MeshInstance3D:
			continue
		var lower := String(node.name).to_lower()
		var material: Material
		if "eye" in lower:
			var eye_key := "eyes_blue" if eye_color.b > eye_color.r else "eyes_red"
			material = _orderly_material(eye_key, eye_color.darkened(0.30), eye_color.darkened(0.78), 0.25, 0.0, eye_color, 8.0)
		elif "face_void" in lower or "bucket_inner" in lower:
			material = _orderly_material("void", Color(0.001, 0.001, 0.001), Color.BLACK, 1.0)
		elif "apron" in lower:
			material = _orderly_material("apron", Color(0.34, 0.32, 0.23), Color(0.055, 0.045, 0.025), 0.98)
		elif "hood" in lower or "face_rim" in lower:
			material = _orderly_material("hood", Color(0.20, 0.21, 0.18), Color(0.025, 0.03, 0.024), 0.98)
		elif "hand" in lower or "forearm" in lower or "elbow" in lower or "wrist" in lower or "palm" in lower or "finger" in lower or "thumb" in lower:
			material = _orderly_material("skin", Color(0.29, 0.29, 0.26), Color(0.065, 0.065, 0.052), 0.96)
		elif "shoe" in lower or "grip" in lower:
			material = _orderly_material("rubber", Color(0.012, 0.013, 0.01), Color(0.001, 0.001, 0.001), 0.94)
		elif "bucket" in lower:
			material = _orderly_material("bucket", Color(0.025, 0.10, 0.18), Color(0.003, 0.014, 0.028), 0.70, 0.20)
		elif "rust" in lower:
			material = _orderly_material("rust", Color(0.32, 0.05, 0.01), Color(0.05, 0.005, 0.001), 1.0, 0.12)
		elif "metal" in lower or "button" in lower or "handle" in lower or "rim" in lower:
			material = _orderly_material("metal", Color(0.25, 0.27, 0.23), Color(0.045, 0.05, 0.038), 0.78, 0.42)
		else:
			material = _orderly_material("cloth", Color(0.10, 0.155, 0.12), Color(0.015, 0.032, 0.023), 0.98)
		node.material_override = material

func pool_for_phase(phase: String) -> Array[String]:
	var result: Array[String] = []
	var allowed := ["DOUBT"]
	if phase == "ESCALATION":
		allowed = ["DOUBT", "ESCALATION"]
	elif phase == "PROVOCATION":
		allowed = ["DOUBT", "ESCALATION", "PROVOCATION"]
	elif phase == "SILENCE":
		allowed = ["SILENCE", "DOUBT"]
	for id in DEFINITIONS:
		if DEFINITIONS[id].phase in allowed and not active.has(id):
			result.append(id)
	return result

func activate(id: String) -> bool:
	if not DEFINITIONS.has(id):
		return false
	if active.has(id):
		# Repeated scripted requests are idempotent for the world, but an
		# undiscovered anomaly still applies its one initial pressure when the
		# player reaches the source later. This also makes content tests stable
		# when a random background event selected the same anomaly first.
		if not discovered.has(id):
			_apply_sanity_impact(id)
		return true
	active[id] = true
	activated_count += 1
	match id:
		"extra_patient": _extra_patient()
		"room6_television": _audio().set_tv_noise(true)
		"wrong_bucket": _spawn_orderly_ghost("wrong_bucket_orderly", true)
		"elevator_minus_one": _elevator_minus_one()
		"operator_count_call": _start_phone_call("operator_count")
		"room_zero": _room_zero()
		"reverse_clock":
			_time().set_reverse(true)
			_audio().set_silence(true)
		"player_name_journal": _state().set_flag("player_name_journal", true)
		"extra_chair": _duplicate_named("nurse_chair_v2", Vector3(-0.8, 0.0, 0.0))
		"moving_wheelchair": _move_named_parts("wheelchair", Vector3(2.4, 0.0, 0.0), 18.0)
		"anatomy_poster": _recolor_first("anatom", Color(0.36, 0.055, 0.035))
		"wrong_reflection": _spawn_figure("window_reflection", Vector3(8.0, 0.0, -5.85), 1.0, Color(0.05, 0.06, 0.055))
		"copied_footsteps": _audio().set_echo_steps(true)
		"self_phone_call": _start_phone_call("self")
		"mannequin": _spawn_figure("cpr_mannequin", Vector3(-1.8, 0.0, 2.7), 0.92, Color(0.57, 0.50, 0.40))
		"wrong_door_label": _wrong_door_label()
		"wrong_door": _state().set_flag("wrong_door", true)
		"long_corridor": _long_corridor()
		"extra_window": _duplicate_named("window_frame", Vector3(0.0, 0.0, 3.2))
		"wrong_patient": _scale_first("ward_1_bed_1_patient_head", Vector3(1.0, 1.0, 1.12))
		"empty_bed": _empty_bed()
		"false_note": _spawn_note()
		"false_nurse": spawn_hostile_orderly()
		"violent_patient": _spawn_violent_patient()
		_:
			_state().set_flag(id, true)
	_state().record_observation("event_started", id)
	var audio := _audio()
	if audio and audio.has_method("play_anomaly_sting"):
		audio.play_anomaly_sting(id)
	_apply_sanity_impact(id)
	return true

func discover(id: String) -> bool:
	# Discovery is separate from activation so a remote event does not reveal its
	# name. The first direct observation supplies the specific clue and is logged
	# only once.
	if not active.has(id) or discovered.has(id):
		return false
	discovered[id] = true
	var hud := get_tree().get_first_node_in_group("hud")
	if hud:
		hud.show_message(tr("Замечено: %s") % tr(String(ANOMALY_NAMES.get(id, "необычное изменение"))), 3.5)
	var state := _state()
	if state:
		state.record_observation("anomaly_discovered", id)
	return true

func discover_target(target: Node) -> void:
	if not target:
		return
	var name := String(target.name).to_lower()
	var mapping := {
		"note": "false_note", "journal": "player_name_journal",
		"chair": "extra_chair", "poster": "anatomy_poster",
		"window": "extra_window", "door": "wrong_door_label",
		"mannequin": "mannequin", "wheelchair": "moving_wheelchair",
		"blood": "wrong_patient"
	}
	for token in mapping:
		if token in name:
			discover(String(mapping[token]))
			return

func _hospital() -> Node:
	return get_tree().get_first_node_in_group("hospital_model")

func _state() -> Node:
	return get_tree().get_first_node_in_group("hospital_state")

func _time() -> Node:
	return get_tree().get_first_node_in_group("time_manager")

func _audio() -> Node:
	return get_tree().get_first_node_in_group("audio_manager")

func _all_nodes(root: Node) -> Array[Node]:
	var out: Array[Node] = [root]
	for child in root.get_children():
		out.append_array(_all_nodes(child))
	return out

func _find_first(partial: String) -> Node:
	var hospital := _hospital()
	if not hospital:
		return null
	for node in _all_nodes(hospital):
		if partial.to_lower() in String(node.name).to_lower():
			return node
	return null

func _extra_patient() -> void:
	# A third figure between the two beds of ward 6: night 3 announces "three
	# silhouettes, still two beds", and the operator's count must rest on
	# something the player can actually see. It used to copy the empty
	# ward_2_bed_2 frame into ward 2, which showed neither a patient nor ward 6.
	var hospital := _hospital()
	var first := _find_first("ward_6_bed_1_patient_v3") as Node3D
	var second := _find_first("ward_6_bed_2_patient_v3") as Node3D
	var spot := Vector3(-7.5, 0.0, 3.72)
	if first and second:
		spot = (first.global_position + second.global_position) * 0.5
		spot.y = 0.0
	if hospital:
		var figure := _spawn_figure("anomaly_extra_patient", (hospital as Node3D).to_local(spot), 1.0, Color(0.09, 0.11, 0.10), 0.0)
		figure.look_at(Vector3(spot.x, figure.global_position.y, 0.0), Vector3.UP)
	# Relative, so an escaped or missing patient on the same night still counts.
	_state().set_patient_count(int(_state().patient_count) + 1)

func _empty_bed() -> void:
	# Hidden the same way the story hides a patient: the interaction volume goes
	# with the body and the journal stops listing her. It is temporary, so a
	# prescription for Demina is delayed rather than lost for the whole night.
	var levels := get_tree().get_first_node_in_group("level_manager")
	var patient := _find_first("ward_5_bed_1_patient_v3") as Node3D
	if not patient or not patient.visible or not levels:
		return
	levels._set_patient_visible("ward_5_bed_1_patient_v3", false)
	_state().set_patient_count(int(_state().patient_count) - 1)
	get_tree().create_timer(EMPTY_BED_SECONDS, false).timeout.connect(_restore_empty_bed)

func _restore_empty_bed() -> void:
	if not is_inside_tree():
		return
	var levels := get_tree().get_first_node_in_group("level_manager")
	var patient := _find_first("ward_5_bed_1_patient_v3") as Node3D
	var state := _state()
	if not levels or not patient or patient.visible or not state or bool(state.get_flag("ending_requested", false)):
		return
	levels._set_patient_visible("ward_5_bed_1_patient_v3", true)
	state.set_patient_count(int(state.patient_count) + 1)

func spawn_normal_orderly() -> void:
	var hospital := _hospital()
	if not hospital or hospital.get_node_or_null("normal_orderly"):
		return
	_spawn_orderly_ghost("normal_orderly", false)

func spawn_hostile_orderly() -> Node3D:
	var hospital := _hospital()
	if not hospital:
		return null
	var existing := hospital.get_node_or_null("hostile_orderly")
	if existing:
		return existing
	if _danger_active():
		# Two lethal encounters never overlap, but a story beat that asked for
		# this one must not be dropped: it arrives once the current danger ends.
		hostile_pending = true
		return null
	var actor := CharacterBody3D.new()
	actor.name = "hostile_orderly"
	actor.set_script(ORDERLY_ENEMY_SCRIPT)
	actor.collision_layer = 2
	actor.collision_mask = 1
	actor.position = Vector3(17.5, 0.04, 0.0)
	var collision := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.38
	capsule.height = 1.78
	collision.shape = capsule
	collision.position.y = 0.89
	actor.add_child(collision)
	var model := ORDERLY_GHOST_SCENE.instantiate() as Node3D
	if not model:
		return null
	model.name = "Model"
	actor.add_child(model)
	hospital.add_child(actor)
	_apply_orderly_materials(model)
	actor.call("setup", model)
	var hud := get_tree().get_first_node_in_group("hud")
	if hud:
		hud.show_message(tr("Санитарка вернулась. Не попадайтесь под красный взгляд — прячьтесь за дверями."), 5.0)
	return actor

func spawn_head_nurse_inspector(reason := "medical_error") -> Node3D:
	var hospital := _hospital()
	if not hospital:
		return null
	var existing := hospital.get_node_or_null("head_nurse_inspector")
	if existing:
		return existing
	var actor := CharacterBody3D.new()
	actor.name = "head_nurse_inspector"
	actor.set_script(ORDERLY_ENEMY_SCRIPT)
	actor.set("patrol_speed", 1.95)
	actor.set("beam_color", Color(0.02, 0.32, 1.0))
	actor.set("enemy_title", tr("главной медсестры"))
	actor.set("enemy_kind", "head_nurse")
	actor.set("safe_in_doctors_room", true)
	actor.set("corridor_only_damage", false)
	actor.set("sight_distance", 15.5)
	actor.set("lifetime_limit", 58.0)
	actor.set("sanity_damage", 3)
	actor.set("health_damage", 0)
	actor.set("max_sanity_damage_total", 18)
	actor.set("minimum_sanity_after_attack", 5)
	actor.set("recovery_hint_on_exit", true)
	actor.set("eye_height", 1.88)
	actor.collision_layer = 2
	actor.collision_mask = 1
	actor.position = Vector3(-17.5, 0.04, 0.0)
	var collision := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.43
	capsule.height = 2.08
	collision.shape = capsule
	collision.position.y = 1.04
	actor.add_child(collision)
	var model := ORDERLY_GHOST_SCENE.instantiate() as Node3D
	if not model:
		return null
	model.name = "Model"
	model.scale = Vector3(1.18, 1.18, 1.18)
	for node in _all_nodes(model):
		if node is Node3D and "bucket" in String(node.name).to_lower():
			(node as Node3D).visible = false
	actor.add_child(model)
	hospital.add_child(actor)
	actor.add_to_group("head_nurse_inspectors")
	_apply_orderly_materials(model, Color(0.02, 0.32, 1.0))
	actor.call("setup", model)
	var hud := get_tree().get_first_node_in_group("hud")
	if hud:
		if reason == "inspection":
			# Scheduled rounds (nights 4, 8, 10, 11) are not a reaction to a mistake.
			hud.show_message(tr("Главная медсестра начала обход. Синий взгляд отнимает рассудок — спрячьтесь в ОРДИНАТОРСКОЙ."), 6.0)
		else:
			hud.show_message(tr("Врачебная ошибка зарегистрирована. Главная медсестра идёт по коридору. Синий взгляд отнимает рассудок — спрячьтесь в ОРДИНАТОРСКОЙ."), 6.0)
	var audio := _audio()
	if audio and audio.has_method("play_anomaly_sting"):
		audio.play_anomaly_sting("главная_медсестра")
	return actor

func request_head_nurse_inspector(reason := "medical_error") -> void:
	if _hospital() and _hospital().get_node_or_null("head_nurse_inspector"):
		return
	# A real mistake outranks a scheduled round that is still waiting.
	if not head_nurse_pending or reason == "medical_error":
		head_nurse_reason = reason
	head_nurse_pending = true
	if not _danger_active():
		head_nurse_pending = false
		spawn_head_nurse_inspector(head_nurse_reason)

func _danger_active() -> bool:
	return not get_tree().get_nodes_in_group("violent_patients").is_empty() or not get_tree().get_nodes_in_group("hostile_orderlies").is_empty()

func _apply_sanity_impact(id: String) -> void:
	var director := get_tree().get_first_node_in_group("game_director")
	if not director or not director.started:
		return
	var player := get_tree().get_first_node_in_group("player")
	if not player or not player.has_method("take_sanity_damage"):
		return
	var category := String(DEFINITIONS[id].category)
	var amount := 3
	if category == "PATIENT":
		amount = 5
	elif category in ["SPATIAL", "SIGNAL"]:
		amount = 7
	elif category == "DANGEROUS":
		amount = 10
	# The event is allowed to affect the player immediately, but the HUD must not
	# hand out the solution/name before the player sees or hears the source.
	# Specific names are exposed by the interaction/observation that discovers it.
	player.take_sanity_damage(amount, tr("что-то не так в отделении"), "anomaly")

func _spawn_violent_patient() -> Node3D:
	var hospital := _hospital()
	if not hospital or hospital.get_node_or_null("violent_patient"):
		return null
	var actor := CharacterBody3D.new()
	actor.name = "violent_patient"
	actor.set_script(VIOLENT_PATIENT_SCRIPT)
	actor.collision_layer = 2
	actor.collision_mask = 1
	actor.position = Vector3(-11.0, 0.05, 0.0)
	var collision := CollisionShape3D.new()
	collision.name = "PatientCollision"
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.36
	capsule.height = 1.72
	collision.shape = capsule
	collision.position.y = 0.86
	actor.add_child(collision)
	var interaction_area := Area3D.new()
	interaction_area.name = "RestraintInteractionArea"
	interaction_area.collision_layer = 1
	interaction_area.collision_mask = 0
	var interaction_collision := CollisionShape3D.new()
	var interaction_shape := CapsuleShape3D.new()
	interaction_shape.radius = 0.58
	interaction_shape.height = 1.92
	interaction_collision.shape = interaction_shape
	interaction_collision.position.y = 0.96
	interaction_area.add_child(interaction_collision)
	actor.add_child(interaction_area)
	var model := VIOLENT_PATIENT_SCENE.instantiate() as Node3D
	if not model:
		return null
	model.name = "Model"
	actor.add_child(model)
	hospital.add_child(actor)
	actor.call("setup", model)
	var hud := get_tree().get_first_node_in_group("hud")
	if hud:
		hud.show_message(tr("Из процедурной слышны крики и удары по металлу."), 4.0)
	return actor

func _spawn_orderly_ghost(node_name: String, wrong_bucket: bool) -> Node3D:
	var hospital := _hospital()
	if not hospital:
		return null
	var orderly := ORDERLY_GHOST_SCENE.instantiate() as Node3D
	if not orderly:
		return null
	orderly.name = node_name
	orderly.position = Vector3(-18.0, 0.025, 0.0)
	hospital.add_child(orderly)
	_apply_orderly_materials(orderly)
	if wrong_bucket:
		_recolor_orderly_bucket(orderly, Color(0.48, 0.012, 0.008))
	_animate_orderly_ghost(orderly)
	var travel := orderly.create_tween()
	travel.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	travel.tween_property(orderly, "position:x", 18.0, 22.0)
	travel.tween_callback(orderly.queue_free)
	return orderly

func _animate_orderly_ghost(orderly: Node3D) -> void:
	for node in _all_nodes(orderly):
		if node is AnimationPlayer:
			var animation_player := node as AnimationPlayer
			for animation_name in animation_player.get_animation_list():
				if animation_name == &"RESET":
					continue
				var animation := animation_player.get_animation(animation_name)
				if animation:
					animation.loop_mode = Animation.LOOP_LINEAR
				animation_player.play(animation_name)
				return
	var left_leg := orderly.find_child("ghost_l_leg_pivot", true, false) as Node3D
	var right_leg := orderly.find_child("ghost_r_leg_pivot", true, false) as Node3D
	var left_arm := orderly.find_child("ghost_l_arm_pivot", true, false) as Node3D
	var right_arm := orderly.find_child("ghost_r_arm_pivot", true, false) as Node3D
	var body := orderly.find_child("ghost_body_pivot", true, false) as Node3D
	var head := orderly.find_child("ghost_head_pivot", true, false) as Node3D
	var bucket := orderly.find_child("ghost_bucket_pivot", true, false) as Node3D
	var gait := orderly.create_tween().set_loops()
	gait.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT).set_parallel(true)
	if left_leg:
		gait.tween_property(left_leg, "rotation:z", deg_to_rad(23.0), 0.48).from(deg_to_rad(-23.0))
	if right_leg:
		gait.tween_property(right_leg, "rotation:z", deg_to_rad(-23.0), 0.48).from(deg_to_rad(23.0))
	if left_arm:
		gait.tween_property(left_arm, "rotation:z", deg_to_rad(-20.0), 0.48).from(deg_to_rad(20.0))
	if right_arm:
		gait.tween_property(right_arm, "rotation:z", deg_to_rad(7.0), 0.48).from(deg_to_rad(-7.0))
	if head:
		gait.tween_property(head, "rotation:z", deg_to_rad(4.0), 0.48).from(deg_to_rad(-4.0))
	if bucket:
		gait.tween_property(bucket, "rotation:z", deg_to_rad(-5.0), 0.48).from(deg_to_rad(5.0))
	gait.chain().set_parallel(true)
	if left_leg:
		gait.tween_property(left_leg, "rotation:z", deg_to_rad(-23.0), 0.48)
	if right_leg:
		gait.tween_property(right_leg, "rotation:z", deg_to_rad(23.0), 0.48)
	if left_arm:
		gait.tween_property(left_arm, "rotation:z", deg_to_rad(20.0), 0.48)
	if right_arm:
		gait.tween_property(right_arm, "rotation:z", deg_to_rad(-7.0), 0.48)
	if head:
		gait.tween_property(head, "rotation:z", deg_to_rad(-4.0), 0.48)
	if bucket:
		gait.tween_property(bucket, "rotation:z", deg_to_rad(5.0), 0.48)
	if body:
		var base_y := body.position.y
		var bob := orderly.create_tween().set_loops()
		bob.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
		bob.tween_property(body, "position:y", base_y + 0.035, 0.24)
		bob.tween_property(body, "position:y", base_y, 0.24)

func _recolor_orderly_bucket(orderly: Node3D, color: Color) -> void:
	for node in _all_nodes(orderly):
		if node is MeshInstance3D and "ghost_blue_bucket_body" in String(node.name).to_lower():
			var material := StandardMaterial3D.new()
			material.albedo_color = color
			material.roughness = 0.48
			material.metallic = 0.28
			node.material_override = material

func _elevator_minus_one() -> void:
	var elevator := _find_first("elevator_unit_v2")
	if not elevator:
		return
	var label := Label3D.new()
	label.name = "ANOMALY_ELEVATOR_MINUS_ONE"
	label.text = "-1"
	label.font_size = 72
	label.modulate = Color(0.8, 0.04, 0.02)
	label.position = Vector3(0.0, 2.0, 0.0)
	elevator.add_child(label)

func _wrong_door_label() -> void:
	var door := _find_first("pivot_hospital_door_N_3")
	if not door:
		return
	var label := Label3D.new()
	label.name = "ANOMALY_WRONG_ROOM_NUMBER"
	label.text = tr("ПАЛАТА 8")
	label.font_size = 36
	label.modulate = Color(0.12, 0.09, 0.05)
	label.position = Vector3(0.0, 1.8, -0.14)
	door.add_child(label)

func _spawn_figure(id: String, position: Vector3, scale_factor: float, color := Color(0.28, 0.34, 0.33), lifetime := 18.0) -> Node3D:
	var root := Node3D.new()
	root.name = id
	root.position = position
	root.scale = Vector3.ONE * scale_factor
	_hospital().add_child(root)
	var body := MeshInstance3D.new()
	var capsule := CapsuleMesh.new()
	capsule.radius = 0.28
	capsule.height = 1.35
	body.mesh = capsule
	body.position.y = 0.85
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = 0.95
	body.material_override = material
	root.add_child(body)
	var head := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 0.22
	sphere.height = 0.44
	head.mesh = sphere
	head.position.y = 1.65
	head.material_override = material
	root.add_child(head)
	if lifetime > 0.0:
		var departure := root.create_tween()
		departure.tween_interval(lifetime)
		departure.tween_property(root, "scale", Vector3.ZERO, 0.8)
		departure.tween_callback(root.queue_free)
	return root

func _recolor_first(partial: String, color: Color) -> void:
	var node := _find_first(partial)
	if node is MeshInstance3D:
		var material := StandardMaterial3D.new()
		material.albedo_color = color
		material.roughness = 0.55
		node.material_override = material

func _room_zero() -> void:
	var source := _find_first("pivot_hospital_door_N_3")
	if source:
		# Default flags: the copy has to keep door.gd. With instantiation alone
		# the script was dropped, the door could not be opened and the room_zero
		# ending was unreachable.
		var copy := source.duplicate()
		source.get_parent().add_child(copy)
		copy.name = "ANOMALY_ROOM_ZERO"
		copy.global_position = Vector3(15.0, 0.0, -1.55)
		if "closed_rotation" in source:
			copy.rotation = source.closed_rotation
		# Runtime state is not duplicated; configure the copy as a fresh, closed,
		# unlocked door at its own rotation.
		copy.set("configured", false)
		copy.set("opened", false)
		copy.set("locked", false)
		if copy.has_method("setup_from_import"):
			copy.setup_from_import()
		copy.set_meta("room_zero", true)

func _long_corridor() -> void:
	# The corridor "stretches" for the player instead of in the level. Moving
	# the east wing apart used to push every node with x > 9 again after its
	# parent had already moved, tearing colliders and interaction volumes up to
	# 50 m away from what they belong to, and the corridor floor does not extend
	# past the end wall anyway - mops, restraints, fuses and the extinguisher
	# became unusable and several nights unfinishable. A dolly-zoom and a slower
	# walk in the corridor sell the same anomaly without touching reachability.
	var player := get_tree().get_first_node_in_group("player")
	if not player or not player.has_method("set_corridor_stretch"):
		return
	player.set_corridor_stretch(1.0)
	long_corridor_running = true
	get_tree().create_timer(LONG_CORRIDOR_SECONDS, false).timeout.connect(_end_long_corridor)

func _end_long_corridor() -> void:
	if not is_inside_tree():
		return
	long_corridor_running = false
	var player := get_tree().get_first_node_in_group("player")
	if player and player.has_method("set_corridor_stretch"):
		player.set_corridor_stretch(0.0)

func _move_named_parts(partial: String, offset: Vector3, duration: float) -> void:
	# Only the outermost matching node moves; its parts follow as children.
	# Offsetting every match compounded down the hierarchy (48 of the
	# wheelchair's 49 nodes are nested) and pulled the model apart.
	var roots: Array[Node3D] = []
	_collect_named_roots(_hospital(), partial.to_lower(), roots)
	if roots.is_empty():
		return
	var tween := create_tween().set_parallel(true)
	for node in roots:
		tween.tween_property(node, "position", node.position + offset, duration)

func _collect_named_roots(parent: Node, partial: String, out: Array[Node3D]) -> void:
	if not parent:
		return
	for child in parent.get_children():
		if child is Node3D and partial in String(child.name).to_lower():
			out.append(child as Node3D)
		else:
			_collect_named_roots(child, partial, out)

func _duplicate_named(partial: String, offset: Vector3) -> void:
	var node := _find_first(partial)
	if node and node is Node3D:
		var copy := node.duplicate(Node.DUPLICATE_USE_INSTANTIATION)
		node.get_parent().add_child(copy)
		copy.name = "ANOMALY_DUPLICATE_" + partial.to_upper()
		copy.position += offset

func _scale_first(partial: String, factor: Vector3) -> void:
	var node := _find_first(partial)
	if node is Node3D:
		node.scale *= factor

func _stand_patient() -> void:
	var patient := _find_first("ward_6_bed_2_patient_head")
	if patient is Node3D:
		patient.position += Vector3(0.0, 1.05, -1.0)

func _spawn_note() -> void:
	var note := Label3D.new()
	note.name = "ANOMALY_FALSE_NOTE"
	note.text = tr("Не считай тех, кто спит")
	note.font_size = 36
	note.modulate = Color(0.08, 0.07, 0.05)
	note.position = Vector3(2.5, 1.58, -2.7)
	note.rotation_degrees.x = -90.0
	_hospital().add_child(note)

func _start_phone_call(type: String) -> void:
	var phone := get_tree().get_first_node_in_group("hospital_phone")
	if phone:
		phone.start_call(type)
	else:
		_state().set_flag("pending_phone_call", type)
