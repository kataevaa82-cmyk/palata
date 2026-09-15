"""Render every bound level prop in isolation and glue the shots into contact
sheets, so the geometry can be judged on its own silhouette instead of through
a corridor wall (which is what the in-scene capture kept producing).

Usage: blender --background <blend> --python this.py -- <out_dir> <tag>
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT_DIR = argv[0] if argv else "C:/palata/build/prop_review"
TAG = argv[1] if len(argv) > 1 else "before"

LEVEL_PROPS = [
    "fuse_box", "spare_fuses", "emergency_lamp", "oxygen_pillow", "quarantine_curtain",
    "mask_box", "hand_sanitizer", "sample_tube", "gurney", "body_bag", "death_certificate",
    "blood_fridge", "blood_bag_first", "blood_bag_second", "blood_bag_third", "blood_chart",
    "radiator_key", "blanket_stack", "radiator_valve", "window_latch", "tea_kettle",
    "hospital_slippers", "muddy_trail", "bed_note", "escaped_patient", "duty_journal_form",
    "misplaced_chair", "floor_dirt", "fire_extinguisher", "smoke_source", "fire_alarm_panel",
    "sterile_bix", "surgical_lamp", "surgical_gown", "zero_door", "zero_key", "zero_card",
]
TILE = 420
os.makedirs(OUT_DIR, exist_ok=True)
scene = bpy.context.scene

for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
scene.render.resolution_x = TILE
scene.render.resolution_y = TILE
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.image_settings.file_format = "PNG"

world = bpy.data.worlds.new("PROPSHEET_world")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.09, 0.10, 0.10, 1.0)
world.node_tree.nodes["Background"].inputs[1].default_value = 1.1
scene.world = world

for name in ("PROPSHEET_cam", "PROPSHEET_key", "PROPSHEET_fill", "PROPSHEET_rim"):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

cam_data = bpy.data.cameras.new("PROPSHEET_cam")
cam_data.lens = 50
camera = bpy.data.objects.new("PROPSHEET_cam", cam_data)
scene.collection.objects.link(camera)
scene.camera = camera

lights = []
for light_name, energy, size in (("PROPSHEET_key", 900.0, 1.6),
                                 ("PROPSHEET_fill", 260.0, 2.4),
                                 ("PROPSHEET_rim", 420.0, 1.0)):
    data = bpy.data.lights.new(light_name, "POINT")
    data.energy = energy
    data.shadow_soft_size = size
    obj = bpy.data.objects.new(light_name, data)
    scene.collection.objects.link(obj)
    lights.append(obj)

HELPERS = {camera.name} | {light.name for light in lights}
ALL = [o for o in scene.objects if o.name not in HELPERS]
for obj in ALL:
    obj.hide_render = True


def subtree(root):
    return [root] + list(root.children_recursive)


def bounds(objects):
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for obj in objects:
        if obj.type not in {"MESH", "CURVE", "FONT"}:
            continue
        for corner in obj.bound_box:
            world_co = obj.matrix_world @ Vector(corner)
            lo = Vector((min(lo[i], world_co[i]) for i in range(3)))
            hi = Vector((max(hi[i], world_co[i]) for i in range(3)))
    if lo.x > hi.x:
        return None, None
    return lo, hi


tiles = []
for prop in LEVEL_PROPS:
    root = bpy.data.objects.get("interaction_" + prop)
    if root is None:
        print("PROPSHEET_MISSING", prop)
        continue
    parts = subtree(root)
    for obj in parts:
        obj.hide_render = False
    lo, hi = bounds(parts)
    if lo is None:
        for obj in parts:
            obj.hide_render = True
        continue
    centre = (lo + hi) * 0.5
    radius = max((hi - lo).length * 0.5, 0.12)
    distance = radius * 3.1 + 0.35
    azimuth = math.radians(38.0)
    elevation = math.radians(24.0)
    offset = Vector((math.cos(azimuth) * math.cos(elevation),
                     -math.sin(azimuth) * math.cos(elevation),
                     math.sin(elevation))) * distance
    camera.location = centre + offset
    direction = (centre - camera.location).normalized()
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    lights[0].location = centre + Vector((radius * 2.2, -radius * 2.6, radius * 3.0 + 0.6))
    lights[1].location = centre + Vector((-radius * 3.0, -radius * 1.4, radius * 1.2))
    lights[2].location = centre + Vector((-radius * 1.0, radius * 3.0, radius * 2.0))
    for light in lights:
        light.data.energy = (900.0 if light is lights[0] else 260.0 if light is lights[1] else 420.0) * max(radius, 0.25) ** 2 * 4.0

    path = os.path.join(OUT_DIR, "%s_%s.png" % (prop, TAG))
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    tiles.append((prop, path))
    for obj in parts:
        obj.hide_render = True

# --- contact sheets, 3x3 ------------------------------------------------------
def load(path):
    image = bpy.data.images.load(path)
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(image.size[1], image.size[0], 4)
    bpy.data.images.remove(image)
    return pixels


for sheet_index in range(0, len(tiles), 9):
    chunk = tiles[sheet_index:sheet_index + 9]
    sheet = np.zeros((TILE * 3, TILE * 3, 4), dtype=np.float32)
    sheet[:, :, 3] = 1.0
    for position, (_prop, path) in enumerate(chunk):
        row, col = divmod(position, 3)
        # Blender images are bottom-up; place row 0 at the top of the sheet.
        top = (2 - row) * TILE
        sheet[top:top + TILE, col * TILE:(col + 1) * TILE] = load(path)
    out = bpy.data.images.new("sheet", TILE * 3, TILE * 3, alpha=True)
    out.pixels = sheet.reshape(-1)
    out.filepath_raw = os.path.join(OUT_DIR, "sheet_%s_%d.png" % (TAG, sheet_index // 9 + 1))
    out.file_format = "PNG"
    out.save()
    print("PROPSHEET_SAVED", out.filepath_raw, [name for name, _ in chunk])

print("PROPSHEET_DONE", len(tiles))
