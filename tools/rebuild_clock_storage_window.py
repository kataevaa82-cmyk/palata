import math

import bpy
from mathutils import Vector


BLEND_PATH = "C:/palata/palata_zero.blend"
ROOM_COLLECTION = "EAST_MEDICAL_STORAGE_V1"
GAMEPLAY_COLLECTION = "GAMEPLAY_CARE_PROPS_V2"


def remove_tree(root):
    if root is None:
        return
    descendants = list(root.children_recursive)
    for child in reversed(descendants):
        if child and child.name in bpy.data.objects:
            bpy.data.objects.remove(child, do_unlink=True)
    if root.name in bpy.data.objects:
        bpy.data.objects.remove(root, do_unlink=True)


def reset_collection(name):
    old = bpy.data.collections.get(name)
    if old:
        for obj in list(old.all_objects):
            if obj and obj.name in bpy.data.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old)
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def procedural_material(name, base, dark, roughness=0.9, metallic=0.0, noise_scale=8.0, bump=0.08, emission=None, alpha=1.0):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.diffuse_color = (*base, alpha)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    noise = nodes.new("ShaderNodeTexNoise")
    ramp = nodes.new("ShaderNodeValToRGB")
    bump_node = nodes.new("ShaderNodeBump")
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = 3.5
    noise.inputs["Roughness"].default_value = 0.72
    ramp.color_ramp.elements[0].color = (*dark, 1.0)
    ramp.color_ramp.elements[0].position = 0.20
    ramp.color_ramp.elements[1].color = (*base, 1.0)
    ramp.color_ramp.elements[1].position = 0.82
    shader.inputs["Base Color"].default_value = (*base, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    if alpha < 1.0:
        shader.inputs["Alpha"].default_value = alpha
        material.surface_render_method = "DITHERED"
    if emission and "Emission Color" in shader.inputs:
        shader.inputs["Emission Color"].default_value = (*emission, 1.0)
        shader.inputs["Emission Strength"].default_value = 2.6
    bump_node.inputs["Strength"].default_value = bump
    bump_node.inputs["Distance"].default_value = 0.012
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump_node.inputs["Height"])
    links.new(bump_node.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def link_object(obj, name, collection, material=None, parent=None):
    obj.name = name
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    if material and hasattr(obj.data, "materials"):
        obj.data.materials.append(material)
    if obj.type == "MESH":
        for polygon in obj.data.polygons:
            polygon.use_smooth = False
    if parent:
        obj.parent = parent
    return obj


def empty(name, location, collection, rotation=(0.0, 0.0, 0.0)):
    obj = bpy.data.objects.new(name, None)
    collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    return obj


def cube(name, location, size, material, collection, parent=None, rotation=(0.0, 0.0, 0.0), bevel=0.015):
    bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, 0.0))
    obj = bpy.context.object
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = tuple(value * 0.5 for value in size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0.0:
        modifier = obj.modifiers.new("soft_worn_edges", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
    return link_object(obj, name, collection, material, parent)


def cylinder(name, location, radius, depth, material, collection, parent=None, rotation=(0.0, 0.0, 0.0), vertices=32, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=(0.0, 0.0, 0.0))
    obj = bpy.context.object
    obj.location = location
    obj.rotation_euler = rotation
    if bevel > 0.0:
        modifier = obj.modifiers.new("rounded_edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
    return link_object(obj, name, collection, material, parent)


def sphere(name, location, scale, material, collection, parent=None, segments=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=16, location=(0.0, 0.0, 0.0))
    obj = bpy.context.object
    obj.location = location
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return link_object(obj, name, collection, material, parent)


def torus(name, location, major_radius, minor_radius, material, collection, parent=None, rotation=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_radius, minor_radius=minor_radius, major_segments=48, minor_segments=12, location=(0.0, 0.0, 0.0))
    obj = bpy.context.object
    obj.location = location
    obj.rotation_euler = rotation
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return link_object(obj, name, collection, material, parent)


def curve(name, points, bevel_depth, material, collection, parent=None):
    data = bpy.data.curves.new(name + "_curve", "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = bevel_depth
    data.bevel_resolution = 2
    spline = data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, coordinate in zip(spline.bezier_points, points):
        point.co = coordinate
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    data.materials.append(material)
    if parent:
        obj.parent = parent
    return obj


def text(name, body, location, size, material, collection, parent=None, rotation=(math.pi / 2.0, 0.0, 0.0), extrude=0.002):
    data = bpy.data.curves.new(name + "_font", "FONT")
    data.body = body
    data.align_x = "CENTER"
    data.align_y = "CENTER"
    data.size = size
    data.extrude = extrude
    data.bevel_depth = min(extrude * 0.30, 0.001)
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    data.materials.append(material)
    if parent:
        obj.parent = parent
    return obj


def box_between(name, start, end, width, depth, material, collection, parent=None):
    start_vector = Vector(start)
    end_vector = Vector(end)
    direction = end_vector - start_vector
    obj = cube(name, (start_vector + end_vector) * 0.5, (width, depth, direction.length), material, collection, parent, bevel=width * 0.22)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    obj.rotation_mode = "XYZ"
    return obj


MAT_BAKELITE = procedural_material("MAT_clock_bakelite_v3", (0.16, 0.075, 0.032), (0.018, 0.009, 0.004), 0.72, 0.0, 12.0, 0.09)
MAT_CLOCK_FACE = procedural_material("MAT_clock_face_aged_v3", (0.68, 0.64, 0.48), (0.29, 0.22, 0.12), 0.96, 0.0, 7.0, 0.035)
MAT_CLOCK_INK = procedural_material("MAT_clock_ink_v3", (0.018, 0.014, 0.010), (0.002, 0.001, 0.001), 0.82, 0.0, 5.0, 0.02)
MAT_CLOCK_RED = procedural_material("MAT_clock_second_red_v3", (0.42, 0.018, 0.008), (0.08, 0.002, 0.001), 0.60, 0.05, 6.0, 0.02)
MAT_METAL = procedural_material("MAT_storage_old_metal", (0.28, 0.31, 0.27), (0.055, 0.065, 0.048), 0.80, 0.32, 11.0, 0.11)
MAT_ENAMEL = procedural_material("MAT_storage_enamel", (0.47, 0.54, 0.45), (0.075, 0.095, 0.072), 0.90, 0.08, 9.0, 0.07)
MAT_WOOD = procedural_material("MAT_storage_old_wood", (0.24, 0.13, 0.065), (0.035, 0.018, 0.008), 0.94, 0.0, 7.0, 0.12)
MAT_CANVAS = procedural_material("MAT_storage_canvas", (0.48, 0.42, 0.27), (0.13, 0.10, 0.05), 0.99, 0.0, 22.0, 0.16)
MAT_PAPER = procedural_material("MAT_storage_paper", (0.66, 0.62, 0.45), (0.23, 0.18, 0.09), 0.98, 0.0, 14.0, 0.035)
MAT_RUBBER = procedural_material("MAT_storage_rubber", (0.022, 0.026, 0.021), (0.002, 0.003, 0.002), 0.95, 0.0, 8.0, 0.08)
MAT_OXYGEN = procedural_material("MAT_storage_oxygen", (0.12, 0.29, 0.25), (0.015, 0.055, 0.045), 0.74, 0.38, 9.0, 0.08)
MAT_NIGHT = procedural_material("MAT_storage_window_night", (0.003, 0.008, 0.018), (0.0003, 0.001, 0.004), 0.47, 0.0, 4.0, 0.015)
MAT_MOON = procedural_material("MAT_storage_window_moon", (0.48, 0.53, 0.55), (0.17, 0.20, 0.22), 0.66, 0.0, 5.0, 0.02, emission=(0.18, 0.24, 0.30))
MAT_GLASS = procedural_material("MAT_storage_window_glass", (0.16, 0.22, 0.22), (0.02, 0.035, 0.04), 0.28, 0.0, 6.0, 0.015, alpha=0.24)


def rebuild_clock():
    old_clock = bpy.data.objects.get("corridor_clock_v2")
    remove_tree(old_clock)
    props = bpy.data.collections.get("PROPS") or bpy.context.scene.collection
    root = empty("corridor_clock_v2", (0.0, 1.47, 2.40), props)
    root["asset_type"] = "soviet_wall_clock"
    root["version"] = 3
    cylinder("corridor_clock_v3_case", (0.0, 0.0, 0.0), 0.365, 0.13, MAT_BAKELITE, props, root, (math.pi / 2.0, 0.0, 0.0), 64, 0.012)
    torus("corridor_clock_v3_bezel", (0.0, -0.072, 0.0), 0.323, 0.025, MAT_BAKELITE, props, root, (math.pi / 2.0, 0.0, 0.0))
    cylinder("corridor_clock_v3_dial", (0.0, -0.073, 0.0), 0.306, 0.012, MAT_CLOCK_FACE, props, root, (math.pi / 2.0, 0.0, 0.0), 64)
    for minute in range(60):
        angle = math.radians(minute * 6.0)
        radius = 0.275 if minute % 5 else 0.268
        length = 0.018 if minute % 5 else 0.035
        center = (math.sin(angle) * radius, -0.084, math.cos(angle) * radius)
        tick = cube(
            "corridor_clock_v3_minute_tick",
            center,
            (0.004 if minute % 5 else 0.008, 0.006, length),
            MAT_CLOCK_INK,
            props,
            root,
            bevel=0.001,
        )
        tick.rotation_euler.y = angle
    for number in range(1, 13):
        angle = math.radians(number * 30.0)
        location = (math.sin(angle) * 0.222, -0.091, math.cos(angle) * 0.222)
        text("corridor_clock_v3_numeral", str(number), location, 0.060 if number < 10 else 0.050, MAT_CLOCK_INK, props, root)
    text("corridor_clock_v3_brand", "ЯНТАРЬ", (0.0, -0.092, -0.112), 0.022, MAT_CLOCK_INK, props, root)
    text("corridor_clock_v3_origin", "СССР", (0.0, -0.092, -0.145), 0.016, MAT_CLOCK_INK, props, root)

    def clock_point(angle_degrees, length):
        angle = math.radians(angle_degrees)
        return (math.sin(angle) * length, -0.104, math.cos(angle) * length)

    box_between("corridor_clock_v3_hour_hand", (0.0, -0.104, 0.0), clock_point(98.5, 0.155), 0.020, 0.009, MAT_CLOCK_INK, props, root)
    box_between("corridor_clock_v3_minute_hand", (0.0, -0.106, 0.0), clock_point(102.0, 0.230), 0.011, 0.008, MAT_CLOCK_INK, props, root)
    box_between("corridor_clock_v3_second_hand", clock_point(282.0, 0.050), clock_point(102.0, 0.252), 0.004, 0.005, MAT_CLOCK_RED, props, root)
    cylinder("corridor_clock_v3_center_pin", (0.0, -0.114, 0.0), 0.021, 0.018, MAT_BAKELITE, props, root, (math.pi / 2.0, 0.0, 0.0), 24)
    cylinder("corridor_clock_v3_glass", (0.0, -0.119, 0.0), 0.312, 0.008, MAT_GLASS, props, root, (math.pi / 2.0, 0.0, 0.0), 64)
    return root


def rebuild_storage_room():
    for root_name in ("care_stair_restraint_cabinet", "care_emergency_restraint_cabinet", "interaction_patient_restraints"):
        remove_tree(bpy.data.objects.get(root_name))
    stair_roots = [
        obj for obj in list(bpy.data.objects)
        if obj and obj.parent is None and (obj.name == "stair_railing_v2" or obj.name.startswith("stair_step"))
    ]
    for root in stair_roots:
        remove_tree(root)

    room = reset_collection(ROOM_COLLECTION)
    gameplay = bpy.data.collections.get(GAMEPLAY_COLLECTION)
    if gameplay is None:
        gameplay = bpy.data.collections.new(GAMEPLAY_COLLECTION)
        bpy.context.scene.collection.children.link(gameplay)

    sign = bpy.data.objects.get("sign_text_1_7")
    if sign and sign.type == "FONT":
        sign.data.body = "МЕДСКЛАД"
        sign.data.align_x = "CENTER"
        sign.data.size = 0.115

    # Steel shelving against the west wall, leaving a broad entrance route.
    rack = empty("medical_storage_rack", (15.34, 4.56, 0.0), room)
    for y in (-0.92, 0.92):
        for x in (-0.18, 0.18):
            cube("medical_storage_rack_post", (x, y, 1.08), (0.055, 0.055, 2.16), MAT_METAL, room, rack, bevel=0.008)
    for z in (0.22, 0.72, 1.22, 1.72, 2.14):
        cube("medical_storage_rack_shelf", (0.0, 0.0, z), (0.46, 1.95, 0.055), MAT_METAL, room, rack, bevel=0.010)
    for index, (y, z, width) in enumerate(((-0.60, 0.47, 0.58), (0.42, 0.47, 0.66), (-0.48, 0.97, 0.62), (0.48, 1.47, 0.60))):
        cube(f"medical_storage_supply_crate_{index}", (0.0, y, z), (0.36, width, 0.34), MAT_WOOD if index % 2 else MAT_ENAMEL, room, rack, bevel=0.025)
        cube(f"medical_storage_crate_label_{index}", (-0.195, y, z), (0.012, width * 0.55, 0.16), MAT_PAPER, room, rack, bevel=0.004)
    for y in (-0.68, 0.0, 0.68):
        cylinder("medical_storage_bandage_roll", (-0.02, y, 1.94), 0.11, 0.24, MAT_CANVAS, room, rack, (0.0, math.pi / 2.0, 0.0), 24)

    # Oxygen cylinders and their wheeled retaining cradle.
    oxygen = empty("medical_storage_oxygen_station", (19.35, 2.55, 0.0), room)
    for x in (-0.19, 0.19):
        cylinder("medical_storage_oxygen_cylinder", (x, 0.0, 0.68), 0.15, 1.18, MAT_OXYGEN, room, oxygen, vertices=32, bevel=0.015)
        sphere("medical_storage_oxygen_shoulder", (x, 0.0, 1.27), (0.15, 0.15, 0.17), MAT_OXYGEN, room, oxygen, 24)
        cylinder("medical_storage_oxygen_valve", (x, 0.0, 1.46), 0.038, 0.18, MAT_METAL, room, oxygen, vertices=16)
        torus("medical_storage_oxygen_wheel", (x, 0.0, 1.57), 0.07, 0.012, MAT_METAL, room, oxygen)
    cube("medical_storage_oxygen_cradle", (0.0, 0.0, 0.22), (0.62, 0.42, 0.18), MAT_METAL, room, oxygen, bevel=0.025)

    # Folded canvas stretcher hung flat on the east wall.
    stretcher = empty("medical_storage_folded_stretcher", (20.22, 3.40, 1.33), room, (0.0, 0.0, -math.pi / 2.0))
    for x in (-0.28, 0.28):
        cylinder("medical_storage_stretcher_pole", (x, 0.0, 0.0), 0.026, 1.70, MAT_METAL, room, stretcher, vertices=18)
        for z in (-0.91, 0.91):
            cube("medical_storage_stretcher_grip", (x, 0.0, z), (0.075, 0.075, 0.24), MAT_RUBBER, room, stretcher, bevel=0.018)
    cube("medical_storage_stretcher_canvas", (0.0, 0.025, 0.0), (0.54, 0.035, 1.58), MAT_CANVAS, room, stretcher, bevel=0.025)
    for z in (-0.52, 0.0, 0.52):
        cube("medical_storage_stretcher_strap", (0.0, -0.008, z), (0.58, 0.018, 0.055), MAT_RUBBER, room, stretcher, bevel=0.008)

    # A low packing table and enamel containers on the north side.
    table = empty("medical_storage_packing_table", (17.55, 5.24, 0.0), room)
    cube("medical_storage_table_top", (0.0, 0.0, 0.86), (1.65, 0.62, 0.10), MAT_WOOD, room, table, bevel=0.028)
    for x in (-0.72, 0.72):
        for y in (-0.23, 0.23):
            cube("medical_storage_table_leg", (x, y, 0.42), (0.075, 0.075, 0.84), MAT_METAL, room, table, bevel=0.010)
    for x in (-0.42, 0.0, 0.42):
        cylinder("medical_storage_enamel_canister", (x, 0.0, 1.12), 0.15, 0.42, MAT_ENAMEL, room, table, vertices=28, bevel=0.012)
        cylinder("medical_storage_canister_lid", (x, 0.0, 1.35), 0.17, 0.05, MAT_METAL, room, table, vertices=28, bevel=0.010)

    # Wall cabinet and reusable canvas restraints, now mounted on the clear east wall.
    cabinet = empty("care_emergency_restraint_cabinet", (20.30, 4.72, 1.48), gameplay, (0.0, 0.0, -math.pi / 2.0))
    cube("care_restraint_cabinet_back", (0.0, 0.10, 0.0), (0.92, 0.12, 0.92), MAT_ENAMEL, gameplay, cabinet, bevel=0.025)
    cube("care_restraint_cabinet_top", (0.0, -0.04, 0.46), (0.98, 0.34, 0.08), MAT_METAL, gameplay, cabinet, bevel=0.018)
    cube("care_restraint_cabinet_bottom", (0.0, -0.04, -0.46), (0.98, 0.34, 0.08), MAT_METAL, gameplay, cabinet, bevel=0.018)
    for x in (-0.46, 0.46):
        cube("care_restraint_cabinet_side", (x, -0.04, 0.0), (0.08, 0.34, 0.92), MAT_METAL, gameplay, cabinet, bevel=0.018)
    cube("care_restraint_cabinet_shelf", (0.0, -0.08, -0.05), (0.88, 0.28, 0.055), MAT_METAL, gameplay, cabinet, bevel=0.010)
    text("care_restraint_cabinet_title", "ВЯЗКИ", (0.0, -0.235, 0.37), 0.075, MAT_CLOCK_INK, gameplay, cabinet)

    restraints = empty("interaction_patient_restraints", (20.00, 4.72, 1.43), gameplay, (0.0, 0.0, -math.pi / 2.0))
    restraints["care_item"] = "patient_restraints"
    for x in (-0.16, 0.16):
        torus("care_restraint_coil", (x, 0.0, 0.0), 0.12, 0.026, MAT_CANVAS, gameplay, restraints, (math.pi / 2.0, 0.0, 0.0))
        cube("care_restraint_buckle", (x, -0.035, 0.0), (0.10, 0.035, 0.075), MAT_METAL, gameplay, restraints, bevel=0.012)
    cube("care_restraint_label", (0.0, -0.045, -0.19), (0.42, 0.025, 0.12), MAT_PAPER, gameplay, restraints, bevel=0.010)
    text("care_restraint_label_text", "ДЛЯ ФИКСАЦИИ", (0.0, -0.064, -0.19), 0.034, MAT_CLOCK_INK, gameplay, restraints)

    # Deep night window opposite the entrance. It is layered geometry, not an image texture.
    window = empty("medical_storage_night_window", (17.50, 5.82, 1.73), room)
    cube("medical_storage_window_night", (0.0, 0.035, 0.0), (2.05, 0.028, 1.20), MAT_NIGHT, room, window, bevel=0.01)
    # Low buildings and a single lit moon are geometry behind the glass.
    for index, (x, width, height) in enumerate(((-0.78, 0.34, 0.42), (-0.42, 0.40, 0.56), (0.00, 0.48, 0.34), (0.48, 0.42, 0.50), (0.83, 0.28, 0.30))):
        cube(f"medical_storage_window_building_{index}", (x, 0.012, -0.60 + height * 0.5), (width, 0.018, height), MAT_CLOCK_INK, room, window, bevel=0.006)
    sphere("medical_storage_window_moon", (0.68, -0.002, 0.31), (0.105, 0.010, 0.105), MAT_MOON, room, window, 32)
    curve("medical_storage_window_tree", [(-0.86, -0.006, -0.58), (-0.82, -0.006, -0.10), (-0.91, -0.006, 0.32), (-0.76, -0.006, 0.54)], 0.018, MAT_CLOCK_INK, room, window)
    curve("medical_storage_window_branch", [(-0.84, -0.008, 0.05), (-0.57, -0.008, 0.21), (-0.42, -0.008, 0.42)], 0.012, MAT_CLOCK_INK, room, window)
    curve("medical_storage_window_branch", [(-0.88, -0.008, 0.28), (-1.00, -0.008, 0.48), (-0.95, -0.008, 0.60)], 0.010, MAT_CLOCK_INK, room, window)
    cube("medical_storage_window_glass", (0.0, -0.025, 0.0), (2.08, 0.018, 1.23), MAT_GLASS, room, window, bevel=0.012)
    for x in (-1.09, 1.09):
        cube("medical_storage_window_frame_vertical", (x, -0.055, 0.0), (0.13, 0.13, 1.43), MAT_WOOD, room, window, bevel=0.022)
    for z in (-0.67, 0.67):
        cube("medical_storage_window_frame_horizontal", (0.0, -0.055, z), (2.31, 0.13, 0.13), MAT_WOOD, room, window, bevel=0.022)
    cube("medical_storage_window_mullion", (0.0, -0.060, 0.0), (0.075, 0.12, 1.31), MAT_WOOD, room, window, bevel=0.014)
    cube("medical_storage_window_transom", (0.0, -0.061, 0.25), (2.18, 0.12, 0.065), MAT_WOOD, room, window, bevel=0.012)
    cube("medical_storage_window_sill", (0.0, -0.25, -0.76), (2.48, 0.52, 0.10), MAT_ENAMEL, room, window, bevel=0.025)

    return len(stair_roots), len(room.all_objects)


clock = rebuild_clock()
removed_stairs, room_object_count = rebuild_storage_room()
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print(
    "CLOCK_STORAGE_WINDOW_REBUILT",
    "clock=", clock.name,
    "stairs_removed=", removed_stairs,
    "storage_objects=", room_object_count,
    "restraints=", tuple(round(value, 3) for value in bpy.data.objects["interaction_patient_restraints"].location),
)
