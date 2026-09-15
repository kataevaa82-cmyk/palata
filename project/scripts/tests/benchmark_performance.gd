extends SceneTree

const ProgressGuard := preload("res://scripts/tests/progress_guard.gd")

# A measured baseline, not a guess: the ward is walked along a fixed route with
# the real materials, lights and props switched on, and every frame is timed.
#
# Headless proves nothing here - it draws nothing. This runs in a real window,
# so it must be launched WITHOUT --headless.
#
# Reported per station: frame time (ms), draw calls, and the primitives the
# renderer actually pushed, plus a whole-route summary. Compare two runs by
# their `ROUTE` line.

# Blender (x, y, z) maps to Godot (x, z, -y): these are the ward's own rooms.
const ROUTE := [
	["corridor_west", Vector3(-18.0, 0.0, 0.0), Vector3(0.0, 0.0, 0.0)],
	["corridor_mid", Vector3(-6.0, 0.0, 0.0), Vector3(14.0, 0.0, 0.0)],
	["corridor_east", Vector3(15.0, 0.0, 0.0), Vector3(-14.0, 0.0, 0.0)],
	["nurse_station", Vector3(4.5, 0.0, -3.6), Vector3(4.5, 0.0, -5.2)],
	["ward_1", Vector3(-16.5, 0.0, -4.0), Vector3(-16.5, 0.0, -6.0)],
	["ward_6", Vector3(-1.3, 0.0, -4.9), Vector3(-1.3, 0.0, -6.4)],
	["procedure", Vector3(9.5, 0.0, -4.2), Vector3(9.5, 0.0, -6.0)],
	["doctors_room", Vector3(7.5, 0.0, -3.8), Vector3(9.0, 0.0, -3.8)],
	["sanitary", Vector3(9.1, 0.0, 5.2), Vector3(7.5, 0.0, 5.2)],
	["storage", Vector3(16.5, 0.0, -4.3), Vector3(18.0, 0.0, -4.3)],
]
const WARMUP_FRAMES := 45
const SAMPLE_FRAMES := 90

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	ProgressGuard.snapshot()
	# Without this every station reports exactly 16.66 ms - the vsync wait, not
	# the frame cost. The numbers only mean something uncapped.
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0
	var started_load := Time.get_ticks_usec()
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game: Node = packed.instantiate()
	root.add_child(game)
	while not game.prepared:
		await process_frame
	var load_ms := float(Time.get_ticks_usec() - started_load) / 1000.0

	var hud := game.get_node("HUD")
	var director := game.get_node("GameDirector")
	var player: CharacterBody3D = game.get_node("Player")
	director.start_shift()
	player.set_frozen(true)
	for child in hud.get_children():
		if child is CanvasItem:
			child.visible = false

	for _i in WARMUP_FRAMES:
		await process_frame

	var route_samples: Array[float] = []
	var worst_station := ""
	var worst_ms := 0.0
	print("BENCH_STATIONS")
	for station in ROUTE:
		var label: String = station[0]
		var stand: Vector3 = station[1]
		var target: Vector3 = station[2]
		var eye_offset: float = player.camera.global_position.y - player.global_position.y
		player.global_position = Vector3(stand.x, 1.62 - eye_offset, stand.z)
		player.rotation = Vector3.ZERO
		player.head.rotation = Vector3.ZERO
		player.camera.look_at(Vector3(target.x, 1.5, target.z), Vector3.UP)
		for _i in 12:
			await process_frame

		var samples: Array[float] = []
		for _i in SAMPLE_FRAMES:
			var before := Time.get_ticks_usec()
			await RenderingServer.frame_post_draw
			samples.append(float(Time.get_ticks_usec() - before) / 1000.0)
		samples.sort()
		var median: float = samples[samples.size() / 2]
		var p95: float = samples[int(samples.size() * 0.95)]
		route_samples.append_array(samples)
		if median > worst_ms:
			worst_ms = median
			worst_station = label
		print("  %-14s median=%6.2fms p95=%6.2fms draw_calls=%5d prims=%9d objects=%5d" % [
			label, median, p95,
			RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
			RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),
			RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME)])

	route_samples.sort()
	var median: float = route_samples[route_samples.size() / 2]
	var p95: float = route_samples[int(route_samples.size() * 0.95)]
	var mesh_count := 0
	var light_count := 0
	for node in _all(game.get_node("HospitalModel")):
		if node is MeshInstance3D:
			mesh_count += 1
		elif node is Light3D:
			light_count += 1
	print("ROUTE median=%.2fms p95=%.2fms (%.0f fps median) worst=%s %.2fms" % [
		median, p95, 1000.0 / maxf(median, 0.001), worst_station, worst_ms])
	print("SCENE load=%.0fms meshes=%d lights=%d video_mem=%.1fMB" % [
		load_ms, mesh_count, light_count,
		float(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED)) / 1048576.0])
	ProgressGuard.restore()
	quit(0)

func _all(node: Node) -> Array[Node]:
	var out: Array[Node] = [node]
	for child in node.get_children():
		out.append_array(_all(child))
	return out
