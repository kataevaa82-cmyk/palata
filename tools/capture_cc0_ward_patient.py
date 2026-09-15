"""Render a close review shot of the downloaded ward patient on its pillow."""

import os

import bpy
from mathutils import Vector


PATIENT = "ward_4_bed_1_patient_v3"
OUTPUT = "C:/palata/build/cc0_ward_patient.png"
BODY_OUTPUT = "C:/palata/build/cc0_ward_patient_body.png"
TOP_OUTPUT = "C:/palata/build/cc0_ward_patient_face_up.png"

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
scene = bpy.context.scene
root = bpy.data.objects[PATIENT]
patient = bpy.data.objects[PATIENT + "_patient_head"]

# Source-space head centre: the prepared static character stands along +Z and
# faces +X. The patient object rotates that source pose face-up on the bed.
face = patient.matrix_world @ Vector((0.34, 0.0, 2.36))
basis = root.matrix_world.to_3x3()
right = (basis @ Vector((1.0, 0.0, 0.0))).normalized()
bed_axis = (basis @ Vector((0.0, 1.0, 0.0))).normalized()
up = Vector((0.0, 0.0, 1.0))

camera_data = bpy.data.cameras.new("CC0_patient_review_camera")
camera_data.lens = 58.0
camera = bpy.data.objects.new("CC0_patient_review_camera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera.location = face + right * 0.48 - bed_axis * 0.50 + up * 0.42
camera.rotation_mode = "QUATERNION"
camera.rotation_quaternion = (face - camera.location).to_track_quat("-Z", "Y")

light_data = bpy.data.lights.new("CC0_patient_review_light", "AREA")
light_data.energy = 850.0
light_data.shape = "DISK"
light_data.size = 1.4
light = bpy.data.objects.new("CC0_patient_review_light", light_data)
light.location = face + right * 0.8 - bed_axis * 0.35 + up * 1.2
scene.collection.objects.link(light)

scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.render.resolution_x = 900
scene.render.resolution_y = 700
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = OUTPUT
scene.world.color = (0.025, 0.025, 0.025)
bpy.ops.render.render(write_still=True)

# Near-vertical proof shot: facial plane must be visible from directly above.
camera.data.lens = 64.0
camera.location = face - bed_axis * 0.02 + up * 0.66
camera.rotation_quaternion = (face - camera.location).to_track_quat("-Z", "Y")
scene.render.resolution_x = 700
scene.render.resolution_y = 700
scene.render.filepath = TOP_OUTPUT
bpy.ops.render.render(write_still=True)

# Full-bed shot verifies both the face-up pose and blanket occlusion.
body_target = root.matrix_world @ Vector((0.0, -0.05, 1.04))
camera.data.lens = 52.0
camera.location = body_target + right * 1.15 - bed_axis * 1.35 + up * 1.75
camera.rotation_quaternion = (body_target - camera.location).to_track_quat("-Z", "Y")
scene.render.resolution_x = 900
scene.render.resolution_y = 760
scene.render.filepath = BODY_OUTPUT
bpy.ops.render.render(write_still=True)

bpy.data.objects.remove(camera, do_unlink=True)
bpy.data.objects.remove(light, do_unlink=True)
print("CC0_WARD_PATIENT_CAPTURED", OUTPUT, TOP_OUTPUT, BODY_OUTPUT, "face=", tuple(round(v, 3) for v in face))
