extends SceneTree

func _initialize() -> void:
	call_deferred("_capture")

func _capture() -> void:
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game := packed.instantiate()
	root.add_child(game)
	for _frame in 8:
		await process_frame
	var hud := game.get_node("HUD")
	hud._start_pressed()
	var player := game.get_node("Player")
	player.set_frozen(true)
	var care := game.get_node("CareManager")
	care.accept_phone_assignment("medication")
	hud.message_label.modulate.a = 0.0

	# Corridor view: restored room sign, vitals and persistent assignment panel.
	player.global_position = Vector3(-2.5, 0.08, 0.25)
	player.rotation = Vector3.ZERO
	player.head.rotation = Vector3.ZERO
	await _save("C:/palata/build/care_corridor_hud.png")

	# Procedure room: cabinet, medicines and instruments.
	player.global_position = Vector3(-2.0, 0.08, -3.15)
	player.look_at(Vector3(-4.15, 0.08, -5.15), Vector3.UP)
	player.head.rotation.x = deg_to_rad(-5.0)
	await _save("C:/palata/build/care_procedure_props.png")

	# Close inspection of the rebuilt patient in ward 4.
	var patient: Node3D
	for candidate in get_nodes_in_group("care_patients"):
		if candidate.get("patient_id") == "saveliev":
			patient = candidate
			break
	if patient:
		player.global_position = patient.global_position + Vector3(1.30, 0.08, 0.10)
		player.look_at(Vector3(patient.global_position.x, 0.08, patient.global_position.z), Vector3.UP)
		player.head.rotation.x = deg_to_rad(-27.0)
		await _save("C:/palata/build/care_patient_rebuild.png")
	quit(0)

func _save(path: String) -> void:
	for _frame in 8:
		await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	var error := image.save_png(path)
	print("CARE_CAPTURE ", path, " error=", error)
