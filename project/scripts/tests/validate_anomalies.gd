extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var scene := packed.instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	var manager := scene.get_node("AnomalyManager")
	var failures: Array[String] = []
	if manager.DEFINITIONS.has("facing_wall") or manager.DEFINITIONS.has("child_after_four"):
		failures.append("primitive_corridor_figure_still_enabled")
	for id in manager.DEFINITIONS.keys():
		if not manager.activate(id):
			failures.append(id)
	await process_frame
	print("VALIDATION anomalies=", manager.activated_count, " failures=", failures.size())
	if not failures.is_empty():
		print("FAILED_IDS ", failures)
		quit(1)
	else:
		quit(0)
