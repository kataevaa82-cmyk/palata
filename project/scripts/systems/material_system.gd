extends Node

var shader: Shader
var matte_shader: Shader
var mobile_shader: Shader

# Categories whose surfaces are worth a specular highlight: linoleum and tile,
# painted metal and chrome, ceramic. Everything else runs the matte build.
const GLOSSY_PATTERNS := [1, 4, 5]
var cache: Dictionary = {}
var mobile_mode := false

func _ready() -> void:
	add_to_group("material_system")
	var platform := get_tree().get_first_node_in_group("yandex_sdk")
	mobile_mode = platform and platform.is_mobile_device()
	# One body, two builds: see GLOSSY_PATTERNS below.
	var surface_code := """
shader_type spatial;
render_mode RENDER_MODE_LINE;

uniform vec4 base_color : source_color = vec4(0.5, 0.5, 0.5, 1.0);
uniform vec4 secondary_color : source_color = vec4(0.4, 0.4, 0.4, 1.0);
uniform vec4 detail_color : source_color = vec4(0.25, 0.25, 0.25, 1.0);
uniform float texture_scale = 1.0;
uniform float material_roughness = 0.7;
uniform float material_metallic = 0.0;
uniform float grime_strength = 0.55;
uniform float wear_strength = 0.55;
uniform int pattern = 0;
varying vec3 world_pos;

float hash31(vec3 p) {
	p = fract(p * 0.1031);
	p += dot(p, p.yzx + 33.33);
	return fract((p.x + p.y) * p.z);
}

float value_noise(vec3 p) {
	vec3 i = floor(p);
	vec3 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hash31(i), hash31(i + vec3(1,0,0)), f.x),
	               mix(hash31(i + vec3(0,1,0)), hash31(i + vec3(1,1,0)), f.x), f.y),
	           mix(mix(hash31(i + vec3(0,0,1)), hash31(i + vec3(1,0,1)), f.x),
	               mix(hash31(i + vec3(0,1,1)), hash31(i + vec3(1,1,1)), f.x), f.y), f.z);
}

// Three octaves, not four. Each octave is eight hash31() calls, and the fourth
// carried an amplitude of 0.069 out of 1.03 - under 7% of the result, for 25% of
// the cost of every fbm() in the frame. The lost amplitude is folded back into
// the first two so the overall contrast is unchanged.
float fbm(vec3 p) {
	float v = 0.0;
	float a = 0.585;
	for (int i = 0; i < 3; i++) {
		v += value_noise(p) * a;
		p = p * 2.03 + vec3(7.1, 3.7, 5.4);
		a *= 0.5;
	}
	return v;
}

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 p = world_pos * texture_scale;
	float n = fbm(p);
	float fine = fbm(p * 4.1 + vec3(8.0, 2.0, 13.0));
	float grime = smoothstep(0.57, 0.88, fbm(p * 0.55 + vec3(17.0, 4.0, 9.0))) * grime_strength;
	float ground_grime = (1.0 - smoothstep(0.05, 1.15, world_pos.y)) * grime_strength;
	vec3 color = mix(base_color.rgb, secondary_color.rgb, n * 0.34);
	float rough = material_roughness;
	float metal = material_metallic;

	if (pattern == 0) {
		float peel = smoothstep(0.77, 0.93, fbm(p * 1.75 + vec3(4.0))) * wear_strength;
		float crack_line = 1.0 - smoothstep(0.018, 0.055, abs(fbm(p * 3.8) - 0.52));
		crack_line *= smoothstep(0.56, 0.86, fine) * wear_strength;
		color = mix(color, detail_color.rgb, peel * 0.44 + crack_line * 0.62);
		color *= 1.0 - max(grime * 0.24, ground_grime * 0.40);
		rough = clamp(rough + n * 0.16 + peel * 0.12, 0.0, 1.0);
	} else if (pattern == 1) {
		vec2 tile = abs(fract(world_pos.xz * vec2(0.72, 0.58)) - 0.5);
		float seam = 1.0 - smoothstep(0.455, 0.490, max(tile.x, tile.y));
		float slab_seed = hash31(vec3(floor(world_pos.x * 0.72), floor(world_pos.z * 0.58), 3.0));
		float stone_mottle = fbm(vec3(world_pos.x * 1.2, world_pos.z * 0.2, world_pos.z * 1.2));
		float hairline = 1.0 - smoothstep(0.012, 0.038, abs(fbm(vec3(world_pos.xz * 2.7, 4.0)) - 0.51));
		float scuff = smoothstep(0.70, 0.91, fbm(vec3(world_pos.x * 2.2, world_pos.z * 0.16, world_pos.z * 2.2)));
		float black_stain = smoothstep(0.79, 0.94, fbm(vec3(world_pos.x * 0.55, 3.0, world_pos.z * 0.55)));
		color = mix(base_color.rgb * (0.86 + slab_seed * 0.18), secondary_color.rgb, stone_mottle * 0.30);
		color = mix(color, detail_color.rgb, seam * 0.72 + hairline * wear_strength * 0.20 + scuff * 0.11);
		color *= 1.0 - black_stain * grime_strength * 0.18;
		rough = 0.78 + n * 0.17;
	} else if (pattern == 2) {
		float grain = 0.5 + 0.5 * sin((world_pos.x + world_pos.z * 0.23 + world_pos.y * 0.06) * 38.0 + n * 8.0);
		float gouge = smoothstep(0.82, 0.96, fine) * wear_strength;
		color = mix(base_color.rgb * 0.70, secondary_color.rgb * 1.08, grain * 0.58);
		color = mix(color, detail_color.rgb, gouge * 0.34 + grime * 0.18);
		rough = 0.58 + n * 0.24;
	} else if (pattern == 3) {
		float weave = (sin(world_pos.x * 125.0) * sin(world_pos.z * 125.0)) * 0.5 + 0.5;
		float old_stain = smoothstep(0.67, 0.88, fbm(p * 0.62 + vec3(3.0, 19.0, 1.0)));
		color *= 0.82 + weave * 0.16;
		color = mix(color, detail_color.rgb, old_stain * grime_strength * 0.48);
		rough = 0.93;
	} else if (pattern == 4) {
		float chip = smoothstep(0.76, 0.91, fbm(p * 2.7)) * wear_strength;
		float rust = smoothstep(0.64, 0.88, fbm(p * 1.12 + vec3(14.0, 3.0, 5.0))) * chip;
		float scratch = 1.0 - smoothstep(0.02, 0.065, abs(fract((world_pos.x + world_pos.y * 0.08) * 17.0 + fine) - 0.5));
		color = mix(color, detail_color.rgb, chip * 0.54);
		color = mix(color, vec3(0.24, 0.055, 0.018), rust * 0.76);
		color = mix(color, secondary_color.rgb * 1.18, scratch * wear_strength * 0.13);
		rough = mix(material_roughness, 0.96, max(chip, rust));
		metal = mix(material_metallic, 0.42, chip);
	} else if (pattern == 5) {
		float age = smoothstep(0.65, 0.91, fbm(p * 1.4 + vec3(8.0)));
		float crack = 1.0 - smoothstep(0.016, 0.045, abs(fbm(p * 5.0) - 0.50));
		color *= 0.91 + n * 0.10;
		color = mix(color, detail_color.rgb, age * grime_strength * 0.35 + crack * wear_strength * 0.31);
		rough = 0.46 + n * 0.20;
	} else if (pattern == 6) {
		float dust = smoothstep(0.62, 0.91, fbm(p * 1.7 + vec3(11.0, 2.0, 7.0)));
		float worn = smoothstep(0.76, 0.97, fbm(p * 5.2));
		color *= 0.84 + n * 0.18;
		color = mix(color, detail_color.rgb, dust * grime_strength * 0.40 + worn * wear_strength * 0.14);
		rough = clamp(rough + 0.12 + n * 0.12, 0.0, 1.0);
	} else if (pattern == 7) {
		float broad_peel = smoothstep(0.69, 0.88, fbm(p * 1.18 + vec3(21.0, 7.0, 2.0)));
		float fine_peel = smoothstep(0.77, 0.92, fine);
		float peel = max(broad_peel * 0.82, fine_peel * 0.48) * wear_strength;
		float scratch = smoothstep(0.84, 0.965, fbm(p * 5.6 + vec3(13.0, 4.0, 19.0)));
		float wood_grain = fbm(p * 3.2 + vec3(2.0, 17.0, 6.0));
		vec3 aged_paint = mix(base_color.rgb, secondary_color.rgb, n * 0.38);
		vec3 exposed_wood = mix(detail_color.rgb * 0.66, detail_color.rgb * 1.20, wood_grain);
		color = mix(aged_paint, exposed_wood, peel);
		color = mix(color, exposed_wood * 0.72, scratch * wear_strength * 0.15);
		color *= 1.0 - max(grime * 0.18, ground_grime * 0.46);
		rough = clamp(0.74 + peel * 0.22 + n * 0.08, 0.0, 1.0);
		metal = 0.0;
	}

	ALBEDO = color;
	ROUGHNESS = clamp(rough, 0.05, 1.0);
	METALLIC = clamp(metal, 0.0, 1.0);
}
"""
	shader = Shader.new()
	shader.code = surface_code.replace("RENDER_MODE_LINE", "diffuse_burley, specular_schlick_ggx")
	matte_shader = Shader.new()
	matte_shader.code = surface_code.replace("RENDER_MODE_LINE", "diffuse_lambert, specular_disabled")
	mobile_shader = Shader.new()
	mobile_shader.code = """
shader_type spatial;
render_mode diffuse_lambert, specular_schlick_ggx;

uniform vec4 base_color : source_color = vec4(0.5, 0.5, 0.5, 1.0);
uniform float material_roughness = 0.8;
uniform float material_metallic = 0.0;

void fragment() {
	ALBEDO = base_color.rgb;
	ROUGHNESS = material_roughness;
	METALLIC = material_metallic;
}
"""

