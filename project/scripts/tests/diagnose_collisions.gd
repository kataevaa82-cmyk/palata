extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _i in 30:
		await process_frame
	var hospital: Node = game.get_node("HospitalModel")

	# Where is the visible corridor wall surface, and does it block?
	for wanted in ["corridor_N_4_L_lower", "corridor_N_4_L_upper"]:
		var node := hospital.find_child(wanted, true, false) as MeshInstance3D
		if node and node.mesh:
			var world: AABB = node.global_transform * node.mesh.get_aabb()
			print(wanted, " z=[", world.position.z, " .. ", world.end.z,
				"] collision=", node.get_node_or_null("RuntimeCollision") != null)

	var player: CharacterBody3D = game.get_node("Player")
	player.set_frozen(true)
	for child in player.get_children():
		if child is CollisionShape3D and (child as CollisionShape3D).shape is CapsuleShape3D:
			var capsule := (child as CollisionShape3D).shape as CapsuleShape3D
			print("PLAYER_CAPSULE radius=", capsule.radius, " height=", capsule.height)

	player.global_position = Vector3(-5.0, 0.08, 0.0)
	player.velocity = Vector3.ZERO
	for _step in 300:
		player.velocity = Vector3(0.0, -2.0, 6.0)
		player.move_and_slide()
	print("PLAYER_STOPS_AT z=", player.global_position.z,
		"  CAMERA z=", player.camera.global_position.z)
	quit(0)
