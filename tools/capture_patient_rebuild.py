import math
import os

import bpy
from mathutils import Vector

COLLECTION_NAME = "ASSET_violent_patient_v1"
OUT_DIR = "C:/palata/build/patient_rebuild"
RIG_NAME = "violent_patient_rig"

os.makedirs(OUT_DIR, exist_ok=True)
collection = bpy.data.collections[COLLECTION_NAME]
scene = bpy.context.scene

# Materialised before the visibility edits below: toggling a collection's
# visibility invalidates the lazy all_objects view mid-iteration.
patient_objects = list(collection.all_objects)
visibility = {child.name: (child.hide_viewport, child.hide_render)
              for child in scene.collection.children}
for child in scene.collection.children:
    child.hide_viewport = child != collection
    child.hide_render = child != collection
for obj in patient_objects:
    obj.hide_viewport = False
    obj.hide_render = False
    obj.hide_set(False)

rig = bpy.data.objects[RIG_NAME]

for name in ("CAP_cam", "CAP_key", "CAP_fill", "CAP_rim"):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

cam_data = bpy.data.cameras.new("CAP_cam")
cam_data.lens = 60
cam = bpy.data.objects.new("CAP_cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

lights = (
    ("CAP_key", (2.4, -3.2, 3.0), 900.0),
    ("CAP_fill", (-3.0, -2.2, 1.6), 320.0),
    ("CAP_rim", (0.4, 3.4, 2.6), 500.0),
)
light_objects = []
for name, position, power in lights:
    data = bpy.data.lights.new(name, "POINT")
    data.energy = power
    data.shadow_soft_size = 1.2
    obj = bpy.data.objects.new(name, data)
    obj.location = position
    scene.collection.objects.link(obj)
    light_objects.append(obj)

world = scene.world or bpy.data.worlds.new("CAP_world")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.05, 0.055, 0.06, 1.0)
    bg.inputs[1].default_value = 0.55

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.render.film_transparent = False


def aim(target, distance, azimuth_deg, elevation_deg, resolution=(900, 1200)):
    scene.render.resolution_x, scene.render.resolution_y = resolution
    a = math.radians(azimuth_deg)
    e = math.radians(elevation_deg)
    offset = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * distance
    cam.location = Vector(target) + offset
    direction = Vector(target) - cam.location
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = direction.to_track_quat("-Z", "Y")


shots = (
    ("01_front_full", (0, 0, 0.95), 3.4, 0, 4, (900, 1300)),
    ("02_threequarter_full", (0, 0, 0.95), 3.4, 38, 8, (900, 1300)),
    ("03_side_full", (0, 0, 0.95), 3.4, 88, 5, (900, 1300)),
    ("04_face_close", (0, -0.06, 1.70), 0.62, 14, 6, (1000, 1100)),
    ("05_face_threequarter", (0, -0.06, 1.70), 0.62, 44, 10, (1000, 1100)),
    ("06_torso", (0, -0.05, 1.20), 1.5, 26, 6, (900, 1100)),
)

try:
    for frame in (1, 7, 16):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for name, target, distance, azimuth, elevation, resolution in shots:
            if frame != 1 and name not in ("01_front_full", "02_threequarter_full"):
                continue
            aim(target, distance, azimuth, elevation, resolution)
            scene.render.filepath = "%s/f%02d_%s.png" % (OUT_DIR, frame, name)
            bpy.ops.render.render(write_still=True)
finally:
    scene.frame_set(1)
    bpy.data.objects.remove(cam, do_unlink=True)
    for obj in light_objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    for child in scene.collection.children:
        old = visibility.get(child.name)
        if old:
            child.hide_viewport, child.hide_render = old

print("CAPTURED " + OUT_DIR)
