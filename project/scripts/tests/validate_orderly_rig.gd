extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var packed: PackedScene = load("res://assets/models/orderly_ghost_v6.glb")
	if not packed:
		push_error("ORDERLY_RIG missing scene")
		quit(1)
		return
	var orderly := packed.instantiate()
	root.add_child(orderly)
	await process_frame
	var skeleton: Skeleton3D
	var animation_player: AnimationPlayer
	var meshes := 0
	for node in _all_nodes(orderly):
		if node is Skeleton3D:
			skeleton = node
		elif node is AnimationPlayer:
			animation_player = node
		elif node is MeshInstance3D:
			meshes += 1
	var failures: Array[String] = []
	var bucket := orderly.find_child("ghost_bucket_pivot", true, false) as Node3D
	var grip := orderly.find_child("ghost_blue_bucket_grip", true, false) as Node3D
	var palm := orderly.find_child("ghost_r_palm", true, false) as Node3D
	var bucket_held := (
		bucket != null
		and bucket.get_parent() != null
		and String(bucket.get_parent().name) == "ghost_r_arm_pivot"
		and grip != null
		and palm != null
		and grip.global_position.distance_to(palm.global_position) < 0.12
	)
	if not skeleton or skeleton.get_bone_count() < 15:
		failures.append("skeleton_bones")
	if not animation_player or animation_player.get_animation_list().is_empty():
		failures.append("walk_animation")
	if meshes < 40:
		failures.append("ghost_meshes")
	if not bucket_held:
		failures.append("bucket_not_held")
	print(
		"ORDERLY_RIG bones=", skeleton.get_bone_count() if skeleton else 0,
		" animations=", animation_player.get_animation_list().size() if animation_player else 0,
		" meshes=", meshes,
		" bucket_held=", bucket_held,
		" failures=", failures.size()
	)
	quit(0 if failures.is_empty() else 1)

func _all_nodes(node: Node) -> Array[Node]:
	var result: Array[Node] = [node]
	for child in node.get_children():
		result.append_array(_all_nodes(child))
	return result
