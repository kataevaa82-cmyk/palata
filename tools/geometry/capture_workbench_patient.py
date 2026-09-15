# -*- coding: utf-8 -*-
"""Workbench stills of the improved ward-4 patient. EEVEE crashes on the 920M."""
import math
import os

import bpy
from mathutils import Vector

PATIENT = "ward_4_bed_1_patient_v3"
OUT_DIR = "C:/palata/build/ward_patient_quality"
os.makedirs(OUT_DIR, exist_ok=True)

scene = bpy.context.scene
root = bpy.data.objects[PATIENT]
head = bpy.data.objects[PATIENT + "_patient_head"]
patient_objects = [root] + list(root.children_recursive)

basis = root.matrix_world.to_3x3()
forward = (basis @ Vector((0.0, 1.0, 0.0))).normalized()
right = (basis @ Vector((1.0, 0.0, 0.0))).normalized()
up = (basis @ Vector((0.0, 0.0, 1.0))).normalized()
face_verts = [v.co for v in head.data.vertices if v.co.y > 0.45 and v.co.z > 1.02]
if not face_verts:
    face_verts = list(v.co for v in head.data.vertices)
nose = head.matrix_world @ max(face_verts, key=lambda co: co.z)
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

for name in ("CAP_cam",):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

cam_data = bpy.data.cameras.new("CAP_cam")
cam_data.lens = 55
cam = bpy.data.objects.new("CAP_cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False


def aim(target, distance, swing_deg, elevation_deg, resolution):
    scene.render.resolution_x, scene.render.resolution_y = resolution
    a, e = math.radians(swing_deg), math.radians(elevation_deg)
    offset = (forward * (math.cos(a) * math.cos(e))
              + right * (math.sin(a) * math.cos(e))
              + up * math.sin(e)) * distance
    cam.location = Vector(target) + offset
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (Vector(target) - cam.location).to_track_quat("-Z", "Y")


shots = (
    ("01_body", body_centre, 1.9, -28, 26, (1000, 800)),
    ("02_face", nose, 0.58, 22, 14, (1000, 900)),
    ("03_face_side", nose, 0.58, -52, 10, (1000, 900)),
)
for name, target, distance, swing, elevation, resolution in shots:
    aim(target, distance, swing, elevation, resolution)
    scene.render.filepath = "%s/%s.png" % (OUT_DIR, name)
    bpy.ops.render.render(write_still=True)

print("CAPTURED", OUT_DIR, "nose=", tuple(round(v, 3) for v in nose))
