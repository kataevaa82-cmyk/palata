"""Shared image textures and material assignment for downloaded patients."""

import math
import os

import bpy


TEXTURE_DIR = "C:/palata/assets/textures/patients"
TEXTURE_SIZE = 128


PALETTES = {
    "skin": ((0.47, 0.30, 0.21), 0.035, "skin", 0.78),
    "gown": ((0.075, 0.23, 0.205), 0.055, "cloth", 0.92),
    "trousers": ((0.095, 0.13, 0.15), 0.040, "cloth", 0.94),
    "shoes": ((0.018, 0.022, 0.021), 0.018, "leather", 0.88),
    "hair": ((0.035, 0.020, 0.012), 0.030, "hair", 0.84),
    "eye_white": ((0.76, 0.78, 0.72), 0.012, "leather", 0.34),
    "eye_pupil": ((0.018, 0.012, 0.008), 0.006, "leather", 0.28),
}


def _clamp(value):
    return max(0.0, min(1.0, value))


def _pixel_variation(x, y, pattern):
    grain = math.sin(x * 12.9898 + y * 78.233) * 43758.5453
    grain = (grain - math.floor(grain)) * 2.0 - 1.0
    if pattern == "cloth":
        weave = (0.55 if x % 5 == 0 else 0.0) + (0.35 if y % 7 == 0 else 0.0)
        return grain * 0.35 + weave
    if pattern == "skin":
        pore = 0.8 if (x * 17 + y * 29) % 113 == 0 else 0.0
        return grain * 0.45 + pore
    if pattern == "hair":
        strand = math.sin((x + y * 0.35) * 0.75)
        return grain * 0.25 + strand * 0.55
    if pattern == "leather":
        return grain * 0.30 + math.sin(x * 0.18) * 0.12
    return grain


def _load_or_create_image(key, base, amount, pattern):
    os.makedirs(TEXTURE_DIR, exist_ok=True)
    path = "%s/patient_%s.png" % (TEXTURE_DIR, key)
    image_name = "TEX_patient_%s" % key
    old = bpy.data.images.get(image_name)
    if old:
        return old

    image = bpy.data.images.new(image_name, width=TEXTURE_SIZE, height=TEXTURE_SIZE, alpha=False)
    pixels = []
    for y in range(TEXTURE_SIZE):
        for x in range(TEXTURE_SIZE):
            variation = _pixel_variation(x, y, pattern) * amount
            # Slightly warmer highlights and cooler shadows keep skin and cloth
            # from reading as a single flat game-engine colour.
            pixels.extend((
                _clamp(base[0] + variation * 1.05),
                _clamp(base[1] + variation * 0.92),
                _clamp(base[2] + variation * 0.80),
                1.0,
            ))
    image.pixels.foreach_set(pixels)
    image.filepath_raw = path
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image


def build_patient_materials():
    materials = {}
    for key, (base, amount, pattern, roughness) in PALETTES.items():
        name = "MAT_patient_%s_textured" % key
        material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        material.diffuse_color = (*base, 1.0)
        material.use_nodes = True
        nodes = material.node_tree.nodes
        nodes.clear()
        output = nodes.new("ShaderNodeOutputMaterial")
        shader = nodes.new("ShaderNodeBsdfPrincipled")
        texture = nodes.new("ShaderNodeTexImage")
        texture.image = _load_or_create_image(key, base, amount, pattern)
        texture.interpolation = "Linear"
        shader.inputs["Roughness"].default_value = roughness
        shader.inputs["Specular IOR Level"].default_value = 0.28 if key == "skin" else 0.18
        shader.inputs["Alpha"].default_value = 1.0
        material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
        material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
        materials[key] = material
    return materials


def _install_materials(mesh, materials):
    mesh.materials.clear()
    order = ("skin", "gown", "trousers", "shoes", "hair", "eye_white", "eye_pupil")
    for key in order:
        mesh.materials.append(materials[key])
    return {key: index for index, key in enumerate(order)}


def apply_static_patient_materials(mesh):
    """Assign textured regions on the centred, standing static source mesh."""
    indices = _install_materials(mesh, build_patient_materials())
    for polygon in mesh.polygons:
        centre = polygon.center
        x, y, z = centre.x, centre.y, centre.z
        width = abs(y)
        # Explicit opaque eye surfaces. The foremost cap becomes a dark pupil;
        # the rest of each small sphere is an off-white sclera.
        if x > 0.22 and 2.58 < z < 2.71 and 0.08 < width < 0.22:
            key = "eye_pupil" if x > 0.255 else "eye_white"
        elif z > 1.82:
            # Orthogonal source renders show that the face points +X; -X is
            # the back of the head.
            key = "hair" if z > 2.42 or (z > 2.13 and x < -0.08) else "skin"
        elif z > 1.48 and width < 0.20:
            key = "skin"
        elif z < -2.28:
            key = "shoes"
        # Only the upper arms remain exposed. Lower wide components overlap the
        # thighs in this triangulated source and used to produce red leg-like
        # patches beside the blanket.
        elif width > 0.52 and 0.0 < z < 1.18:
            key = "skin"
        elif z < -0.16:
            key = "trousers"
        else:
            key = "gown"
        polygon.material_index = indices[key]

    # The downloaded low-poly head has a wedge-shaped forelock that projects
    # from the brow and reads as a pair of horns when the patient lies supine.
    # Pull only the high, front hair vertices back to a smooth skull profile.
    hair_index = indices["hair"]
    adjusted_vertices = set()
    for polygon in mesh.polygons:
        if polygon.material_index != hair_index or polygon.center.z < 2.60 or polygon.center.x < 0.08:
            continue
        for vertex_index in polygon.vertices:
            if vertex_index in adjusted_vertices:
                continue
            vertex = mesh.vertices[vertex_index]
            if vertex.co.z < 2.60:
                continue
            front_limit = 0.10 + max(0.0, 2.77 - vertex.co.z) * 0.82
            if vertex.co.x > front_limit:
                vertex.co.x = front_limit
            adjusted_vertices.add(vertex_index)
    mesh.update()


def _dominant_group_name(obj, polygon):
    totals = {}
    for vertex_index in polygon.vertices:
        for membership in obj.data.vertices[vertex_index].groups:
            totals[membership.group] = totals.get(membership.group, 0.0) + membership.weight
    if not totals:
        return ""
    group_index = max(totals, key=totals.get)
    return obj.vertex_groups[group_index].name.lower()


def apply_rigged_patient_materials(obj):
    """Assign equivalent textured regions without disturbing skin weights."""
    indices = _install_materials(obj.data, build_patient_materials())
    for polygon in obj.data.polygons:
        group = _dominant_group_name(obj, polygon)
        rest_centre = obj.matrix_world @ polygon.center
        if "head" in group:
            key = "hair" if rest_centre.z > 4.93 or (rest_centre.z > 4.62 and rest_centre.y > 0.16) else "skin"
        elif "neck" in group or "hand" in group or "forearm" in group:
            key = "skin"
        elif "foot" in group or "toe" in group:
            key = "shoes"
        elif "leg" in group:
            key = "trousers"
        else:
            key = "gown"
        polygon.material_index = indices[key]
    obj.data.update()
