extends SceneTree

const MODEL := "res://assets/models/palata_zero.glb"
const REQUIRED := [
	"interaction_assignment_board",
	"interaction_doctors_computer",
	"interaction_fuse_box",
	"interaction_gurney",
	"interaction_zero_door",
	"ward_1_bed_1",
	"ward_4_bed_1_patient_v3",
	"ward_6_bed_2",
	"corridor_clock_v2",
	"wheelchair_v2",
]

func _initialize() -> void:
	var packed := load(MODEL) as PackedScene
	if not packed:
		push_error("OPTIMIZED_HOSPITAL load failed")
		quit(1)
		return
	var hospital := packed.instantiate()
	root.add_child(hospital)
	var missing: Array[String] = []
	for object_name in REQUIRED:
		if not hospital.find_child(object_name, true, false):
			missing.append(object_name)
	var mesh_count := 0
	for node in _all_nodes(hospital):
		if node is MeshInstance3D:
			mesh_count += 1
	print("OPTIMIZED_HOSPITAL meshes=", mesh_count, " missing=", missing)
	quit(0 if missing.is_empty() and mesh_count > 2500 else 1)

func _all_nodes(root_node: Node) -> Array[Node]:
	var result: Array[Node] = [root_node]
	var index := 0
	while index < result.size():
		result.append_array(result[index].get_children())
		index += 1
	return result
