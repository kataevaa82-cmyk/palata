extends SceneTree

# Two defects reached the player because nothing measured whether things sit
# where they belong: a patient whose neck hung 0.23 m through the mattress and
# out under the bed, and door signs whose bottom 85 mm overhung the doorway with
# no wall behind them.
#
# Both are geometry-fitment bugs - the kind a texture, collision or reachability
# test cannot see - so they get their own checks here, against the imported
# model rather than the .blend.

const MAX_SINK := 0.09      # a body may press into the mattress, not through it
const SIGN_MARGIN := 0.002  # a sign must sit inside its own header

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var failures: Array[String] = []
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game: Node = packed.instantiate()
	root.add_child(game)
	while not game.prepared:
		await process_frame
	var hospital: Node3D = game.get_node("HospitalModel")

	# --- patients must rest ON their mattress -------------------------------
	var patients := 0
	for ward in range(1, 7):
		for bed in [1, 2]:
			var patient := hospital.find_child("ward_%d_bed_%d_patient_v3" % [ward, bed], true, false)
			var mattress := hospital.find_child("ward_%d_bed_%d_mattress" % [ward, bed], true, false)
			if not patient or not mattress:
				continue
			patients += 1
			# The blanket is meant to drape over the edge; the body is not.
			var body := _bounds(patient, "blanket")
			var bed_top: float = _bounds(mattress, "").end.y
			var sink: float = bed_top - body.position.y
			if sink > MAX_SINK:
				failures.append("ward%d_bed%d_patient_sunk_%.3fm_into_mattress" % [ward, bed, sink])
			if body.position.y > bed_top + 0.25:
				failures.append("ward%d_bed%d_patient_floats_%.3fm" % [ward, bed, body.position.y - bed_top])

	# --- door signs must be backed by their header --------------------------
	var signs := 0
	for node in _all(hospital):
		if not String(node.name).begins_with("sign_back"):
			continue
		signs += 1
		var plate := _bounds(node, "")
		var header := _header_behind(hospital, plate)
		if header == Rect2():
			failures.append("no_header_behind_%s" % node.name)
			continue
		if plate.position.y < header.position.x - SIGN_MARGIN:
			failures.append("%s_overhangs_%.3fm_below_header" % [
				node.name, header.position.x - plate.position.y])
		if plate.end.y > header.position.y + SIGN_MARGIN:
			failures.append("%s_rises_%.3fm_above_header" % [
				node.name, plate.end.y - header.position.y])

	print("VALIDATE_SCENE_FITMENT patients=%d signs=%d failures=%d" % [patients, signs, failures.size()])
	if failures.is_empty():
		print("VALIDATE_SCENE_FITMENT OK")
	else:
		for failure in failures:
			print("  FAIL ", failure)
	quit(0 if failures.is_empty() else 1)

func _header_behind(hospital: Node3D, plate: AABB) -> Rect2:
	# Returns the header's vertical span as a Rect2(min_y, max_y, 0, 0) - Godot
	# has no "range" type and an AABB would imply a volume this does not need.
	var centre := plate.get_center()
	for node in _all(hospital):
		if not String(node.name).begins_with("opening_header"):
			continue
		var header := _bounds(node, "")
		if centre.x < header.position.x or centre.x > header.end.x:
			continue
		if absf(header.get_center().z - centre.z) > 0.6:
			continue
		return Rect2(header.position.y, header.end.y, 0.0, 0.0)
	return Rect2()

func _bounds(node: Node, skip_substring: String) -> AABB:
	var box := AABB()
	var started := false
	for child in _all(node):
		if not child is MeshInstance3D or not (child as MeshInstance3D).mesh:
			continue
		if not skip_substring.is_empty() and skip_substring in String(child.name).to_lower():
			continue
		var mesh_instance := child as MeshInstance3D
		var world := mesh_instance.global_transform * mesh_instance.get_aabb()
		if not started:
			box = world
			started = true
		else:
			box = box.merge(world)
	return box

func _all(node: Node) -> Array[Node]:
	var out: Array[Node] = [node]
	for child in node.get_children():
		out.append_array(_all(child))
	return out
