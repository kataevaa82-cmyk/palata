"""Render a review shot of each new level prop, framed on the prop itself.

Cheaper than an exe rebuild: a prop that ended up inside a wall, floating, or
blocking a doorway shows here for the cost of one render each.
"""

import math
import os

import bpy
from mathutils import Vector

OUT_DIR = "C:/palata/build/level_props"
COLLECTION_NAME = "GAMEPLAY_LEVEL_PROPS_V1"

SHOTS = (
    # name, camera distance, swing degrees around +X, elevation degrees
    ("interaction_fuse_box", 1.6, 200, 12),
    ("interaction_oxygen_pillow", 1.4, 200, 22),
    ("interaction_quarantine_curtain", 2.8, 20, 8),
    ("interaction_gurney", 3.4, 200, 26),
    ("interaction_blood_fridge", 2.6, 250, 18),
    ("interaction_radiator_valve", 2.0, 200, 14),
    ("interaction_escaped_patient", 2.6, 40, 16),
    ("interaction_misplaced_chair", 2.4, 120, 26),
    ("interaction_fire_extinguisher", 2.0, 200, 14),
    ("interaction_surgical_lamp", 2.4, 200, -6),
    ("interaction_zero_door", 3.2, 200, 8),
    ("interaction_sterile_bix", 1.8, 220, 26),
)

os.makedirs(OUT_DIR, exist_ok=True)
scene = bpy.context.scene

for name in ("PROPCAP_cam", "PROPCAP_key", "PROPCAP_fill"):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

camera_data = bpy.data.cameras.new("PROPCAP_cam")
camera_data.lens = 40
camera = bpy.data.objects.new("PROPCAP_cam", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera

lights = []
for light_name, energy in (("PROPCAP_key", 260.0), ("PROPCAP_fill", 110.0)):
    data = bpy.data.lights.new(light_name, "POINT")
    data.energy = energy
    data.shadow_soft_size = 0.7
    obj = bpy.data.objects.new(light_name, data)
    scene.collection.objects.link(obj)
    lights.append(obj)

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 760
scene.render.resolution_y = 570
scene.render.resolution_percentage = 100

collection = bpy.data.collections.get(COLLECTION_NAME)


def prop_centre(root):
    parts = [child for child in root.children_recursive if child.type == "MESH"]
    if not parts:
        return root.matrix_world.translation.copy(), 0.5
    lows = Vector((1e9, 1e9, 1e9))
    highs = Vector((-1e9, -1e9, -1e9))
    for part in parts:
        for corner in part.bound_box:
            world = part.matrix_world @ Vector(corner)
            for axis in range(3):
                lows[axis] = min(lows[axis], world[axis])
                highs[axis] = max(highs[axis], world[axis])
    return (lows + highs) * 0.5, (highs - lows).length * 0.5


rendered = []
for name, distance, swing, elevation in SHOTS:
    root = bpy.data.objects.get(name)
    if not root:
        continue
    centre, radius = prop_centre(root)
    reach = max(distance, radius * 2.4)
    a, e = math.radians(swing), math.radians(elevation)
    offset = Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e))) * reach
    camera.location = centre + offset
    camera.rotation_mode = "QUATERNION"
    camera.rotation_quaternion = (centre - camera.location).to_track_quat("-Z", "Y")
    lights[0].location = centre + offset * 0.55 + Vector((0.0, 0.0, 0.9))
    lights[1].location = centre - offset * 0.4 + Vector((0.0, 0.0, 0.6))
    scene.render.filepath = "%s/%s.png" % (OUT_DIR, name.replace("interaction_", ""))
    bpy.ops.render.render(write_still=True)
    rendered.append(name)

bpy.data.objects.remove(camera, do_unlink=True)
for obj in lights:
    bpy.data.objects.remove(obj, do_unlink=True)

print("LEVEL_PROP_SHOTS", len(rendered), OUT_DIR)
