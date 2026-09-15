extends Node3D

signal hospital_ready

const DOOR_SCRIPT := preload("res://scripts/interaction/door.gd")
const SWITCH_SCRIPT := preload("res://scripts/interaction/light_switch.gd")
const PHONE_SCRIPT := preload("res://scripts/interaction/phone.gd")
const DOCUMENT_SCRIPT := preload("res://scripts/interaction/document.gd")
const EXIT_SCRIPT := preload("res://scripts/interaction/exit_door.gd")
const ELEVATOR_SCRIPT := preload("res://scripts/interaction/elevator.gd")
const INTERACTIVE_PROP_SCRIPT := preload("res://scripts/interaction/interactive_prop.gd")
const CARE_INTERACTABLE_SCRIPT := preload("res://scripts/interaction/care_interactable.gd")
const PATIENT_INTERACTION_SCRIPT := preload("res://scripts/interaction/patient_interaction.gd")

const CARE_PROP_IDS := {
	"interaction_assignment_board": "assignment_board",
	"interaction_med_aminazine": "med_aminazine",
	"interaction_med_cordiamin": "med_cordiamin",
	"interaction_med_bandage": "med_bandage",
	"interaction_med_saline": "med_saline",
	"interaction_med_stethoscope": "med_stethoscope",
	"interaction_med_thermometer": "med_thermometer",
	"interaction_patient_restraints": "patient_restraints",
	"interaction_doctors_computer": "doctors_computer",
	"interaction_clean_linen": "clean_linen",
	"interaction_laundry_basket": "laundry_basket",
	"interaction_mop_bucket": "mop_bucket",
	"interaction_water_spill": "water_spill",
	"interaction_fire_exit_seal": "fire_exit_seal",
	"interaction_elevator_inspection": "elevator_inspection"
}

# Props belonging to the ten extra nights (tools/build_level_props.py). All of
# them ship in the same GLB; every one is hidden and de-collided at load and
# only the selected night's whitelist is switched back on by LevelManager. The
# list is kept here rather than read from a Blender custom property so the
# binding cannot silently break on a re-export.
const LEVEL_PROP_IDS := {
	"interaction_fuse_box": "fuse_box",
	"interaction_spare_fuses": "spare_fuses",
	"interaction_emergency_lamp": "emergency_lamp",
	"interaction_oxygen_pillow": "oxygen_pillow",
	"interaction_quarantine_curtain": "quarantine_curtain",
	"interaction_mask_box": "mask_box",
	"interaction_hand_sanitizer": "hand_sanitizer",
	"interaction_sample_tube": "sample_tube",
	"interaction_gurney": "gurney",
	"interaction_body_bag": "body_bag",
	"interaction_death_certificate": "death_certificate",
	"interaction_blood_fridge": "blood_fridge",
	"interaction_blood_bag_first": "blood_bag_first",
	"interaction_blood_bag_second": "blood_bag_second",
	"interaction_blood_bag_third": "blood_bag_third",
	"interaction_blood_chart": "blood_chart",
	"interaction_radiator_key": "radiator_key",
	"interaction_blanket_stack": "blanket_stack",
	"interaction_radiator_valve": "radiator_valve",
	"interaction_window_latch": "window_latch",
	"interaction_tea_kettle": "tea_kettle",
	"interaction_hospital_slippers": "hospital_slippers",
	"interaction_muddy_trail": "muddy_trail",
	"interaction_bed_note": "bed_note",
	"interaction_escaped_patient": "escaped_patient",
	"interaction_duty_journal_form": "duty_journal_form",
	"interaction_misplaced_chair": "misplaced_chair",
	"interaction_floor_dirt": "floor_dirt",
	"interaction_fire_extinguisher": "fire_extinguisher",
	"interaction_smoke_source": "smoke_source",
	"interaction_fire_alarm_panel": "fire_alarm_panel",
	"interaction_sterile_bix": "sterile_bix",
	"interaction_surgical_lamp": "surgical_lamp",
	"interaction_surgical_gown": "surgical_gown",
	"interaction_zero_door": "zero_door",
	"interaction_zero_key": "zero_key",
	"interaction_zero_card": "zero_card"
}

# Two level props physically carry another prop the player must also be able to
# aim at: the transport bag lies on the gurney deck, the donor units stand on
# the fridge. A volume fitted to the container's full height swallows the
# smaller prop, and since the interaction ray returns the first collider it
# meets, the container would always win and the contents would be unusable.
# Capping the container's box (in world Y) leaves the top surface to its cargo.
const LEVEL_PROP_VOLUME_CAPS := {
	"gurney": 0.70,
	"blood_fridge": 1.00
}

