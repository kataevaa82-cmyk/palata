import bpy
import math


def rebuild():
    def material(name, color, dark=None, roughness=0.8):
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.diffuse_color = (*color, 1.0)
        m.use_nodes = True
        nodes = m.node_tree.nodes
        links = m.node_tree.links
        nodes.clear()
        out = nodes.new("ShaderNodeOutputMaterial")
        shader = nodes.new("ShaderNodeBsdfPrincipled")
        shader.inputs["Roughness"].default_value = roughness
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 5.5
        noise.inputs["Detail"].default_value = 3.2
        noise.inputs["Roughness"].default_value = 0.68
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (*(dark or tuple(max(0.0, x * 0.55) for x in color)), 1.0)
        ramp.color_ramp.elements[1].color = (*color, 1.0)
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.10
        bump.inputs["Distance"].default_value = 0.025
        links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], shader.inputs["Normal"])
        links.new(shader.outputs["BSDF"], out.inputs["Surface"])
        return m

    wood = material("MAT_old_solid_wood_doors", (0.34, 0.19, 0.085), (0.12, 0.055, 0.022), 0.84)
    floor = material("MAT_marble_chips_floor", (0.39, 0.43, 0.37), (0.16, 0.18, 0.15), 0.92)
    metal = bpy.data.materials.get("MAT_interaction_old_metal")
    blue = bpy.data.materials.get("MAT_interaction_bucket_blue")
    paper = bpy.data.materials.get("MAT_interaction_aged_paper")
    black = bpy.data.materials.get("MAT_interaction_black_rubber")
    if not metal:
        metal = material("MAT_interaction_old_metal", (0.25, 0.30, 0.27), roughness=0.72)
    if not blue:
        blue = material("MAT_interaction_bucket_blue", (0.035, 0.16, 0.31), roughness=0.58)
    if not paper:
        paper = material("MAT_interaction_aged_paper", (0.72, 0.65, 0.47), roughness=0.94)
    if not black:
        black = material("MAT_interaction_black_rubber", (0.025, 0.028, 0.024), roughness=0.96)

    def assign(obj, mat):
        if obj.type != "MESH":
            return
        obj.data.materials.clear()
        obj.data.materials.append(mat)

    # Wooden doors: remove the glass look by assigning the same solid wood to
    # slabs, frames, panels and former glass inserts.
    door_prefixes = ("hospital_door_", "door_glass_", "doorframe_", "doorframe_top_", "door_detail", "ANOMALY_room_zero_door")
    for obj in bpy.data.objects:
        if obj.name.startswith(door_prefixes):
            assign(obj, wood)

    # Marble-chip floor across all floor modules.
    for obj in bpy.data.objects:
        low = obj.name.lower()
        if any(token in low for token in ("floor", "linoleum", "floor_track")):
            assign(obj, floor)

    # Replace the simple bucket/mop with a sturdier janitor set.
    collection = bpy.data.collections.get("INTERACTIVE_PROPS")
    if collection:
        old_root = bpy.data.objects.get("interaction_mop_bucket")
        if old_root:
            bpy.data.objects.remove(old_root, do_unlink=True)
        root = bpy.data.objects.new("interaction_mop_bucket", None)
        collection.objects.link(root)
        root.location = (9.0, 1.15, 0.0)
        root["interactive"] = True

        def finish(obj, name, loc, mat, rot=(0, 0, 0)):
            obj.name = name
            for owner in list(obj.users_collection):
                owner.objects.unlink(obj)
            collection.objects.link(obj)
            obj.parent = root
            obj.location = loc
            obj.rotation_euler = rot
            obj.data.materials.append(mat)
            for poly in obj.data.polygons:
                poly.use_smooth = True
            return obj

        def cube(name, loc, size, mat, rot=(0, 0, 0)):
            bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
            o = bpy.context.object
            o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            return finish(o, name, loc, mat, rot)

        def cylinder(name, loc, radius, depth, mat, rot=(0, 0, 0), vertices=28):
            bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=(0, 0, 0))
            return finish(bpy.context.object, name, loc, mat, rot)

        def sphere(name, loc, scale, mat):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=14, location=(0, 0, 0))
            o = bpy.context.object
            o.scale = scale
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            return finish(o, name, loc, mat)

        bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.28, radius2=0.235, depth=0.46, location=(0, 0, 0))
        finish(bpy.context.object, "interaction_mop_bucket_body", (0, 0, 0.29), blue)
        cylinder("interaction_mop_bucket_bottom_ring", (0, 0, 0.075), 0.25, 0.035, metal, vertices=32)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.255, minor_radius=0.018, major_segments=32, minor_segments=8, location=(0, 0, 0))
        finish(bpy.context.object, "interaction_mop_bucket_rim", (0, 0, 0.525), metal)
        cylinder("interaction_mop_handle", (0.20, 0.0, 1.18), 0.020, 1.78, metal, (0.0, math.radians(-8), 0.0), 16)
        cylinder("interaction_mop_grip", (0.325, 0.0, 2.05), 0.035, 0.24, black, (0.0, math.pi / 2, 0.0), 16)
        cube("interaction_mop_head_block", (0.36, 0.0, 0.33), (0.34, 0.16, 0.13), metal)
        for y in (-0.07, -0.035, 0.0, 0.035, 0.07):
            sphere("interaction_mop_string", (0.36, y, 0.23), (0.025, 0.018, 0.14), paper)

    for c in bpy.context.scene.collection.children:
        c.hide_viewport = c.name != "ASSET_orderly_ghost_v5"
    bpy.ops.wm.save_as_mainfile(filepath="C:/palata/palata_zero.blend")


rebuild()
