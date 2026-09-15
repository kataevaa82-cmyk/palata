"""Baked image textures for ward windows that survive glTF export."""

import math
import os

import bpy


TEXTURE_DIR = "C:/palata/assets/textures/windows"
TEXTURE_SIZE = 192

MATERIALS = {
    "MAT_offwhite_painted_wood": ("painted_wood", (0.67, 0.65, 0.53)),
    "MAT_night_outside": ("night", (0.025, 0.045, 0.070)),
    "MAT_storage_window_glass": ("glass", (0.12, 0.19, 0.20)),
    "MAT_storage_window_night": ("night", (0.018, 0.035, 0.060)),
    "MAT_storage_old_wood": ("old_wood", (0.19, 0.095, 0.035)),
    "MAT_storage_enamel": ("enamel", (0.60, 0.59, 0.48)),
}


def _clamp(value):
    return max(0.0, min(1.0, value))


def _noise(x, y):
    value = math.sin(x * 12.9898 + y * 78.233) * 43758.5453
    return value - math.floor(value)


def _pixel(pattern, base, x, y):
    u = x / max(1, TEXTURE_SIZE - 1)
    v = y / max(1, TEXTURE_SIZE - 1)
    grain = _noise(x, y) * 2.0 - 1.0
    value = grain * 0.035

    if pattern == "painted_wood":
        value += math.sin(v * 115.0 + math.sin(u * 17.0) * 2.0) * 0.035
        chip = _noise(x // 5, y // 5) > 0.91 and _noise(x, y + 73) > 0.56
        if chip:
            return (0.24 + grain * 0.025, 0.13 + grain * 0.018, 0.055, 1.0)
    elif pattern == "old_wood":
        value += math.sin(v * 92.0 + math.sin(u * 11.0) * 2.5) * 0.055
        if _noise(x // 8, y // 3) > 0.94:
            value -= 0.08
    elif pattern == "enamel":
        value *= 0.55
        if _noise(x // 4, y // 4) > 0.965:
            return (0.18, 0.17, 0.12, 1.0)
    elif pattern == "night":
        value = (v - 0.5) * 0.035 + grain * 0.012
        if _noise(x, y) > 0.9975:
            return (0.45, 0.50, 0.42, 1.0)
        skyline = 0.10 + 0.11 * _noise(x // 18, 5)
        if v < skyline:
            return (0.008, 0.012, 0.018, 1.0)
    elif pattern == "glass":
        edge = min(u, 1.0 - u, v, 1.0 - v)
        grime = max(0.0, 0.14 - edge) * 0.65
        streak = max(0.0, math.sin(u * 53.0 + _noise(x // 9, 2) * 4.0))
        value = grain * 0.025 - grime + streak * 0.016 * (1.0 - v)

    return (
        _clamp(base[0] + value * 1.05),
        _clamp(base[1] + value * 0.95),
        _clamp(base[2] + value * 0.82),
        1.0,
    )


def _image(material_name, pattern, base):
    os.makedirs(TEXTURE_DIR, exist_ok=True)
    key = material_name.removeprefix("MAT_").lower()
    image_name = "TEX_window_" + key
    old = bpy.data.images.get(image_name)
    if old:
        bpy.data.images.remove(old)
    image = bpy.data.images.new(image_name, width=TEXTURE_SIZE, height=TEXTURE_SIZE, alpha=False)
    pixels = []
    for y in range(TEXTURE_SIZE):
        for x in range(TEXTURE_SIZE):
            pixels.extend(_pixel(pattern, base, x, y))
    image.pixels.foreach_set(pixels)
    image.filepath_raw = "%s/%s.png" % (TEXTURE_DIR, key)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image


def _ensure_uv(mesh):
    if mesh.uv_layers:
        return
    uv_layer = mesh.uv_layers.new(name="WindowUV")
    for polygon in mesh.polygons:
        normal = polygon.normal
        axis = max(range(3), key=lambda index: abs(normal[index]))
        uv_axes = [index for index in range(3) if index != axis]
        for loop_index in polygon.loop_indices:
            coordinate = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            uv_layer.data[loop_index].uv = (coordinate[uv_axes[0]] * 0.7, coordinate[uv_axes[1]] * 0.7)


def apply_window_textures():
    images = {}
    for material_name, (pattern, base) in MATERIALS.items():
        material = bpy.data.materials.get(material_name)
        if material is None:
            continue
        material.use_nodes = True
        nodes = material.node_tree.nodes
        shader = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
        if shader is None:
            continue
        texture = nodes.get("Ward Window Texture") or nodes.new("ShaderNodeTexImage")
        texture.name = "Ward Window Texture"
        texture.label = "Exported ward-window texture"
        texture.image = _image(material_name, pattern, base)
        texture.interpolation = "Linear"
        texture.extension = "REPEAT"
        for link in list(shader.inputs["Base Color"].links):
            material.node_tree.links.remove(link)
        material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
        material.diffuse_color = (*base, 1.0)
        images[material_name] = texture.image.name

    textured_materials = set(images)
    textured_objects = 0
    for obj in bpy.data.objects:
        if obj.type != "MESH" or "window" not in obj.name.lower():
            continue
        if any(material and material.name in textured_materials for material in obj.data.materials):
            _ensure_uv(obj.data)
            textured_objects += 1
    print("WINDOW_TEXTURES_APPLIED", textured_objects, images)
    return textured_objects
