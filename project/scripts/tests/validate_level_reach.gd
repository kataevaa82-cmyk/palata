extends SceneTree

# Interaction is a 2.45 m RayCast3D from the player's camera (player.gd
# _find_interactable), not a proximity check. A prop can therefore be visible,
# correctly placed and still impossible to use if its CareInteractionArea sits
# below the ray - which is exactly what a fixed 0.58 box at a floor-rooted
# origin does.
#
# This stands the player in front of every level prop, aims the camera at the
# prop's own centre and asserts the ray resolves to that prop.

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var failures: Array[String] = []
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _frame in 6:
		await process_frame

	var hospital := game.get_node("HospitalModel")
	var levels := game.get_node("LevelManager")
	var player: CharacterBody3D = game.get_node("Player")
	player.set_frozen(true)

	# Test each prop under a night that actually uses it, and run that night's
	# opening incidents first. Night 7 hides Morozov before the note on his
	# pillow matters, and with him visible his own CareInteractionArea covers
	# the bed and intercepts the ray - so "show everything at once" would report
	# a failure the real game never has.
	var owner_night: Dictionary = {}
	for index in LevelManager.level_count():
		for prop_name in LevelManager.LEVELS[index].get("props", []):
			if not owner_night.has(prop_name):
				owner_night[prop_name] = index

	var checked := 0
	for node in get_nodes_in_group("level_props"):
		var prop := node as Node3D
		LevelManager.selected_index = int(owner_night.get(String(prop.name), 0))
		levels.apply_prop_visibility(hospital)
		for beat_key in LevelManager.level().get("beats", {}):
			for beat in LevelManager.level().beats[beat_key]:
				if String(beat[0]) == "incident":
					levels._run_incident(String(beat[1]))
		prop.visible = true
		levels._set_prop_active(prop, true)
		await process_frame
		var area := prop.get_node_or_null("CareInteractionArea") as Area3D
		if not area:
			failures.append("no_area_%s" % prop.name)
			continue
		var shape := area.get_child(0) as CollisionShape3D
		var box := shape.shape as BoxShape3D
		var centre: Vector3 = prop.global_transform * shape.position

		# Approach from whichever horizontal side has the most clearance, at a
		# distance inside the ray's 2.45 m reach.
		var solved := false
		var blockers: Dictionary = {}
		for direction in [Vector3.FORWARD, Vector3.BACK, Vector3.LEFT, Vector3.RIGHT]:
			for distance in [1.1, 1.6]:
				var stand: Vector3 = centre + direction * distance
				var eye_offset: float = player.camera.global_position.y - player.global_position.y
				player.global_position = Vector3(stand.x, 1.62 - eye_offset, stand.z)
				player.head.rotation = Vector3.ZERO
				player.rotation = Vector3.ZERO
				player.camera.look_at(centre, Vector3.UP)
				await process_frame
				player.ray.force_raycast_update()
				var hit: Node = player._find_interactable()
				if hit == prop:
					solved = true
					break
				if player.ray.is_colliding():
					var blocker: Node = player.ray.get_collider()
					blockers[String(blocker.get_parent().name) + "/" + String(blocker.name)] = true
				else:
					blockers["<nothing>"] = true
			if solved:
				break
		checked += 1
		if not solved:
			failures.append("unreachable_%s box=%.2fx%.2fx%.2f@y%.2f blocked_by=%s" % [
				prop.name, box.size.x, box.size.y, box.size.z, shape.position.y,
				",".join(PackedStringArray(blockers.keys()))])

	# The loop above leaves selected_index on whichever night owned the last
	# prop. It is a static, so restore it the way the other level tests do
	# rather than handing an arbitrary night to whatever reads it next.
	LevelManager.selected_index = 0
	print("VALIDATE_LEVEL_REACH checked=%d failures=%d" % [checked, failures.size()])
	if failures.is_empty():
		print("VALIDATE_LEVEL_REACH OK")
	else:
		for failure in failures:
			print("  FAIL ", failure)
	quit(0 if failures.is_empty() else 1)