func apply_to_hospital(hospital: Node) -> int:
	var changed := 0
	for node in _all_nodes(hospital):
		if node is MeshInstance3D and node.mesh:
			for surface in node.mesh.get_surface_count():
				var source: Material = node.mesh.surface_get_material(surface)
				if not source:
					continue
				var category: int = _category_for(String(node.name).to_lower(), String(source.resource_name).to_lower())
				if category < 0:
					continue
				var replacement := _mobile_material(source, category) if mobile_mode else _textured_material(source, category)
				node.set_surface_override_material(surface, replacement)
				changed += 1
	print("MATERIALS_TEXTURED surfaces=", changed, " mobile=", mobile_mode)
	return changed

func _all_nodes(root_node: Node) -> Array[Node]:
	var result: Array[Node] = [root_node]
	for child in root_node.get_children():
		result.append_array(_all_nodes(child))
	return result

func _category_for(object_name: String, name: String) -> int:
	# Preserve the authored strand colours and roughness on the patient hair.
	if name.begins_with("mat_patient_hair_groom"):
		return -1
	if _is_old_wooden_door(object_name):
		return 7
	if "glass" in name or "window" in name or "water" in name or "mirror" in name or "screen" in name or "emiss" in name or "light" in name or "glow" in name or "eye" in name:
		return -1
	if "whitewash" in name or "oil_paint_green" in name or "repainted_mint" in name or "wall_repair" in name or "ceiling" in name:
		return 0
	if "linoleum" in name or "worn_floor" in name or "wheel_scuff" in name or "marble" in name or "stone" in name:
		return 1
	if "painted_wood" in name or "offwhite" in name:
		return 7
	if "veneer" in name or "old_dsp" in name or "tv_dark_wood" in name or "wood" in name:
		return 2
	if "linen" in name or "blanket" in name or "chair_vinyl" in name or "green_vinyl" in name or "gown" in name or "apron" in name or "scarf" in name or "bandage" in name or "curtain" in name or "towel" in name or "robe" in name or "cloth" in name or "fabric" in name:
		return 3
	if "painted_metal" in name or "fire_door_metal" in name or "painted_wood" in name or "old_enamel" in name or "chipped_white" in name or "lamp_housing" in name or "metal" in name or "chrome" in name or "steel" in name or "iron" in name or "bucket" in name or "pipe" in name or "hinge" in name or "rust" in name:
		return 4
	if "ceramic" in name or "porcelain" in name or "square_tile" in name:
		return 5
	return 6

