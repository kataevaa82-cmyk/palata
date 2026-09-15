extends SceneTree

func _initialize() -> void:
	call_deferred("_capture")

func _capture() -> void:
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var scene := packed.instantiate()
	root.add_child(scene)
	for _i in 8:
		await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	var error := image.save_png("C:/palata/build/menu_preview.png")
	scene.get_node("HUD")._start_pressed()
	for _i in 8:
		await process_frame
	await RenderingServer.frame_post_draw
	var game_image := root.get_texture().get_image()
	var game_error := game_image.save_png("C:/palata/build/gameplay_preview.png")
	print("MENU_CAPTURE error=", error, " gameplay_error=", game_error)
	quit(0 if error == OK and game_error == OK else 1)
