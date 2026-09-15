extends SceneTree

const ProgressGuard := preload("res://scripts/tests/progress_guard.gd")

# Publication screenshots rendered by the shipping scene at 1280x720. Locale
# and device mode are passed after `--`, for example: `-- en mobile`.

var game: Node
var hud: Node
var player: CharacterBody3D
var care: Node
var hospital: Node
var locale := "ru"
var output_dir := "C:/palata/build/yandex_media/screenshots/ru"
var mobile := false
var failures: Array[String] = []

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	ProgressGuard.snapshot()
	var args := OS.get_cmdline_user_args()
	for argument in args:
		if String(argument).to_lower() == "en":
			locale = "en"
		elif String(argument).to_lower() == "mobile":
			mobile = true
	output_dir = (
		"C:/palata/build/yandex_media/screenshots/mobile/%s" % locale
		if mobile
		else "C:/palata/build/yandex_media/screenshots/%s" % locale)
	DirAccess.make_dir_recursive_absolute(output_dir)
	LevelManager.selected_index = 0

	game = load("res://scenes/hospital/main.tscn").instantiate()
	root.add_child(game)
	while not game.prepared:
		await process_frame
	for _frame in 8:
		await process_frame

	hud = game.get_node("HUD")
	player = game.get_node("Player")
	care = game.get_node("CareManager")
	hospital = game.get_node("HospitalModel")
	if mobile:
		hud._on_device_type_detected("mobile")
		game.get_node("MobileControls").set_mobile_enabled_for_test(true)
	# Use the same menu button path as the player. Calling the SDK setter alone
	# changes TranslationServer but intentionally leaves HUD rebuilding to the
	# button callback.
	if TranslationServer.get_locale().left(2) != locale:
		hud.language_button.pressed.emit()
	else:
		hud._refresh_language_button()
	for _frame in 6:
		await process_frame

	await _save("00_menu")
	hud._begin_shift()
	player.set_frozen(true)
	var board := _care_interactable("assignment_board")
	if board:
		board.interact(player)
		hud.close_document()
	else:
		failures.append("assignment_board_missing")
	hud.message_label.modulate.a = 0.0

	# Wide corridor: the normal moment-to-moment view with objective, vitals and
	# the current care assignment all visible.
	_set_view(Vector3(-14.8, 0.08, 0.20), Vector3(2.0, 1.48, -0.10))
	await _save("01_corridor_shift")

	# Treatment room with the real medicine/instrument shelves. Picking up the
	# prescribed drug also puts its actual world mesh in the player's hand.
	var aminazine := hospital.find_child("interaction_med_aminazine", true, false) as Node3D
	if aminazine:
		care.interact_object("med_aminazine", aminazine)
	else:
		failures.append("aminazine_missing")
	hud.message_label.modulate.a = 0.0
	_set_view(Vector3(-2.0, 0.08, -3.15), Vector3(-4.15, 1.20, -5.15))
	await _save("02_procedure_inventory")

	# The prescribed patient in ward 4, framed as the player approaches the bed.
	var patient := _patient("saveliev")
	if patient:
		_set_view(patient.global_position + Vector3(1.35, 0.08, 0.18),
			patient.global_position + Vector3(0.0, 0.72, 0.0))
	else:
		failures.append("saveliev_missing")
	await _save("03_patient_care")

	# A genuine hostile-orderly encounter. It is paused only for a clean still;
	# the model, lighting, red gaze and HUD are the same runtime encounter.
	var anomalies := game.get_node("AnomalyManager")
	var orderly: Node3D = anomalies.spawn_hostile_orderly()
	if orderly:
		orderly.set_physics_process(false)
		orderly.global_position = Vector3(7.2, 0.04, 0.0)
		orderly.look_at(Vector3(3.8, 0.04, 0.0), Vector3.UP)
		_set_view(Vector3(3.6, 0.08, 0.08), Vector3(7.2, 1.52, 0.0))
	else:
		failures.append("hostile_orderly_missing")
	await _save("04_hostile_encounter")

	ProgressGuard.restore()
	print("YANDEX_SCREENSHOTS locale=%s mobile=%s files=5 failures=%d" % [
		locale, mobile, failures.size()])
	for failure in failures:
		print("  FAIL ", failure)
	quit(0 if failures.is_empty() else 1)

func _set_view(position: Vector3, target: Vector3) -> void:
	player.global_position = position
	player.rotation = Vector3.ZERO
	player.head.rotation = Vector3.ZERO
	player.camera.look_at(target, Vector3.UP)

func _save(name: String) -> void:
	for _frame in 10:
		await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	image.convert(Image.FORMAT_RGB8)
	var path := "%s/%s_%s.png" % [output_dir, name, locale]
	var error := image.save_png(path)
	if error != OK:
		failures.append("save_%s_%d" % [name, error])
	print("YANDEX_SCREEN path=%s size=%dx%d error=%d" % [path, image.get_width(), image.get_height(), error])

func _care_interactable(id: String) -> Node:
	for node in get_nodes_in_group("care_interactables"):
		if String(node.get("care_id")) == id:
			return node
	return null

func _patient(id: String) -> Node3D:
	for node in get_nodes_in_group("care_patients"):
		if String(node.get("patient_id")) == id:
			return node as Node3D
	return null
