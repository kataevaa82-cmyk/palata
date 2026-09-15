extends SceneTree

const ProgressGuard := preload("res://scripts/tests/progress_guard.gd")

# In-engine shots of the seven props rebuilt in
# tools/geometry/improve_level_prop_geometry.py. A Blender render is not proof:
# the ward's own materials, fog and runtime lights are what the player sees, and
# a prop can also end up half inside the furniture it stands on.
#
# The viewpoint is not hand-authored. Each prop is approached from whichever
# side the interaction ray actually resolves to it - the same search
# validate_level_reach.gd does - so the shot is taken from a spot the player can
# really stand in and use the prop from.

const SHOTS := [
	[1, "oxygen_pillow", "interaction_oxygen_pillow"],
	[3, "body_bag", "interaction_body_bag"],
	[5, "window_latch", "interaction_window_latch"],
	[5, "blanket_stack", "interaction_blanket_stack"],
	[5, "radiator_valve", "interaction_radiator_valve"],
	[6, "hospital_slippers", "interaction_hospital_slippers"],
	[6, "muddy_trail", "interaction_muddy_trail"],
]

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	ProgressGuard.snapshot()
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _i in 14:
		await process_frame

	var hud := game.get_node("HUD")
	var levels := game.get_node("LevelManager")
	var hospital := game.get_node("HospitalModel")
	var player: CharacterBody3D = game.get_node("Player")
	for child in hud.get_children():
		if child is CanvasItem:
			child.visible = false
	player.set_frozen(true)

	var failures := 0
	for shot in SHOTS:
		var index: int = shot[0]
		var shot_name: String = shot[1]
		var prop_name: String = shot[2]
		LevelManager.selected_index = index
		levels.apply_prop_visibility(hospital)
		var prop := hospital.find_child(prop_name, true, false) as Node3D
		if not prop:
			print("MISSING ", prop_name)
			failures += 1
			continue
		var area := prop.get_node_or_null("CareInteractionArea") as Area3D
		var shape := area.get_child(0) as CollisionShape3D
		var centre: Vector3 = prop.global_transform * shape.position

		var framed := false
		for direction in [Vector3.FORWARD, Vector3.BACK, Vector3.LEFT, Vector3.RIGHT]:
			for distance in [1.1, 1.5]:
				var stand: Vector3 = centre + direction * distance
				var eye_offset: float = player.camera.global_position.y - player.global_position.y
				player.global_position = Vector3(stand.x, 1.62 - eye_offset, stand.z)
				player.head.rotation = Vector3.ZERO
				player.rotation = Vector3.ZERO
				player.camera.look_at(centre, Vector3.UP)
				await process_frame
				player.ray.force_raycast_update()
				if player._find_interactable() == prop:
					framed = true
					break
			if framed:
				break
		if not framed:
			print("NO_VIEWPOINT ", prop_name)
			failures += 1
			continue
		for _i in 6:
			await process_frame
		await RenderingServer.frame_post_draw
		var image := root.get_texture().get_image()
		var error := image.save_png("C:/palata/build/prop_review/ingame_%s.png" % shot_name)
		print("SHOT %s bbox=%.2fx%.2fx%.2f error=%d" % [shot_name, shape.shape.size.x,
			shape.shape.size.y, shape.shape.size.z, error])

	LevelManager.selected_index = 0
	print("CAPTURE_IMPROVED_PROPS failures=", failures)
	ProgressGuard.restore()
	quit(0 if failures == 0 else 1)