func _is_old_wooden_door(object_name: String) -> bool:
	return (
		object_name.begins_with("hospital_door_")
		or object_name.begins_with("doorframe_")
		or object_name.begins_with("door_detail")
		or "anomaly_room_zero_door" in object_name
	)

func _palette_color(name: String, fallback: Color, category: int) -> Color:
	# Imported GLB materials often expose a neutral albedo even when their Blender
	# shader has a colored ramp. Recover the intended hospital palette from the
	# stable material name before applying the procedural aging pattern.
	if category == 7:
		return Color(0.72, 0.70, 0.59)
	if "old_whitewash" in name or "ceiling" in name or "chipped_white" in name:
		return Color(0.58, 0.59, 0.50)
	if "oil_paint_green" in name or "repainted_mint" in name or "wall_repair" in name:
		return Color(0.20, 0.34, 0.27)
	if "skirting" in name:
		return Color(0.105, 0.19, 0.145)
	if "linoleum" in name or "worn_floor" in name or "wheel_scuff" in name or "marble" in name or "stone" in name:
		return Color(0.33, 0.35, 0.30)
	if "veneer" in name or "old_dsp" in name or "painted_wood" in name or "wood" in name or "coffee" in name:
		return Color(0.27, 0.135, 0.055)
	if "pillow" in name:
		# Must come before the linen rule below: the mattress is linen too, and
		# sharing its colour made the pillow disappear into the bed it lies on.
		# A pillowcase is the one piece of bedding still meant to look laundered.
		return Color(0.62, 0.63, 0.55)
	if "blanket" in name or "gown" in name or "linen" in name or "apron" in name or "curtain" in name or "towel" in name or "scarf" in name:
		return Color(0.255, 0.315, 0.275)
	if "skin" in name:
		return Color(0.62, 0.43, 0.31)
	if "hair" in name or "rubber" in name or "black" in name or "ink" in name:
		return Color(0.075, 0.065, 0.050)
	if "red" in name or "warning" in name or "hot_mark" in name:
		return Color(0.52, 0.055, 0.035)
	if "blue" in name or "bucket" in name or "cold_faded" in name or "cold_mark" in name:
		return Color(0.08, 0.22, 0.34)
	if "glass" in name or "water" in name:
		return fallback
	if "metal" in name or "chrome" in name or "steel" in name or "iron" in name or "pipe" in name:
		return Color(0.265, 0.29, 0.255)
	if "porcelain" in name or "ceramic" in name or "tile" in name or "enamel" in name:
		return Color(0.67, 0.65, 0.52)
	if "plastic" in name:
		return Color(0.38, 0.35, 0.265)
	return fallback

