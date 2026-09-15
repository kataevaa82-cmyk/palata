extends SceneTree

# In-engine proof that selecting a night swaps what is standing in the ward.
# Each shot picks a night, re-applies the prop whitelist, then looks at that
# night's own prop with the game's real lighting and materials.
#
# Blender (x, y, z) maps to Godot (x, z, -y) through the GLB import, so the
# coordinates below are the Blender placements with y and z traded.

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _i in 14:
		await process_frame

	var hud := game.get_node("HUD")
	var levels := game.get_node("LevelManager")
	var hospital := game.get_node("HospitalModel")
	var player: CharacterBody3D = game.get_node("Player")

	# First shot keeps the HUD up: it is the start screen with the night picker.
	await RenderingServer.frame_post_draw
	var menu_image := root.get_texture().get_image()
	print("menu error=", menu_image.save_png("C:/palata/build/levels/00_menu.png"))

	for child in hud.get_children():
		if child is CanvasItem:
			child.visible = false
	player.set_frozen(true)
	player.rotation = Vector3.ZERO
	player.head.rotation = Vector3.ZERO

	# night index, name, camera stand point, look-at target
	var shots := [
		[1, "night2_fuse_box", Vector3(-14.0, 0.0, -0.2), Vector3(-15.5, 1.55, -1.45)],
		[3, "night4_gurney", Vector3(11.6, 0.0, -0.1), Vector3(9.6, 0.75, -1.02)],
		[5, "night6_radiator", Vector3(-6.6, 0.0, -3.6), Vector3(-6.6, 0.45, -5.34)],
		[6, "night7_escapee", Vector3(17.6, 0.0, -0.4), Vector3(19.45, 0.85, 0.65)],
		[8, "night9_extinguisher", Vector3(12.6, 0.0, -0.3), Vector3(14.5, 0.75, -1.36)],
		[10, "night11_zero_door", Vector3(-3.7, 0.0, -0.2), Vector3(-5.55, 1.1, -1.56)],
	]
	for shot in shots:
		var index: int = shot[0]
		var shot_name: String = shot[1]
		var stand: Vector3 = shot[2]
		var target: Vector3 = shot[3]
		LevelManager.selected_index = index
		levels.apply_prop_visibility(hospital)
		player.global_position = Vector3(stand.x, 0.0, stand.z)
		var eye_offset: float = player.camera.global_position.y - player.global_position.y
		player.global_position = Vector3(stand.x, 1.62 - eye_offset, stand.z)
		player.camera.look_at(target, Vector3.UP)
		for _i in 5:
			await process_frame
		await RenderingServer.frame_post_draw
		var image := root.get_texture().get_image()
		print(shot_name, " error=", image.save_png("C:/palata/build/levels/%s.png" % shot_name))

	LevelManager.selected_index = 0
	quit(0)
