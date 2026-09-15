extends SceneTree

# Renders the ward-4 bedridden patient as the player actually meets him: the
# game's own lighting and material_system.gd shaders, not a Blender preview.
# Blender studio renders told us nothing useful about in-engine appearance.

const PATIENT := "ward_4_bed_1_patient_v3"
const OUTPUT := "C:/palata/build/ward_patient_ingame.png"

func _initialize() -> void:
	call_deferred("_capture")

func _capture() -> void:
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game := packed.instantiate()
	root.add_child(game)
	for _i in 8:
		await process_frame

	var hud := game.get_node("HUD")
	for child in hud.get_children():
		if child is CanvasItem:
			child.visible = false

	var hospital := game.get_node("HospitalModel")
	var patient := hospital.find_child(PATIENT, true, false) as Node3D
	if not patient:
		push_error("WARD_PATIENT_NOT_FOUND")
		quit(1)
		return
	var head := patient.find_child("*patient_head", true, false) as MeshInstance3D
	if not head:
		push_error("WARD_PATIENT_HEAD_NOT_FOUND")
		quit(1)
		return

	# The patient meshes bake absolute vertex coordinates and leave the object
	# origin at the patient root, so head.global_position is the root, not the
	# head. Take the centre of the mesh AABB instead.
	var target: Vector3 = head.global_transform * head.get_aabb().get_center()

	var player := game.get_node("Player")
	player.set_frozen(true)
	player.rotation = Vector3.ZERO
	player.head.rotation = Vector3.ZERO

	# player.global_position is the feet/collider origin; Head and Camera3D add
	# their own vertical offset on top. Measure it rather than hardcoding, or
	# the camera ends up in the ceiling.
	player.global_position = Vector3(target.x, 0.0, target.z)
	var eye_offset: float = player.camera.global_position.y - player.global_position.y
	player.global_position = Vector3(
		target.x + 0.12,
		target.y + 0.10 - eye_offset,
		target.z + 0.55)
	player.camera.look_at(target, Vector3.UP)

	for _i in 6:
		await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	var error := image.save_png(OUTPUT)
	print("WARD_PATIENT_CAPTURE error=", error, " target=", target)
	quit(0 if error == OK else 1)
