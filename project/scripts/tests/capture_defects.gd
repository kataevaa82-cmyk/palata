extends SceneTree

# Look at the spots the player complained about, with the game's own lighting.
# Blender coordinates map to Godot as (x, z, -y).
# Usage: godot --headless --path project --script ... -- <prefix>

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _i in 16:
		await process_frame
	var hud := game.get_node("HUD")
	for child in hud.get_children():
		if child is CanvasItem:
			child.visible = false

	var player: CharacterBody3D = game.get_node("Player")
	player.set_frozen(true)
	player.rotation = Vector3.ZERO
	player.head.rotation = Vector3.ZERO

	# name, look_at target (Godot), stand position (Godot x/z)
	var shots := [
		["nurse_label", Vector3(2.5, 2.48, -1.38), Vector3(2.5, 0.0, 0.4)],
		["nurse_label_angle", Vector3(2.5, 2.48, -1.38), Vector3(-1.0, 0.0, 0.9)],
		["room_zero_label", Vector3(15.0, 2.6, -1.45), Vector3(15.0, 0.0, 0.3)],
		["room_zero_angle", Vector3(15.0, 2.6, -1.45), Vector3(12.0, 0.0, 0.8)],
		["ward1_bed1_pillow", Vector3(-18.75, 0.95, -4.35), Vector3(-18.75, 0.0, -2.2)],
		["ward1_bed1_side", Vector3(-18.75, 0.95, -4.35), Vector3(-17.6, 0.0, -3.4)],
		["ward1_bed2_pillow", Vector3(-16.25, 0.95, -4.35), Vector3(-16.25, 0.0, -2.2)],
		["ward6_bed2_pillow", Vector3(-6.25, 0.95, 4.35), Vector3(-6.25, 0.0, 2.2)],
		["ward6_bed2_side", Vector3(-6.25, 0.95, 4.35), Vector3(-7.4, 0.0, 3.4)],
		["ward4_bed1_side", Vector3(-18.75, 0.95, 4.35), Vector3(-19.9, 0.0, 3.4)],
	]
	var args := OS.get_cmdline_user_args()
	var prefix: String = String(args[0]) if args.size() > 0 else "defect"
	for shot in shots:
		var shot_name: String = shot[0]
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
		print(shot_name, " error=", image.save_png("C:/palata/build/%s_%s.png" % [prefix, shot_name]))
	quit(0)
