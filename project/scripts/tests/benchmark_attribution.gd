extends SceneTree

const ProgressGuard := preload("res://scripts/tests/progress_guard.gd")

# Where does the frame actually go? benchmark_performance.gd says the corridor
# costs ~22 ms and an empty side room still costs ~17 ms on the test GPU, which
# means draw calls are not the whole story. This re-measures the same three
# corridor views with one cost removed at a time:
#
#   base       - the game as shipped
#   flat       - the procedural grime/wear shader swapped for a plain material
#   nolights   - the runtime ceiling omnis switched off
#   nosmall    - meshes under 0.25 m culled (the screws, stains and labels)
#
# Run WITHOUT --headless. The gap between `base` and each mode is that
# subsystem's share of the frame.

const VIEWS := [
	["corridor_west", Vector3(-18.0, 0.0, 0.0), Vector3(0.0, 0.0, 0.0)],
	["corridor_mid", Vector3(-6.0, 0.0, 0.0), Vector3(14.0, 0.0, 0.0)],
	["corridor_east", Vector3(15.0, 0.0, 0.0), Vector3(-14.0, 0.0, 0.0)],
]
const MODES := ["base", "flat", "nolights", "nosmall"]
const SAMPLE_FRAMES := 70

var game: Node
var player: CharacterBody3D
var hospital: Node3D

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	ProgressGuard.snapshot()
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	game = packed.instantiate()
	root.add_child(game)
	while not game.prepared:
		await process_frame
	hospital = game.get_node("HospitalModel")
	player = game.get_node("Player")
	game.get_node("GameDirector").start_shift()
	player.set_frozen(true)
	for child in game.get_node("HUD").get_children():
		if child is CanvasItem:
			child.visible = false
	for _i in 40:
		await process_frame

	print("BENCH_ATTRIBUTION")
	for mode in MODES:
		_apply(mode)
		for _i in 20:
			await process_frame
		var totals: Array[float] = []
		var calls := 0
		for view in VIEWS:
			var eye_offset: float = player.camera.global_position.y - player.global_position.y
			player.global_position = Vector3(view[1].x, 1.62 - eye_offset, view[1].z)
			player.rotation = Vector3.ZERO
			player.head.rotation = Vector3.ZERO
			player.camera.look_at(Vector3(view[2].x, 1.5, view[2].z), Vector3.UP)
			for _i in 10:
				await process_frame
			var samples: Array[float] = []
			for _i in SAMPLE_FRAMES:
				var before := Time.get_ticks_usec()
				await RenderingServer.frame_post_draw
				samples.append(float(Time.get_ticks_usec() - before) / 1000.0)
			samples.sort()
			totals.append(samples[samples.size() / 2])
			calls = maxi(calls, RenderingServer.get_rendering_info(
				RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME))
		var sum := 0.0
		for value in totals:
			sum += value
		print("  %-9s corridor_median=%6.2fms  (%s)  peak_draw_calls=%d" % [
			mode, sum / totals.size(),
			", ".join(PackedStringArray(totals.map(func(v): return "%.1f" % v))), calls])
		_restore(mode)

	ProgressGuard.restore()
	quit(0)

func _apply(mode: String) -> void:
	match mode:
		"flat":
			var plain := StandardMaterial3D.new()
			plain.albedo_color = Color(0.45, 0.48, 0.42)
			plain.roughness = 0.9
			for node in _all(hospital):
				if node is MeshInstance3D:
					(node as MeshInstance3D).material_override = plain
		"nolights":
			for light in get_nodes_in_group("hospital_lights"):
				(light as Light3D).visible = false
		"nosmall":
			for node in _all(hospital):
				if node is MeshInstance3D and (node as MeshInstance3D).mesh:
					if (node as MeshInstance3D).mesh.get_aabb().size.length() < 0.25:
						(node as Node3D).visible = false

func _restore(mode: String) -> void:
	match mode:
		"flat":
			for node in _all(hospital):
				if node is MeshInstance3D:
					(node as MeshInstance3D).material_override = null
		"nolights":
			for light in get_nodes_in_group("hospital_lights"):
				(light as Light3D).visible = true
		"nosmall":
			for node in _all(hospital):
				if node is MeshInstance3D and (node as MeshInstance3D).mesh:
					if (node as MeshInstance3D).mesh.get_aabb().size.length() < 0.25:
						(node as Node3D).visible = true

func _all(node: Node) -> Array[Node]:
	var out: Array[Node] = [node]
	for child in node.get_children():
		out.append_array(_all(child))
	return out
