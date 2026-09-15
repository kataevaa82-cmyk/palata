# -*- coding: utf-8 -*-
"""Render the ward's furniture families in isolation, nine to a contact sheet.

Same idea as render_prop_sheet.py, but keyed on a name PREFIX instead of an
`interaction_*` root, because the furniture has no root empties - a bed is 30-odd
sibling meshes sharing the name `ward_1_bed_1_*`.

Usage: blender --background <blend> --python this.py -- <out_dir> <tag>
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT_DIR = argv[0] if argv else "C:/palata/build/family_review"
TAG = argv[1] if len(argv) > 1 else "before"

# label -> the name prefixes that make up one object
FAMILIES = [
    # A doorway is six separate objects and a window is seven; listing only the
    # leaf and the jambs (as this did at first) renders a hole where the glass
    # and the header should be and invites the wrong conclusion.
    ("door", ["hospital_door_N_1", "door_glass_N_1", "doorframe_N_1",
              "doorframe_top_N_1", "opening_header_N_1", "*door_detail_hinge_barrel_N_1",
              "*door_detail_hinge_plate_N_1", "*door_detail_handle_rose_N_1",
              "*door_detail_handle_neck_N_1", "*door_detail_handle_lever_N_1",
              "*door_detail_bead_top_N_1", "*door_detail_bead_bottom_N_1",
              "*door_detail_bead_left_N_1", "*door_detail_bead_right_N_1",
              "*door_detail_panel_N_1", "*door_detail_kickplate_N_1"]),
    ("bed", ["ward_1_bed_1_"]),
    ("sink", ["sink_unit_v2"]),
    ("toilet", ["toilet_v2"]),
    ("shower", ["shower_unit_v2"]),
    ("radiator", ["radiator_combined_0"]),
    ("wheelchair", ["wheelchair_v2"]),
    ("medical_cart", ["medical_cart_v2"]),
    ("window", ["window_frame_0", "window_detail_mesh_0", "window_mullion_0",
                "window_night_0", "window_sill_0", "*window_sash_head_0",
                "*window_sash_cill_0", "*window_sash_stile_l_0", "*window_sash_stile_r_0",
                "*window_bead_top_0", "*window_bead_bottom_0", "*window_bead_left_0",
                "*window_bead_right_0", "*window_latch_plate_0", "*window_latch_pivot_0",
                "*window_latch_lever_0"]),
    ("office_chair", ["office_chair_left_v2"]),
    ("notice_board", ["notice_board_v2"]),
    ("elevator", ["elevator_unit_v2"]),
    ("linen_rack", ["linen_rack_left_v2"]),
    ("nurse_chair", ["nurse_chair_v2"]),
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

world = bpy.data.worlds.new("FAMILYSHEET_world")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.09, 0.10, 0.10, 1.0)
world.node_tree.nodes["Background"].inputs[1].default_value = 1.1
scene.world = world

for name in ("FAMILY_cam", "FAMILY_key", "FAMILY_fill", "FAMILY_rim"):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

cam_data = bpy.data.cameras.new("FAMILY_cam")
cam_data.lens = 50
camera = bpy.data.objects.new("FAMILY_cam", cam_data)
scene.collection.objects.link(camera)
scene.camera = camera

lights = []
for light_name, energy, size in (("FAMILY_key", 900.0, 1.6),
                                 ("FAMILY_fill", 260.0, 2.4),
                                 ("FAMILY_rim", 420.0, 1.0)):
    data = bpy.data.lights.new(light_name, "POINT")
    data.energy = energy
    data.shadow_soft_size = size
    obj = bpy.data.objects.new(light_name, data)
    scene.collection.objects.link(obj)
    lights.append(obj)

HELPERS = {camera.name} | {light.name for light in lights}
for obj in scene.objects:
    if obj.name not in HELPERS:
        obj.hide_render = True


def bounds(objects):
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for obj in objects:
        for corner in obj.bound_box:
            world_co = obj.matrix_world @ Vector(corner)
            lo = Vector(min(lo[i], world_co[i]) for i in range(3))
            hi = Vector(max(hi[i], world_co[i]) for i in range(3))
    return (None, None) if lo.x > hi.x else (lo, hi)


tiles = []
for label, prefixes in FAMILIES:
    # A prefix starting with "*" is a substring test instead: the door details
    # carry their doorway tag in the MIDDLE of the name, so matching by prefix
    # would pull in all fifteen doorways at once.
    def matches(name):
        for spec in prefixes:
            if spec.startswith("*"):
                if spec[1:] in name:
                    return True
            elif name.startswith(spec):
                return True
        return False

    parts = [obj for obj in scene.objects if obj.type == "MESH" and matches(obj.name)]
    if not parts:
        print("FAMILY_MISSING", label)
        continue
    for obj in parts:
        obj.hide_render = False
    lo, hi = bounds(parts)
    centre = (lo + hi) * 0.5
    radius = max((hi - lo).length * 0.5, 0.12)
    distance = radius * 3.0 + 0.3
    azimuth = math.radians(38.0)
    elevation = math.radians(22.0)
    offset = Vector((math.cos(azimuth) * math.cos(elevation),
                     -math.sin(azimuth) * math.cos(elevation),
                     math.sin(elevation))) * distance
    camera.location = centre + offset
    camera.rotation_euler = (centre - camera.location).normalized().to_track_quat("-Z", "Y").to_euler()
    lights[0].location = centre + Vector((radius * 2.2, -radius * 2.6, radius * 3.0 + 0.6))
    lights[1].location = centre + Vector((-radius * 3.0, -radius * 1.4, radius * 1.2))
    lights[2].location = centre + Vector((-radius * 1.0, radius * 3.0, radius * 2.0))
    for index, light in enumerate(lights):
        base = (900.0, 260.0, 420.0)[index]
        light.data.energy = base * max(radius, 0.25) ** 2 * 4.0

    path = os.path.join(OUT_DIR, "%s_%s.png" % (label, TAG))
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    tris = sum(sum(max(len(p.vertices) - 2, 1) for p in obj.data.polygons) for obj in parts)
    print("FAMILY_RENDERED %-14s meshes=%3d tris=%6d" % (label, len(parts), tris))
    tiles.append((label, path))
    for obj in parts:
        obj.hide_render = True


def load(path):
    image = bpy.data.images.load(path)
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(image.size[1], image.size[0], 4)
    bpy.data.images.remove(image)
    return pixels


for sheet_index in range(0, len(tiles), 9):
    chunk = tiles[sheet_index:sheet_index + 9]
    sheet = np.zeros((TILE * 3, TILE * 3, 4), dtype=np.float32)
    sheet[:, :, 3] = 1.0
    for position, (_label, path) in enumerate(chunk):
        row, col = divmod(position, 3)
        sheet[(2 - row) * TILE:(3 - row) * TILE, col * TILE:(col + 1) * TILE] = load(path)
    out = bpy.data.images.new("sheet", TILE * 3, TILE * 3, alpha=True)
    out.pixels = sheet.reshape(-1)
    out.filepath_raw = os.path.join(OUT_DIR, "family_%s_%d.png" % (TAG, sheet_index // 9 + 1))
    out.file_format = "PNG"
    out.save()
    print("FAMILY_SHEET", out.filepath_raw, [name for name, _ in chunk])

print("FAMILY_DONE", len(tiles))
