extends SceneTree

func _initialize() -> void:
	call_deferred("_capture")

func _capture() -> void:
	var game = load("res://scenes/hospital/main.tscn").instantiate()
	root.add_child(game)
	while not game.prepared:
		await process_frame
	var hud = game.get_node("HUD")
	hud.hide()
	var player = game.get_node("Player")
	player.set_physics_process(false)
	var hospital = game.get_node("HospitalModel")
	var camera := Camera3D.new()
	game.add_child(camera)
	camera.current = true
	camera.fov = 48
	var hair = hospital.find_child("ward_4_bed_1_patient_v3_patient_hair_groom", true, false)
	var target: Vector3 = hair.global_transform * hair.get_aabb().get_center()
	camera.global_position = target + Vector3(-0.27, 0.43, -0.27)
	camera.look_at(target, Vector3.UP)
	await save_frame("ward_ingame")
	game.get_node("AnomalyManager").activate("violent_patient")
	await process_frame
	var actor = hospital.get_node("violent_patient")
	actor.set_physics_process(false)
	actor.global_position = Vector3(-3.6, 0.05, 0)
	camera.global_position = Vector3(-6.3, 1.35, .55)
	actor.look_at(Vector3(camera.global_position.x, .05, camera.global_position.z), Vector3.UP)
	camera.look_at(actor.global_position + Vector3(0,.9,0), Vector3.UP)
	await save_frame("violent_ingame")
	var animation_player: AnimationPlayer
	for node in actor.find_children("*", "AnimationPlayer", true, false):
		animation_player = node
		break
	if animation_player:
		for clip in animation_player.get_animation_list():
			var label := String(clip).to_lower()
			if not ("run" in label or "attack" in label or "idle" in label):
				continue
			animation_player.play(clip)
			animation_player.advance(.35)
			animation_player.pause()
			await save_frame("patient_" + ("attack" if "attack" in label else ("run" if "run" in label else "idle")))
	game.queue_free()
	await process_frame
	quit()

func save_frame(name: String) -> void:
	for frame in 12:
		await process_frame
	await RenderingServer.frame_post_draw
	var error := root.get_texture().get_image().save_png("C:/palata/build/patient_update/" + name + ".png")
	print("PATIENT_REVIEW ", name, " error=", error)
