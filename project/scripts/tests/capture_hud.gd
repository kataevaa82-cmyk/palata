extends SceneTree

# Confirms the two HUD edits in the running game: the vitals panel no longer
# carries the red/blue gaze hint, and the document panel (patient journal /
# assignment board) shows how to close itself.

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _i in 14:
		await process_frame

	var hud := game.get_node("HUD")
	hud._start_pressed()
	for _i in 4:
		await process_frame

	var care := game.get_node("CareManager")
	hud.open_document(care.schedule_text())
	for _i in 4:
		await process_frame
	await RenderingServer.frame_post_draw
	print("document error=", root.get_texture().get_image().save_png("C:/palata/build/hud/document.png"))

	hud.document_panel.visible = false
	for _i in 3:
		await process_frame
	await RenderingServer.frame_post_draw
	print("vitals error=", root.get_texture().get_image().save_png("C:/palata/build/hud/vitals.png"))
	quit(0)
