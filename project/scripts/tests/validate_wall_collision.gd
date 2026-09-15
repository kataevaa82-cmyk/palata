extends SceneTree

# Physics containment test. Node counting is not enough: the corridor cladding
# (corridor_N_*/corridor_S_*) had no collision at all yet the player still
# stopped, because a structural wall sits behind it. "Collisions exist" and
# "you cannot pass" are different questions; only the second one is the bug.
#
# Wards sit every 5 m along X on both sides of the corridor, so the partition
# between two neighbouring wards is 2.5 m from a ward's centre.

const PUSH_STEPS := 300
const WARD_HALF_SPAN := 2.5
const ROOM_XS := [-17.5, -12.5, -7.5, -2.5, 2.5, 7.5, 12.5, 17.5]

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _i in 30:
		await process_frame

	var player: CharacterBody3D = game.get_node("Player")
	player.set_frozen(true)

	var breaches: Array[String] = []
	var probes := 0
	for room_z in [-3.8, 3.8]:
		for room_x in ROOM_XS:
			for direction in [1.0, -1.0]:
				# Skip pushes that lead off the end of the building.
				if (room_x == ROOM_XS[0] and direction < 0.0) \
						or (room_x == ROOM_XS[-1] and direction > 0.0):
					continue
				player.global_position = Vector3(room_x, 0.08, room_z)
				player.velocity = Vector3.ZERO
				for _step in PUSH_STEPS:
					player.velocity = Vector3(direction * 6.0, -2.0, 0.0)
					player.move_and_slide()
				probes += 1
				var p := player.global_position
				var travelled: float = absf(p.x - room_x)
				# Still deep in the ward band but past the partition = went through it.
				if travelled > WARD_HALF_SPAN + 0.5 and absf(p.z) > 1.7:
					breaches.append("ward(%.1f,%.1f) dir%+.0f -> x=%.2f z=%.2f"
						% [room_x, room_z, direction, p.x, p.z])

	print("PARTITION_TEST probes=", probes, " breaches=", breaches.size())
	for entry in breaches:
		print("  THROUGH_WALL ", entry)
	quit(0 if breaches.is_empty() else 1)
