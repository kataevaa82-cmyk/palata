extends SceneTree

# Checks the ten added nights end to end without launching the game:
#   - every prop named in LEVEL_PROP_IDS actually arrived in the GLB and bound
#   - per-night visibility really hides the other nights' props (and their
#     colliders, which visibility alone does not switch off)
#   - each night's task list, assignments and beat actions resolve to something
#     the runtime can act on, so no night is unwinnable or silently inert

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var failures: Array[String] = []
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game := packed.instantiate()
	root.add_child(game)
	for _frame in 4:
		await process_frame

	var hospital := game.get_node("HospitalModel")
	var levels := game.get_node("LevelManager")
	var care := game.get_node("CareManager")
	var state := game.get_node("HospitalState")

	# 1. Every declared level prop exists in the imported model and is bound.
	var main_script: Script = game.get_script()
	var prop_ids: Dictionary = main_script.get_script_constant_map()["LEVEL_PROP_IDS"]
	var bound := get_nodes_in_group("level_props")
	for prop_name in prop_ids:
		if not hospital.find_child(prop_name, true, false):
			failures.append("missing_prop_%s" % prop_name)
	if bound.size() != prop_ids.size():
		failures.append("bound_%d_of_%d" % [bound.size(), prop_ids.size()])

	# 2. Task ids, assignment ids and beat verbs resolve for every night.
	var task_names: Dictionary = state.get_script().get_script_constant_map()["TASK_NAMES"]
	var care_constants: Dictionary = care.get_script().get_script_constant_map()
	var assignments: Dictionary = care_constants["ASSIGNMENTS"]
	var object_tasks: Dictionary = care_constants["LEVEL_OBJECT_TASKS"]
	var supplies: Dictionary = care_constants["LEVEL_SUPPLY_ITEMS"]
	var anomaly_defs: Dictionary = game.get_node("AnomalyManager").get_script().get_script_constant_map()["DEFINITIONS"]

	# Which tasks the night can actually complete: care_ ones come from its
	# assignments, obj_ ones from the props it makes visible.
	for index in LevelManager.level_count():
		var level: Dictionary = LevelManager.LEVELS[index]
		var tag := "n%d" % (index + 1)
		var tasks: Array = level.get("tasks", [])
		var reachable := 0
		for task_id in tasks:
			if not task_names.has(task_id):
				failures.append("%s_unknown_task_%s" % [tag, task_id])
				continue
			var id := String(task_id)
			if id.begins_with("care_"):
				var found := false
				for assignment_id in level.get("assignments", []):
					if assignments.has(assignment_id) and String(assignments[assignment_id].task) == id:
						found = true
				if found:
					reachable += 1
				else:
					failures.append("%s_task_%s_has_no_assignment" % [tag, id])
			elif id.begins_with("obj_"):
				var served := ""
				for care_id in object_tasks:
					if String(object_tasks[care_id].task) == id:
						served = String(care_id)
				if served.is_empty():
					failures.append("%s_task_%s_has_no_prop" % [tag, id])
				elif not ("interaction_" + served) in level.get("props", []):
					failures.append("%s_task_%s_prop_hidden" % [tag, id])
				else:
					reachable += 1
			else:
				reachable += 1
		var required := int(level.get("required", 0))
		if required > reachable:
			failures.append("%s_needs_%d_but_only_%d_reachable" % [tag, required, reachable])

		# Assignments must exist, and any item they need must be obtainable.
		for assignment_id in level.get("assignments", []):
			if not assignments.has(assignment_id):
				failures.append("%s_unknown_assignment_%s" % [tag, assignment_id])
				continue
			var item := String(assignments[assignment_id].item)
			if item.is_empty():
				continue
			var obtainable: bool = item in care_constants["SUPPLY_ITEMS"].values()
			for care_id in supplies:
				if String(supplies[care_id]) == item:
					if ("interaction_" + care_id) in level.get("props", []):
						obtainable = true
			if not obtainable:
				failures.append("%s_item_%s_unobtainable" % [tag, item])

		# Beats must name real calls, anomalies and prop-bearing incidents.
		for key in level.get("beats", {}):
			for beat in level.beats[key]:
				var verb := String(beat[0])
				if verb == "anomaly" and not anomaly_defs.has(String(beat[1])):
					failures.append("%s_%s_bad_anomaly_%s" % [tag, key, beat[1]])
				elif verb == "call":
					var call_type := String(beat[1])
					if call_type.begins_with("care_"):
						var wanted := call_type.trim_prefix("care_")
						if not assignments.has(wanted):
							failures.append("%s_%s_bad_call_%s" % [tag, key, call_type])
						elif not wanted in level.get("assignments", []):
							failures.append("%s_%s_call_%s_not_in_assignments" % [tag, key, wanted])
				elif verb == "spawn" and not String(beat[1]) in ["orderly", "hostile", "nurse", "violent"]:
					failures.append("%s_%s_bad_spawn_%s" % [tag, key, beat[1]])
		for anomaly_id in level.get("anomalies", []):
			if not anomaly_defs.has(String(anomaly_id)):
				failures.append("%s_bad_pool_%s" % [tag, anomaly_id])

		# Story triggers replace the old clock dispatch. Every referenced bundle
		# and every semantic task condition must resolve within this night.
		var trigger_ids: Dictionary = {}
		for trigger in LevelManager.STORY_TRIGGERS.get(String(level.id), []):
			var trigger_id := String(trigger.get("id", ""))
			if trigger_id.is_empty() or trigger_ids.has(trigger_id):
				failures.append("%s_bad_trigger_id_%s" % [tag, trigger_id])
			trigger_ids[trigger_id] = true
			var beat_key := String(trigger.get("beat", ""))
			if not level.get("beats", {}).has(beat_key):
				failures.append("%s_trigger_%s_missing_beat_%s" % [tag, trigger_id, beat_key])
			for condition in ["all", "any"]:
				for task_id in trigger.get(condition, []):
					if not String(task_id) in tasks:
						failures.append("%s_trigger_%s_unknown_task_%s" % [tag, trigger_id, task_id])
		for task_id in LevelManager.ENDING_REQUIREMENTS.get(String(level.id), []):
			if not String(task_id) in tasks:
				failures.append("%s_bad_ending_requirement_%s" % [tag, task_id])

	# 3. Visibility whitelist: switching nights must swap what is standing in
	#    the ward, and hidden props must lose their colliders too.
	for index in [0, 3, 10]:
		LevelManager.selected_index = index
		levels.apply_prop_visibility(hospital)
		var allowed: Array = LevelManager.level().get("props", [])
		var hidden: Array = LevelManager.HIDDEN_STORY_PROPS.get(String(LevelManager.level().id), [])
		for node in get_nodes_in_group("level_props"):
			var should_show: bool = String(node.name) in allowed and not String(node.name) in hidden
			if node.visible != should_show:
				failures.append("n%d_visibility_%s" % [index + 1, node.name])
			if not should_show:
				for body in _colliders(node):
					if body.collision_layer != 0:
						failures.append("n%d_live_collider_%s" % [index + 1, node.name])
						break

	LevelManager.selected_index = 0
	print("VALIDATE_LEVELS props=%d nights=%d failures=%d" % [bound.size(), LevelManager.level_count(), failures.size()])
	if failures.is_empty():
		print("VALIDATE_LEVELS OK")
	else:
		for failure in failures:
			print("  FAIL ", failure)
	quit(0 if failures.is_empty() else 1)

func _colliders(node: Node) -> Array[Node]:
	var out: Array[Node] = []
	for child in node.get_children():
		if child is StaticBody3D or (child is Area3D and String(child.name) == "CareInteractionArea"):
			out.append(child)
		out.append_array(_colliders(child))
	return out
