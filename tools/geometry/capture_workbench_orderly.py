# -*- coding: utf-8 -*-
"""Workbench turnaround of the improved orderly. EEVEE is unavailable here."""
import math
import os

import bpy
from mathutils import Vector

OUT_DIR = "C:/palata/build/orderly_quality"
ROOT_NAME = "orderly_anomaly_v5"
os.makedirs(OUT_DIR, exist_ok=True)

scene = bpy.context.scene
root = bpy.data.objects[ROOT_NAME]
objects = [root] + list(root.children_recursive)

visibility = {child.name: (child.hide_viewport, child.hide_render)
              for child in scene.collection.children}
for child in scene.collection.children:
    child.hide_viewport = True
    child.hide_render = True
for obj in objects:
    obj.hide_viewport = False
    obj.hide_render = False
    obj.hide_set(False)
    if obj.users_collection:
        for col in obj.users_collection:
            col.hide_viewport = False
            col.hide_render = False

scene.frame_set(8)
bpy.context.view_layer.update()

# Bounds in world space.
lo = Vector((1e9, 1e9, 1e9))
hi = Vector((-1e9, -1e9, -1e9))
for obj in objects:
    if obj.type != "MESH":
        continue
    for corner in obj.bound_box:
        p = obj.matrix_world @ Vector(corner)
        lo = Vector(min(lo[i], p[i]) for i in range(3))
        hi = Vector(max(hi[i], p[i]) for i in range(3))
centre = (lo + hi) * 0.5
height = hi.z - lo.z

for name in ("CAP_ord_cam",):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

cam_data = bpy.data.cameras.new("CAP_ord_cam")
cam_data.lens = 50
cam = bpy.data.objects.new("CAP_ord_cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_x = 720
scene.render.resolution_y = 900

target = Vector((centre.x, centre.y, lo.z + height * 0.55))
distance = max(height * 1.7, 2.4)

shots = (("front", 0.0), ("three_quarter", 40.0), ("left", 90.0), ("back", 180.0))
for name, yaw in shots:
    a = math.radians(yaw)
    cam.location = target + Vector((math.sin(a) * distance, -math.cos(a) * distance, height * 0.15))
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (target - cam.location).to_track_quat("-Z", "Y")
    scene.render.filepath = "%s/%s.png" % (OUT_DIR, name)
    bpy.ops.render.render(write_still=True)

print("ORDERLY_CAPTURED", OUT_DIR, "height", round(height, 3), "z", round(lo.z, 3), round(hi.z, 3))
