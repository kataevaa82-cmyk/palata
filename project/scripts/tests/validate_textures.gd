extends SceneTree

# "Does everything have a texture?" is a question about the runtime, not Blender.
# material_system.gd swaps each imported material for a procedural shader, but
# it skips a surface entirely when the imported mesh carries no material
# (`if not source: continue`) - such a surface renders as flat default grey.
#
# Categories are not all failures: _category_for returns -1 on purpose for
# glass, water, screens, mirrors and light emitters, which must stay smooth.
# This reports the three groups separately so a real gap is visible.

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _frame in 5:
		await process_frame

	var hospital := game.get_node("HospitalModel")
	var materials := game.get_node("MaterialSystem")

	var surfaces := 0
	var no_material: Array[String] = []
	var deliberate_skips := 0
	var textured := 0
	var untextured_names: Dictionary = {}

	for node in _all(hospital):
		if not node is MeshInstance3D:
			continue
		var mesh_instance := node as MeshInstance3D
		if not mesh_instance.mesh:
			continue
		for surface in mesh_instance.mesh.get_surface_count():
			surfaces += 1
			var source: Material = mesh_instance.mesh.surface_get_material(surface)
			if not source:
				no_material.append(String(mesh_instance.name))
				continue
			var category: int = materials._category_for(
				String(mesh_instance.name).to_lower(), String(source.resource_name).to_lower())
			if category < 0:
				deliberate_skips += 1
				continue
			if mesh_instance.get_surface_override_material(surface) is ShaderMaterial:
				textured += 1
			else:
				untextured_names[String(mesh_instance.name)] = true

	print("VALIDATE_TEXTURES surfaces=%d textured=%d smooth_by_design=%d no_material=%d not_applied=%d" % [
		surfaces, textured, deliberate_skips, no_material.size(), untextured_names.size()])

	var failures := no_material.size() + untextured_names.size()
	if failures == 0:
		print("VALIDATE_TEXTURES OK — every surface either textured or smooth by design")
	else:
		var seen: Dictionary = {}
		for name in no_material:
			if not seen.has(name):
				seen[name] = true
				print("  NO_MATERIAL ", name)
		for name in untextured_names:
			print("  NOT_APPLIED ", name)
	quit(0 if failures == 0 else 1)

func _all(node: Node) -> Array[Node]:
	var out: Array[Node] = [node]
	for child in node.get_children():
		out.append_array(_all(child))
	return out
