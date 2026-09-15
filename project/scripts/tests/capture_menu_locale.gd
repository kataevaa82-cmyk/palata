extends SceneTree

const ProgressGuard := preload("res://scripts/tests/progress_guard.gd")

# Shot of the start screen in both languages, taken through the menu's own
# language button - the same path a player uses. Proof that the night list, the
# brief and the scene-authored labels all end up in one language at once.

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	ProgressGuard.snapshot()
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game: Node = packed.instantiate()
	root.add_child(game)
	while not game.prepared:
		await process_frame
	for _i in 8:
		await process_frame

	var hud := game.get_node("HUD")
	var button := hud.get_node("StartPanel/LanguageButton") as Button
	for shot in ["ru", "en"]:
		if TranslationServer.get_locale().left(2) != shot:
			button.pressed.emit()
			for _i in 6:
				await process_frame
		await RenderingServer.frame_post_draw
		var image := root.get_texture().get_image()
		print("menu_%s error=%d" % [shot, image.save_png("C:/palata/build/menu_%s.png" % shot)])

	ProgressGuard.restore()
	quit(0)