const PATIENTS := {
	"ward_1_bed_1_patient_v3": ["morozov", "Морозов И. П.", 1, 1],
	"ward_2_bed_1_patient_v3": ["levchenko", "Левченко А. Н.", 2, 1],
	"ward_3_bed_1_patient_v3": ["orlova", "Орлова Н. Д.", 3, 1],
	"ward_4_bed_1_patient_v3": ["saveliev", "Савельев П. М.", 4, 1],
	"ward_5_bed_1_patient_v3": ["demina", "Демина В. Р.", 5, 1],
	"ward_6_bed_1_patient_v3": ["yudin", "Юдин С. К.", 6, 1],
	"ward_6_bed_2_patient_v3": ["klimova", "Климова Т. С.", 6, 2]
}

@onready var hospital: Node3D = $HospitalModel

var prepared := false
var runtime_light_candidate := 0

func _ready() -> void:
	hospital.add_to_group("hospital_model")
	# level_manager reaches the fog through this group when a night thickens the
	# air (smoke on night 9, the cold snap on night 6).
	$WorldEnvironment.add_to_group("world_environment")
	call_deferred("_prepare_imported_hospital")
	var tm := get_tree().get_first_node_in_group("time_manager")
	if tm:
		tm.reached_time.connect(_on_reached_time)
	var state := get_tree().get_first_node_in_group("hospital_state")
	if state:
		state.ending_requested.connect(_on_ending_requested)

func _prepare_imported_hospital() -> void:
	var started_at := Time.get_ticks_msec()
	var nodes := _all_nodes(hospital)
	var collision_count := 0
	for node in nodes:
		var lower := String(node.name).to_lower()
		if node is MeshInstance3D and _needs_collision(lower):
			if _add_box_collision(node):
				collision_count += 1
		if lower.begins_with("pivot_hospital_door") and node is Node3D:
			node.set_script(DOOR_SCRIPT)
			node.setup_from_import()
		if CARE_PROP_IDS.has(lower) and node is Node3D:
			node.set_script(CARE_INTERACTABLE_SCRIPT)
			node.setup_from_import(CARE_PROP_IDS[lower])
			_add_interaction_area(node, String(CARE_PROP_IDS[lower]))
		if LEVEL_PROP_IDS.has(lower) and node is Node3D:
			node.set_script(CARE_INTERACTABLE_SCRIPT)
			node.setup_from_import(LEVEL_PROP_IDS[lower])
			_add_interaction_area(node, String(LEVEL_PROP_IDS[lower]))
			node.add_to_group("level_props")
			(node as Node3D).visible = false
		if PATIENTS.has(lower) and node is Node3D:
			var patient_data: Array = PATIENTS[lower]
			node.set_script(PATIENT_INTERACTION_SCRIPT)
			node.setup_from_import(patient_data[0], patient_data[1], patient_data[2], patient_data[3])
			_add_interaction_area(node, "patient")
		if lower in ["interaction_emergency_button", "interaction_medical_cart"] and node is Node3D:
			node.set_script(INTERACTIVE_PROP_SCRIPT)
			node.setup_from_import()
		if lower.begins_with("soviet_switch") and node is Node3D and not String(node.get_parent().name).to_lower().begins_with("soviet_switch"):
			node.set_script(SWITCH_SCRIPT)
			node.setup_from_import()
		if lower == "telephone_base" and node is Node3D:
			node.set_script(PHONE_SCRIPT)
			node.setup_from_import()
		if lower == "patient_journal" and node is Node3D:
			node.set_script(DOCUMENT_SCRIPT)
			node.setup_from_import("journal")
		if lower == "heavy_fire_door" and node is Node3D:
			node.set_script(EXIT_SCRIPT)
			node.setup_from_import()
		if lower == "elevator_unit_v2" and node is Node3D:
			node.set_script(ELEVATOR_SCRIPT)
			node.setup_from_import()
		if (lower.begins_with("ceiling_lamp_") and "housing" in lower) or lower.begins_with("room_ceiling_fixture"):
			_add_light(node)
	var material_system := get_tree().get_first_node_in_group("material_system")
	if material_system:
		material_system.apply_to_hospital(hospital)
	var levels := get_tree().get_first_node_in_group("level_manager")
	if levels:
		levels.apply_prop_visibility(hospital)
	prepared = true
	print("HOSPITAL_READY nodes=", nodes.size(), " collisions=", collision_count, " ms=", Time.get_ticks_msec() - started_at)
	hospital_ready.emit()
	var hud := get_tree().get_first_node_in_group("hud")
	if hud:
		hud.set_loading_complete()

