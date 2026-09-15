extends SceneTree

# Look at an arbitrary world point from the corridor, with the game's own
# lighting and shaders. Used to identify what the player actually sees on the
# walls before changing geometry in Blender.

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _i in 12:
		await process_frame
	var hud := game.get_node("HUD")
	for child in hud.get_children():
		if child is CanvasItem:
			child.visible = false

	var player: CharacterBody3D = game.get_node("Player")
	player.set_frozen(true)
	player.rotation = Vector3.ZERO
	player.head.rotation = Vector3.ZERO

	var shots := [
		["sign_close", Vector3(-7.5, 2.64, 1.53), Vector3(-7.5, 0.0, -0.4)],
		["corridor_wide", Vector3(0.0, 1.8, 1.5), Vector3(-6.0, 0.0, 0.0)],
		["west_end_wall", Vector3(-20.4, 1.8, 0.0), Vector3(-17.0, 0.0, 0.0)],
		["east_exit", Vector3(20.4, 1.8, 0.0), Vector3(17.0, 0.0, 0.0)],
	]
	for shot in shots:
		var name: String = shot[0]
		var target: Vector3 = shot[1]
		var stand: Vector3 = shot[2]
		player.global_position = Vector3(stand.x, 0.0, stand.z)
		var eye_offset: float = player.camera.global_position.y - player.global_position.y
		player.global_position = Vector3(stand.x, 1.6 - eye_offset, stand.z)
		player.camera.look_at(target, Vector3.UP)
		for _i in 4:
			await process_frame
		await RenderingServer.frame_post_draw
		var image := root.get_texture().get_image()
		# Optional `-- <prefix>` so two runs (e.g. before and after a shader
		# change) can be captured side by side instead of overwriting.
		var args := OS.get_cmdline_user_args()
		var prefix: String = String(args[0]) if args.size() > 0 else "look"
		print(name, " error=", image.save_png("C:/palata/build/%s_%s.png" % [prefix, name]))
	quit(0)
