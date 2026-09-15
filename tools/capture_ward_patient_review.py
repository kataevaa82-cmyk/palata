"""Render review shots of a bedridden ward patient (body, face, 3/4 face).

Everything is derived from the object itself: the bed roots carry a Z rotation
that differs per ward, and the patient meshes bake their vertices as absolute
coordinates with the object origin left at the root, so neither the world
position nor the facing direction can be hardcoded.
"""

import math
import os

import bpy
from mathutils import Vector

PATIENT = "ward_4_bed_1_patient_v3"
OUT_DIR = "C:/palata/build/ward_patient_check"

os.makedirs(OUT_DIR, exist_ok=True)
scene = bpy.context.scene
root = bpy.data.objects[PATIENT]
head = bpy.data.objects[PATIENT + "_patient_head"]
patient_objects = [root] + list(root.children_recursive)

# Local +Y is the face for every patient (see HEAD_PROFILE in
# build_care_gameplay_v2.py); the root rotation maps it into world space.
basis = root.matrix_world.to_3x3()
forward = (basis @ Vector((0.0, 1.0, 0.0))).normalized()
right = (basis @ Vector((1.0, 0.0, 0.0))).normalized()
up = (basis @ Vector((0.0, 0.0, 1.0))).normalized()
nose = head.matrix_world @ max((v.co for v in head.data.vertices), key=lambda co: co.y)
body_centre = root.matrix_world @ Vector((0.0, 0.1, 1.0))

visibility = {child.name: (child.hide_viewport, child.hide_render)
              for child in scene.collection.children}
patient_collection = root.users_collection[0]
for child in scene.collection.children:
    child.hide_viewport = child != patient_collection
    child.hide_render = child != patient_collection
for obj in patient_objects:
    obj.hide_viewport = False
    obj.hide_render = False
    obj.hide_set(False)

for name in ("CAP_cam", "CAP_key", "CAP_fill"):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

cam_data = bpy.data.cameras.new("CAP_cam")
cam_data.lens = 55
cam = bpy.data.objects.new("CAP_cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

light_objects = []
for name, offset, power in (("CAP_key", forward * 0.6 + right * 0.9 + up * 1.4, 900.0),
                            ("CAP_fill", -forward * 1.4 - right * 0.9 + up * 0.8, 400.0)):
    data = bpy.data.lights.new(name, "POINT")
    data.energy = power
    data.shadow_soft_size = 0.6
    obj = bpy.data.objects.new(name, data)
    obj.location = nose + offset
    scene.collection.objects.link(obj)
    light_objects.append(obj)

world = scene.world or bpy.data.worlds.new("CAP_world")
scene.world = world
world.use_nodes = True
background = world.node_tree.nodes.get("Background")
if background:
    background.inputs[0].default_value = (0.05, 0.055, 0.06, 1.0)
    background.inputs[1].default_value = 0.5

scene.render.engine = "BLENDER_EEVEE"


def aim(target, distance, swing_deg, elevation_deg, resolution):
    """Place the camera `distance` from target, swung around the facing axis."""
    scene.render.resolution_x, scene.render.resolution_y = resolution
    a, e = math.radians(swing_deg), math.radians(elevation_deg)
    offset = (forward * (math.cos(a) * math.cos(e))
              + right * (math.sin(a) * math.cos(e))
              + up * math.sin(e)) * distance
    cam.location = Vector(target) + offset
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (Vector(target) - cam.location).to_track_quat("-Z", "Y")


# Swung off the bed's centre line: a headboard post sits exactly on the
# straight-ahead axis and splits the face in two.
shots = (
    ("01_body", body_centre, 1.9, -28, 26, (1000, 800)),
    ("02_face", nose, 0.58, 22, 14, (1000, 900)),
    ("03_face_side", nose, 0.58, -52, 10, (1000, 900)),
)
try:
    for name, target, distance, swing, elevation, resolution in shots:
        aim(target, distance, swing, elevation, resolution)
        scene.render.filepath = "%s/%s.png" % (OUT_DIR, name)
        bpy.ops.render.render(write_still=True)
finally:
    bpy.data.objects.remove(cam, do_unlink=True)
    for obj in light_objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    for child in scene.collection.children:
        old = visibility.get(child.name)
        if old:
            child.hide_viewport, child.hide_render = old

print("CAPTURED", OUT_DIR, "nose=", tuple(round(v, 3) for v in nose))