func _all_nodes(root: Node) -> Array[Node]:
	var out: Array[Node] = [root]
	for child in root.get_children():
		out.append_array(_all_nodes(child))
	return out

func _needs_collision(name_lower: String) -> bool:
	if "outlet" in name_lower or "socket" in name_lower or "door_detail" in name_lower:
		return false
	for decorative in ["wear_decal", "stain", "scuff", "crack", "mount_trace", "poster", "sign_text", "sign_back", "label"]:
		if decorative in name_lower:
			return false
	if name_lower.begins_with("medical_storage_"):
		for solid_part in ["rack_post", "rack_shelf", "supply_crate", "oxygen_cylinder", "oxygen_cradle", "stretcher_canvas", "stretcher_pole", "table_top", "table_leg", "enamel_canister", "window_sill"]:
			if solid_part in name_lower:
				return true
		return false
	# "corridor_n_" / "corridor_s_" are the corridor's own wall panels
	# (corridor_N_3_L_lower, corridor_S_7_R_upper, ...). They carry no "wall" in
	# their name, so they used to match nothing here and the entire corridor was
	# walk-through. The trailing underscore keeps this from catching
	# corridor_sign*, corridor_ceiling or corridor_clock*.
	var architecture := ["floor", "wall", "partition", "door", "counter", "stair_step", "elevator", "interaction_", "corridor_n_", "corridor_s_"]
	for key in architecture:
		if key in name_lower:
			return true
	if "bed_" in name_lower:
		return "mattress" in name_lower or "frame" in name_lower or "headboard" in name_lower or "footboard" in name_lower
	if "desk" in name_lower:
		return "top" in name_lower or "body" in name_lower or "modesty" in name_lower
	if "couch" in name_lower:
		return "frame" in name_lower or "mattress" in name_lower or "headrest" in name_lower
	if "cabinet" in name_lower:
		return "body" in name_lower or "door" in name_lower
	if "sink_unit" in name_lower:
		return "basin" in name_lower or "backplate" in name_lower
	if "toilet" in name_lower:
		return "bowl" in name_lower or "tank" in name_lower
	for key in ["soviet_switch", "telephone_base_heavy_body", "patient_journal"]:
		if key in name_lower:
			return true
	return false

func _add_box_collision(mesh_instance: MeshInstance3D) -> bool:
	if not mesh_instance.mesh or mesh_instance.get_node_or_null("RuntimeCollision"):
		return false
	var bounds := mesh_instance.mesh.get_aabb()
	if bounds.size.length_squared() < 0.000001:
		return false
	var body := StaticBody3D.new()
	body.name = "RuntimeCollision"
	body.collision_layer = 1
	body.collision_mask = 1
	var collision := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = bounds.size
	collision.shape = shape
	collision.position = bounds.get_center()
	body.add_child(collision)
	mesh_instance.add_child(body)
	return true

func _add_interaction_area(root: Node3D, care_id: String) -> void:
	if root.get_node_or_null("CareInteractionArea"):
		return
	var area := Area3D.new()
	area.name = "CareInteractionArea"
	area.collision_layer = 1
	area.collision_mask = 0
	var collision := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	if care_id == "patient":
		shape.size = Vector3(0.95, 0.70, 1.55)
		collision.position = Vector3(0.0, 0.94, 0.0)
	elif care_id == "water_spill":
		shape.size = Vector3(2.15, 0.08, 1.35)
		collision.position = Vector3(0.0, 0.04, 0.0)
	elif care_id in ["assignment_board", "fire_exit_seal", "elevator_inspection"]:
		shape.size = Vector3(0.85, 0.60, 0.35)
	elif LEVEL_PROP_IDS.values().has(care_id):
		# Interaction is a 2.45 m RayCast3D from the camera at eye height, not a
		# proximity check. The old fixed 0.58 box sat at the root origin, which
		# for a floor-rooted prop (the zero door, the extinguisher, the fridge,
		# the gurney) is ankle height - the ray would never reach it and the
		# prop would be visible but impossible to use. Fit the volume to the
		# prop's own geometry instead of guessing per prop.
		var fitted := _local_mesh_bounds(root)
		if fitted.size.length_squared() > 0.0001:
			shape.size = fitted.size + Vector3(0.22, 0.22, 0.22)
			collision.position = fitted.get_center()
			if LEVEL_PROP_VOLUME_CAPS.has(care_id):
				var cap: float = float(LEVEL_PROP_VOLUME_CAPS[care_id]) - root.global_position.y
				var bottom: float = collision.position.y - shape.size.y * 0.5
				var top: float = minf(collision.position.y + shape.size.y * 0.5, cap)
				shape.size.y = maxf(0.12, top - bottom)
				collision.position.y = bottom + shape.size.y * 0.5
		else:
			shape.size = Vector3(0.58, 0.58, 0.58)
	else:
		shape.size = Vector3(0.58, 0.58, 0.58)
	collision.shape = shape
	area.add_child(collision)
	root.add_child(area)

