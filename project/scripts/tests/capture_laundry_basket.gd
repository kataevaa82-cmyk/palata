extends SceneTree

const TARGET := "interaction_laundry_basket"
const OUTPUT_DIR := "C:/palata/build"

func _initialize() -> void:
	call_deferred("_capture")

func _capture() -> void:
	var label := "review"
	var user_args := OS.get_cmdline_user_args()
	if not user_args.is_empty():
		label = String(user_args[0]).validate_filename()

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
	var basket := hospital.find_child(TARGET, true, false) as Node3D
	if not basket:
		push_error("LAUNDRY_BASKET_NOT_FOUND")
		quit(1)
		return

	var visual_bounds := _visual_bounds(basket)
	var center := visual_bounds.get_center()
	var camera := Camera3D.new()
	camera.fov = 58.0
	game.add_child(camera)
	camera.current = true

	# First view is from inside the sanitary room; second is from the adjacent
	# room, so an object crossing the partition is immediately visible.
	var views := {
		"sanitary": Vector3(-1.55, 0.90, -1.35),
		"partition": Vector3(1.45, 0.85, -1.20),
	}
	var failures := 0
	for view_name in views:
		camera.global_position = center + views[view_name]
		camera.look_at(center, Vector3.UP)
		for _i in 5:
			await process_frame
		await RenderingServer.frame_post_draw
		var image := root.get_texture().get_image()
		var path := "%s/laundry_basket_%s_%s.png" % [OUTPUT_DIR, label, view_name]
		var error := image.save_png(path)
		failures += int(error != OK)
		print("LAUNDRY_CAPTURE path=", path, " error=", error)

	print("LAUNDRY_BASKET center=", center, " size=", visual_bounds.size)
	quit(0 if failures == 0 else 1)

func _visual_bounds(node: Node3D) -> AABB:
	var result := AABB()
	var initialized := false
	for descendant in _all_nodes(node):
		if descendant is MeshInstance3D:
			var mesh_node := descendant as MeshInstance3D
			var local_bounds := mesh_node.get_aabb()
			for corner_index in 8:
				var corner := local_bounds.get_endpoint(corner_index)
				var world_corner := mesh_node.global_transform * corner
				if not initialized:
					result = AABB(world_corner, Vector3.ZERO)
					initialized = true
				else:
					result = result.expand(world_corner)
	return result

func _all_nodes(node: Node) -> Array[Node]:
	var result: Array[Node] = [node]
	for child in node.get_children():
		result.append_array(_all_nodes(child))
	return result
