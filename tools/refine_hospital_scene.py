import math

import bpy


BLEND_PATH = "C:/palata/palata_zero.blend"


def assign(obj, material):
    if obj and obj.type == "MESH":
        obj.data.materials.clear()
        obj.data.materials.append(material)


def make_stone_material():
    mat = bpy.data.materials.get("MAT_old_stone_floor") or bpy.data.materials.new("MAT_old_stone_floor")
    mat.diffuse_color = (0.34, 0.33, 0.28, 1.0)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texcoord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    ramp = nodes.new("ShaderNodeValToRGB")
    bump = nodes.new("ShaderNodeBump")
    noise.inputs["Scale"].default_value = 4.0
    noise.inputs["Detail"].default_value = 5.0
    noise.inputs["Roughness"].default_value = 0.76
    color_ramp = ramp.color_ramp
    color_ramp.elements[0].position = 0.23
    color_ramp.elements[0].color = (0.085, 0.085, 0.067, 1.0)
    color_ramp.elements[1].position = 0.77
    color_ramp.elements[1].color = (0.46, 0.44, 0.36, 1.0)
    shader.inputs["Roughness"].default_value = 0.94
    bump.inputs["Strength"].default_value = 0.24
    bump.inputs["Distance"].default_value = 0.035
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return mat


def make_cloudy_glass():
    mat = bpy.data.materials.get("MAT_cloudy_glass") or bpy.data.materials.new("MAT_cloudy_glass")
    mat.diffuse_color = (0.19, 0.27, 0.23, 0.42)
    mat.use_nodes = True
    mat.surface_render_method = "DITHERED"
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    noise = nodes.new("ShaderNodeTexNoise")
    bump = nodes.new("ShaderNodeBump")
    shader.inputs["Base Color"].default_value = (0.18, 0.28, 0.24, 1.0)
    shader.inputs["Roughness"].default_value = 0.48
    shader.inputs["Alpha"].default_value = 0.42
    if "Transmission Weight" in shader.inputs:
        shader.inputs["Transmission Weight"].default_value = 0.28
    noise.inputs["Scale"].default_value = 18.0
    noise.inputs["Detail"].default_value = 3.0
    bump.inputs["Strength"].default_value = 0.09
    bump.inputs["Distance"].default_value = 0.01
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return mat


def box_geometry(boxes):
    vertices = []
    faces = []
    for center, size in boxes:
        offset = len(vertices)
        cx, cy, cz = center
        sx, sy, sz = (value * 0.5 for value in size)
        vertices.extend([
            (cx - sx, cy - sy, cz - sz), (cx + sx, cy - sy, cz - sz),
            (cx + sx, cy + sy, cz - sz), (cx - sx, cy + sy, cz - sz),
            (cx - sx, cy - sy, cz + sz), (cx + sx, cy - sy, cz + sz),
            (cx + sx, cy + sy, cz + sz), (cx - sx, cy + sy, cz + sz),
        ])
        faces.extend([
            (offset + 0, offset + 1, offset + 2, offset + 3),
            (offset + 4, offset + 7, offset + 6, offset + 5),
            (offset + 0, offset + 4, offset + 5, offset + 1),
            (offset + 1, offset + 5, offset + 6, offset + 2),
            (offset + 2, offset + 6, offset + 7, offset + 3),
            (offset + 4, offset + 0, offset + 3, offset + 7),
        ])
    return vertices, faces


def rebuild_glazed_door(slab):
    boxes = [
        ((0.0, 0.0, -0.47), (1.09, 0.10, 1.48)),
        ((-0.46, 0.0, 0.59), (0.17, 0.10, 0.64)),
        ((0.46, 0.0, 0.59), (0.17, 0.10, 0.64)),
        ((0.0, 0.0, 1.06), (1.09, 0.10, 0.30)),
    ]
    vertices, faces = box_geometry(boxes)
    mesh = bpy.data.meshes.new(slab.name + "_glazed_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    old_mesh = slab.data
    slab.data = mesh
    if old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)


def refine():
    stone = make_stone_material()
    glass = make_cloudy_glass()

    floor_count = 0
    for obj in bpy.data.objects:
        lower = obj.name.lower()
        if obj.type == "MESH" and any(token in lower for token in ("floor", "linoleum", "floor_track")):
            assign(obj, stone)
            floor_count += 1

    glass_count = 0
    for glass_obj in [obj for obj in bpy.data.objects if obj.type == "MESH" and obj.name.lower().startswith("door_glass_")]:
        assign(glass_obj, glass)
        glass_obj.location.y = 0.0
        suffix = glass_obj.name[len("door_glass_"):]
        slab = bpy.data.objects.get("hospital_door_" + suffix)
        if slab:
            rebuild_glazed_door(slab)
        glass_count += 1

    removed_sticks = 0
    for obj in list(bpy.data.objects):
        if obj.name.lower().startswith("door_detail_mesh"):
            bpy.data.objects.remove(obj, do_unlink=True)
            removed_sticks += 1

    # Move wall outlets clear of every door swing and player path.
    outlet_count = 0
    for obj in bpy.data.objects:
        if obj.name.lower().startswith("soviet_outlet"):
            obj.location.x += 1.35
            obj.location.y = math.copysign(1.5325, obj.location.y)
            outlet_count += 1

    # Put each bedside cabinet behind its own bed, beside the window.
    room_centers = {
        1: (-17.5, 1.0), 2: (-12.5, 1.0), 3: (-7.5, 1.0),
        4: (-17.5, -1.0), 5: (-12.5, -1.0), 6: (-7.5, -1.0),
    }
    for ward, (center_x, side) in room_centers.items():
        outer_y = 5.18 * side
        for index, offset_x in ((1, -1.25), (2, 1.25)):
            bed = bpy.data.objects.get(f"ward_{ward}_bed_{index}")
            cabinet = bpy.data.objects.get(f"ward_{ward}_bedside_cabinet_{index}")
            if bed:
                bed.location.x = center_x + offset_x
                bed.location.y = 3.72 * side
                bed.rotation_euler.z = 0.0 if side > 0 else 3.141592653589793
            if cabinet:
                cabinet.location.x = center_x + offset_x
                cabinet.location.y = outer_y
                cabinet.rotation_euler.z = 0.0

        iv = bpy.data.objects.get(f"iv_stand_{ward}_v2")
        if iv:
            iv.location = (center_x, 4.78 * side, 0.0)

        first_glass = (ward - 1) * 2 + 1
        for index, offset_x in ((first_glass, -1.25), (first_glass + 1, 1.25)):
            water = bpy.data.objects.get(f"water_glass_{index}_v2")
            if water:
                water.location = (center_x + offset_x, outer_y, 0.80)

        first_slipper = (ward - 1) * 4 + 1
        for local_index in range(4):
            slipper = bpy.data.objects.get(f"patient_slipper_{first_slipper + local_index}_v2")
            if slipper:
                bed_offset = -1.25 if local_index < 2 else 1.25
                foot_offset = -0.18 if local_index % 2 == 0 else 0.18
                slipper.location.x = center_x + bed_offset + foot_offset
                slipper.location.y = 2.52 * side

    # The service room is the south-east room marked "СЛУЖЕБНАЯ".
    mop_bucket = bpy.data.objects.get("interaction_mop_bucket")
    if mop_bucket:
        mop_bucket.location = (18.15, -4.85, 0.0)
        mop_bucket.rotation_euler.z = -0.22

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(
        f"HOSPITAL_REFINED floors={floor_count} glass={glass_count} "
        f"sticks_removed={removed_sticks} outlets_moved={outlet_count}"
    )


refine()
