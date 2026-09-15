import bpy
import math


def build():
    old = bpy.data.collections.get("INTERACTIVE_PROPS")
    if old:
        for obj in list(old.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old)
    collection = bpy.data.collections.new("INTERACTIVE_PROPS")
    bpy.context.scene.collection.children.link(collection)

    def mat(name, color, rough=0.8, metallic=0.0):
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.diffuse_color = (*color, 1.0)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*color, 1.0)
            bsdf.inputs["Roughness"].default_value = rough
            bsdf.inputs["Metallic"].default_value = metallic
        return m

    metal = mat("MAT_interaction_old_metal", (0.25, 0.30, 0.27), 0.72, 0.35)
    red = mat("MAT_interaction_red_painted_metal", (0.48, 0.045, 0.025), 0.64, 0.08)
    cream = mat("MAT_interaction_aged_plastic", (0.64, 0.59, 0.43), 0.86)
    paper = mat("MAT_interaction_aged_paper", (0.72, 0.65, 0.47), 0.94)
    blue = mat("MAT_interaction_bucket_blue", (0.035, 0.16, 0.31), 0.58, 0.12)
    black = mat("MAT_interaction_black_rubber", (0.025, 0.028, 0.024), 0.96)
    green = mat("MAT_interaction_indicator_green", (0.03, 0.32, 0.12), 0.42)

    def root(name, loc):
        obj = bpy.data.objects.new(name, None)
        collection.objects.link(obj)
        obj.location = loc
        obj["interactive"] = True
        return obj

    def finish(obj, name, parent, loc=(0, 0, 0), material=None, rot=(0, 0, 0)):
        obj.name = name
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        collection.objects.link(obj)
        obj.parent = parent
        obj.location = loc
        obj.rotation_euler = rot
        if material:
            obj.data.materials.append(material)
        if obj.type == "MESH":
            for p in obj.data.polygons:
                p.use_smooth = True
        return obj

    def cube(name, parent, loc, size, material, rot=(0, 0, 0), bevel=0.02):
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
        o = bpy.context.object
        o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        o = finish(o, name, parent, loc, material, rot)
        if bevel:
            mod = o.modifiers.new("soft_edges", "BEVEL")
            mod.width = bevel
            mod.segments = 2
        return o

    def cylinder(name, parent, loc, radius, depth, material, rot=(0, 0, 0), vertices=24):
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=(0, 0, 0))
        return finish(bpy.context.object, name, parent, loc, material, rot)

    def sphere(name, parent, loc, scale, material):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, location=(0, 0, 0))
        o = bpy.context.object
        o.scale = scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        return finish(o, name, parent, loc, material)

    # A wall-mounted Soviet emergency button.
    r = root("interaction_emergency_button", (-1.0, 1.405, 1.34))
    cube("interaction_emergency_button_backplate", r, (0, 0, 0), (0.34, 0.06, 0.43), metal)
    cylinder("interaction_emergency_button_red_cap", r, (0, -0.055, 0.03), 0.105, 0.075, red, (math.pi / 2, 0, 0))
    sphere("interaction_emergency_button_indicator", r, (0.0, -0.105, -0.105), (0.028, 0.012, 0.028), green)

    # Old corridor clock with separate hands.
    r = root("interaction_old_wall_clock", (3.8, 2.46, 2.12))
    cylinder("interaction_old_wall_clock_body", r, (0, 0, 0), 0.34, 0.10, cream, (math.pi / 2, 0, 0), 32)
    cylinder("interaction_old_wall_clock_face", r, (0, -0.06, 0), 0.285, 0.018, paper, (math.pi / 2, 0, 0), 32)
    cube("interaction_old_wall_clock_hand_hour", r, (0.0, -0.078, 0.055), (0.025, 0.015, 0.14), black)
    cube("interaction_old_wall_clock_hand_minute", r, (0.075, -0.080, 0.0), (0.15, 0.015, 0.020), black)

    # Stainless medical cart with drawers and castors.
    r = root("interaction_medical_cart", (-5.0, 1.18, 0.0))
    cube("interaction_medical_cart_body", r, (0, 0, 0.72), (0.92, 0.55, 1.28), metal, bevel=0.04)
    for i, z in enumerate((0.36, 0.64, 0.92, 1.20)):
        cube("interaction_medical_cart_drawer_%d" % i, r, (0, -0.292, z), (0.74, 0.025, 0.18), cream, bevel=0.012)
        cylinder("interaction_medical_cart_handle_%d" % i, r, (0, -0.325, z), 0.018, 0.26, black, (0, math.pi / 2, 0), 16)
    for x in (-0.32, 0.32):
        for y in (-0.18, 0.18):
            cylinder("interaction_medical_cart_wheel", r, (x, y, 0.12), 0.075, 0.045, black, (0, math.pi / 2, 0), 16)

    # Blue cleaning bucket with mop handle, placed as a usable corridor prop.
    r = root("interaction_mop_bucket", (9.0, 1.15, 0.0))
    bpy.ops.mesh.primitive_cone_add(vertices=28, radius1=0.27, radius2=0.22, depth=0.43, location=(0, 0, 0))
    finish(bpy.context.object, "interaction_mop_bucket_body", r, (0, 0, 0.28), blue)
    cylinder("interaction_mop_bucket_rim", r, (0, 0, 0.50), 0.255, 0.035, metal, vertices=28)
    cylinder("interaction_mop_handle", r, (0.22, 0.0, 1.15), 0.018, 1.65, metal, rot=(0.0, math.radians(-9), 0.0), vertices=12)
    sphere("interaction_mop_head", r, (0.35, 0.0, 0.32), (0.18, 0.08, 0.12), paper)

    for c in bpy.context.scene.collection.children:
        c.hide_viewport = c.name != "ASSET_orderly_ghost_v5"
    bpy.ops.wm.save_as_mainfile(filepath="C:/palata/palata_zero.blend")


build()