func _textured_material(source: Material, category: int) -> ShaderMaterial:
	var key := "%s:%d" % [source.resource_name, category]
	if cache.has(key):
		return cache[key]
	var color := Color(0.5, 0.5, 0.5)
	var roughness := 0.7
	var metallic := 0.0
	if source is BaseMaterial3D:
		color = source.albedo_color
		roughness = source.roughness
		metallic = source.metallic
	color = _palette_color(source.resource_name.to_lower(), color, category)
	var secondary := color.darkened(0.12)
	var detail := color.darkened(0.34)
	var grime_strength := 0.55
	var wear_strength := 0.58
	if category == 0:
		secondary = color.lightened(0.06)
		detail = Color(0.12, 0.14, 0.105)
		grime_strength = 0.70
	elif category == 1:
		secondary = Color(0.58, 0.57, 0.49)
		detail = Color(0.085, 0.09, 0.075)
		grime_strength = 0.62
	elif category == 4:
		secondary = color.lightened(0.11)
		detail = Color(0.25, 0.075, 0.025)
		grime_strength = 0.65
	elif category == 5:
		secondary = color.lightened(0.08)
		detail = Color(0.24, 0.205, 0.11)
	elif category == 7:
		secondary = Color(0.52, 0.52, 0.42)
		detail = Color(0.255, 0.12, 0.045)
		grime_strength = 0.72
		wear_strength = 0.82
	var material := ShaderMaterial.new()
	material.shader = shader if category in GLOSSY_PATTERNS else matte_shader
	material.resource_name = source.resource_name + "_textured"
	material.set_shader_parameter("base_color", color)
	material.set_shader_parameter("secondary_color", secondary)
	material.set_shader_parameter("detail_color", detail)
	material.set_shader_parameter("texture_scale", [0.52, 1.0, 1.15, 1.7, 1.35, 1.4, 1.25, 0.92][category])
	material.set_shader_parameter("material_roughness", roughness)
	material.set_shader_parameter("material_metallic", metallic)
	material.set_shader_parameter("grime_strength", grime_strength)
	material.set_shader_parameter("wear_strength", wear_strength)
	material.set_shader_parameter("pattern", category)
	cache[key] = material
	return material

func _mobile_material(source: Material, category: int) -> ShaderMaterial:
	# The desktop shader evaluates several layers of procedural noise for every
	# pixel. On mobile WebGL that is the largest GPU cost in the scene, so the
	# touch build keeps the same palette and material response with a flat shader.
	var key := "mobile:%s:%d" % [source.resource_name, category]
	if cache.has(key):
		return cache[key]
	var color := Color(0.5, 0.5, 0.5)
	var roughness := 0.8
	var metallic := 0.0
	if source is BaseMaterial3D:
		color = source.albedo_color
		roughness = source.roughness
		metallic = source.metallic
	color = _palette_color(source.resource_name.to_lower(), color, category)
	var material := ShaderMaterial.new()
	material.shader = mobile_shader
	material.resource_name = source.resource_name + "_mobile"
	material.set_shader_parameter("base_color", color)
	material.set_shader_parameter("material_roughness", maxf(roughness, 0.62))
	material.set_shader_parameter("material_metallic", metallic)
	cache[key] = material
	return material