func _local_mesh_bounds(root: Node3D) -> AABB:
	"""Combined AABB of every mesh under `root`, expressed in root-local space."""
	var bounds := AABB()
	var started := false
	var to_local := root.global_transform.affine_inverse()
	for node in _all_nodes(root):
		if not node is MeshInstance3D:
			continue
		var mesh_instance := node as MeshInstance3D
		if not mesh_instance.mesh:
			continue
		var piece: AABB = (to_local * mesh_instance.global_transform) * mesh_instance.mesh.get_aabb()
		if started:
			bounds = bounds.merge(piece)
		else:
			bounds = piece
			started = true
	return bounds

func _add_light(anchor: Node3D) -> void:
	runtime_light_candidate += 1
	var platform := get_tree().get_first_node_in_group("yandex_sdk")
	var mobile_mode: bool = bool(platform and platform.is_mobile_device())
	# Half as many unshadowed omni lights substantially reduces WebGL light
	# passes on phones while the larger range keeps every room readable.
	if mobile_mode and runtime_light_candidate % 2 == 0:
		return
	var light := OmniLight3D.new()
	light.name = "RuntimeHospitalLight"
	light.light_color = Color(0.68, 0.79, 0.70)
	light.light_energy = 1.45
	light.omni_range = 7.8 if mobile_mode else 6.5
	light.shadow_enabled = false
	light.position = Vector3(0.0, -0.2, 0.0)
	light.add_to_group("hospital_lights")
	anchor.add_child(light)

func _on_reached_time(hour: int, minute: int) -> void:
	var state := get_tree().get_first_node_in_group("hospital_state")
	if not state or state.get_flag("ending_requested", false):
		return
	# 06:00 remains a failure deadline only. Successful completion is dispatched
	# immediately by LevelManager from task/story triggers, with no final call.
	if hour == 6 and minute == 0:
		state.request_ending("unfinished_shift")

func _on_ending_requested(id: String) -> void:
	var platform := get_tree().get_first_node_in_group("yandex_sdk")
	if platform:
		var state := get_tree().get_first_node_in_group("hospital_state")
		var details: Dictionary = {}
		if state:
			details = {
				"task_count": state.task_count(),
				"task_total": state.task_total(),
				"medical_errors": int(state.get_flag("medical_errors", 0)),
				"patient_outcomes": state.patient_outcomes.duplicate(true),
				"observed_patient_count": state.observed_patient_count()
			}
		platform.record_shift_result(LevelManager.selected_index, id, id == "dawn", details)
		platform.set_gameplay_active(false)
	var tm := get_tree().get_first_node_in_group("time_manager")
	if tm:
		tm.pause_clock(true)
	var player := get_tree().get_first_node_in_group("player")
	if player:
		player.set_frozen(true)
	var hud := get_tree().get_first_node_in_group("hud")
	if id != "dawn":
		if not hud:
			return
		# A lost shift is the natural ad break: the run is over either way. The
		# ad plays BEFORE the ending screen rather than on top of it, and the
		# SDK's cooldown keeps it from stacking with the one on restart. Every
		# path through show_interstitial() still calls back, so the ending panel
		# appears even when no ad was shown.
		if platform:
			platform.show_interstitial(hud.show_ending.bind(id, false))
		else:
			hud.show_ending(id, false)
		return
	var environment: Environment = $WorldEnvironment.environment
	var tween := create_tween()
	tween.tween_property(environment, "background_color", Color(0.34, 0.36, 0.38), 5.0)
	if hud:
		hud.show_message(tr("А вы кто?"), 4.0)
		await get_tree().create_timer(4.5).timeout
		hud.show_ending("dawn", true)
