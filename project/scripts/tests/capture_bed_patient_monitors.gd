extends SceneTree

const OUTPUT_DIR := "C:/palata/build"
const REVIEW_PATIENT := "ward_4_bed_1_patient_v3"

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
	var camera := Camera3D.new()
	camera.fov = 54.0
	game.add_child(camera)
	camera.current = true

	var failures := 0
	var patient := hospital.find_child(REVIEW_PATIENT, true, false) as Node3D
	if not patient:
		push_error("REVIEW_PATIENT_NOT_FOUND")
		quit(1)
		return
	var patient_bounds := _visual_bounds(patient)
	var patient_center := patient_bounds.get_center()
	print("BED_PATIENT name=", patient.name, " center=", patient_center, " size=", patient_bounds.size)
	failures += await _save_view(
		camera,
		patient_center + Vector3(1.55, 1.35, -0.65),
		patient_center + Vector3(0.0, 0.05, 0.0),
		"%s/bed_patient_three_quarter.png" % OUTPUT_DIR)
	failures += await _save_view(
		camera,
		patient_center + Vector3(-0.75, 2.25, -0.25),
		patient_center,
		"%s/bed_patient_overhead.png" % OUTPUT_DIR)

	var patients: Array[Node3D] = []
	for node in _all_nodes(hospital):
		if node is Node3D and String(node.name).ends_with("_patient_v3"):
			patients.append(node as Node3D)

	for monitor_index in [1, 2]:
		var monitor_name := "patient_monitor_%d_v2" % monitor_index
		var monitor := hospital.find_child(monitor_name, true, false) as Node3D
		if not monitor:
			push_error("MONITOR_NOT_FOUND " + monitor_name)
			failures += 1
			continue
		var screen := monitor.find_child("*screen", true, false) as MeshInstance3D
		if not screen:
			push_error("MONITOR_SCREEN_NOT_FOUND " + monitor_name)
			failures += 1
			continue
		var monitor_bounds := _visual_bounds(monitor)
		var monitor_center := monitor_bounds.get_center()
		var screen_center := screen.global_transform * screen.get_aabb().get_center()
		var front := screen_center - monitor_center
		front.y = 0.0
		front = front.normalized()
		var nearest_patient := _nearest_patient(monitor_center, patients)
		var nearest_center := _visual_bounds(nearest_patient).get_center()
		print(
			"BED_MONITOR name=", monitor_name,
			" center=", monitor_center,
			" size=", monitor_bounds.size,
			" nearest_patient=", nearest_patient.name)

		failures += await _save_view(
			camera,
			screen_center + front * 1.25 + Vector3.UP * 0.12,
			screen_center,
			"%s/bed_monitor_%d_close.png" % [OUTPUT_DIR, monitor_index])
		var context_target := (monitor_center + nearest_center) * 0.5
		failures += await _save_view(
			camera,
			context_target + front * 2.15 + Vector3.UP * 0.65,
			context_target,
			"%s/bed_monitor_%d_context.png" % [OUTPUT_DIR, monitor_index])

	quit(0 if failures == 0 else 1)

func _save_view(camera: Camera3D, position: Vector3, target: Vector3, path: String) -> int:
	camera.global_position = position
	camera.look_at(target, Vector3.UP)
	for _i in 5:
		await process_frame
	await RenderingServer.frame_post_draw
	var error := root.get_texture().get_image().save_png(path)
	print("BED_REVIEW_CAPTURE path=", path, " error=", error)
	return int(error != OK)

func _nearest_patient(point: Vector3, patients: Array[Node3D]) -> Node3D:
	var nearest := patients[0]
	var nearest_distance := INF
	for patient in patients:
		var center := _visual_bounds(patient).get_center()
		var distance := Vector2(point.x, point.z).distance_to(Vector2(center.x, center.z))
		if distance < nearest_distance:
			nearest = patient
			nearest_distance = distance
	return nearest

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
