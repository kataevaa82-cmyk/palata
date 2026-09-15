extends SceneTree

func _initialize() -> void:
	call_deferred("_capture")

func _capture() -> void:
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game := packed.instantiate()
	root.add_child(game)
	for _i in 8:
		await process_frame
	var hud := game.get_node("HUD")
	hud.start_panel.visible = false
	hud.objective_label.visible = false
	hud.time_label.visible = false
	var player := game.get_node("Player")
	player.set_frozen(true)
	player.global_position = Vector3(-7.0, 0.08, 0.0)
	player.rotation = Vector3(0.0, -PI / 2.0, 0.0)
	player.head.rotation = Vector3.ZERO
	var manager := game.get_node("AnomalyManager")
	manager.activate("violent_patient")
	await process_frame
	var actor := game.get_node("HospitalModel/violent_patient")
	actor.set_physics_process(false)
	actor.global_position = Vector3(-3.6, 0.05, 0.0)
	actor.look_at(player.global_position, Vector3.UP)
	for _i in 10:
		await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	var error := image.save_png("C:/palata/build/violent_patient_preview.png")
	print("VIOLENT_CAPTURE error=", error)
	quit(0 if error == OK else 1)
