extends SceneTree

const ProgressGuard := preload("res://scripts/tests/progress_guard.gd")
const FPS := 30

# Deterministic real-engine gameplay capture for Godot's --write-movie mode.
# It follows one continuous first-person shift, performs the board and medicine
# interactions, approaches the assigned patient, and ends on a hostile encounter.

var game: Node
var hud: Node
var player: CharacterBody3D
var care: Node
var hospital: Node
var locale := "ru"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	ProgressGuard.snapshot()
	var args := OS.get_cmdline_user_args()
	if not args.is_empty() and String(args[0]).to_lower() == "en":
		locale = "en"
	LevelManager.selected_index = 0
	game = load("res://scenes/hospital/main.tscn").instantiate()
	root.add_child(game)
	while not game.prepared:
		await process_frame
	for _frame in FPS:
		await process_frame

	hud = game.get_node("HUD")
	player = game.get_node("Player")
	care = game.get_node("CareManager")
	hospital = game.get_node("HospitalModel")
	if TranslationServer.get_locale().left(2) != locale:
		hud.language_button.pressed.emit()
	else:
		hud._refresh_language_button()
	for _frame in int(FPS * 1.2):
		await process_frame

	# The localized menu remains on screen briefly, then the real shift begins.
	hud._begin_shift()
	player.set_frozen(true)
	var board := _care_interactable("assignment_board")
	if board:
		board.interact(player)
		hud.close_document()
	hud.message_label.modulate.a = 0.0

	await _move_view(Vector3(-17.0, 0.08, 0.18), Vector3(-8.0, 0.08, 0.12),
		Vector3(-5.0, 1.48, 0.0), Vector3(5.0, 1.48, 0.0), 4.8)
	await _hold_view(Vector3(-7.5, 0.08, 0.12), Vector3(4.5, 1.45, -2.3), 1.4)

	# Enter the treatment room and pick up the currently prescribed medicine.
	await _move_view(Vector3(-2.45, 0.08, -2.2), Vector3(-2.0, 0.08, -3.2),
		Vector3(-3.0, 1.30, -4.0), Vector3(-4.15, 1.18, -5.15), 3.8)
	var aminazine := hospital.find_child("interaction_med_aminazine", true, false) as Node3D
	if aminazine:
		care.interact_object("med_aminazine", aminazine)
	await _hold_view(Vector3(-2.0, 0.08, -3.2), Vector3(-4.15, 1.18, -5.15), 2.0)

	# Walk to ward 4 and inspect the assigned patient with the medicine visible
	# in hand and the localized mission panel still active.
	var patient := _patient("saveliev")
	if patient:
		await _move_view(Vector3(7.2, 0.08, -2.2), patient.global_position + Vector3(1.4, 0.08, 0.20),
			Vector3(9.0, 1.45, -4.0), patient.global_position + Vector3(0.0, 0.72, 0.0), 4.2)
		await _hold_view(patient.global_position + Vector3(1.4, 0.08, 0.20),
			patient.global_position + Vector3(0.0, 0.72, 0.0), 2.0)

	# Finish with the game's real danger model and red gaze in the corridor.
	var anomalies := game.get_node("AnomalyManager")
	var orderly: Node3D = anomalies.spawn_hostile_orderly()
	if orderly:
		orderly.set_physics_process(false)
		orderly.global_position = Vector3(7.0, 0.04, 0.0)
		orderly.look_at(Vector3(3.8, 0.04, 0.0), Vector3.UP)
		await _move_view(Vector3(2.8, 0.08, 0.12), Vector3(4.0, 0.08, 0.08),
			Vector3(6.3, 1.45, 0.0), Vector3(7.0, 1.52, 0.0), 3.2)
		await _hold_view(Vector3(4.0, 0.08, 0.08), Vector3(7.0, 1.52, 0.0), 2.0)

	ProgressGuard.restore()
	print("YANDEX_GAMEPLAY_RECORDED locale=%s" % locale)
	quit(0)

func _move_view(from: Vector3, to: Vector3, look_from: Vector3, look_to: Vector3, seconds: float) -> void:
	var frames := maxi(1, int(seconds * FPS))
	for frame in frames:
		var t := float(frame) / float(maxi(1, frames - 1))
		var eased := t * t * (3.0 - 2.0 * t)
		_set_view(from.lerp(to, eased), look_from.lerp(look_to, eased))
		await process_frame

func _hold_view(position: Vector3, target: Vector3, seconds: float) -> void:
	_set_view(position, target)
	for _frame in maxi(1, int(seconds * FPS)):
		await process_frame

func _set_view(position: Vector3, target: Vector3) -> void:
	player.global_position = position
	player.rotation = Vector3.ZERO
	player.head.rotation = Vector3.ZERO
	player.camera.look_at(target, Vector3.UP)

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
