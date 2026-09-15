"""Render the downloaded static head from all four horizontal axes."""

import os

import bpy
from mathutils import Vector


SOURCE = "C:/palata/assets/third_party/supine-human-model/human_posed.glb"
OUT = "C:/palata/build/source_head_axes"
os.makedirs(OUT, exist_ok=True)

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
bpy.ops.import_scene.gltf(filepath=SOURCE)
human = bpy.data.objects["Human_Mesh"]

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "BOTH"
scene.display.shading.curvature_ridge_factor = 2.0
scene.display.shading.curvature_valley_factor = 2.0
scene.render.resolution_x = 600
scene.render.resolution_y = 600
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"

camera_data = bpy.data.cameras.new("source_head_axis_camera")
camera_data.type = "ORTHO"
camera_data.ortho_scale = 1.25
camera = bpy.data.objects.new("source_head_axis_camera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
target = Vector((0.0, 0.0, 2.30))

views = {
    "from_pos_x": Vector((4.0, 0.0, 2.30)),
    "from_neg_x": Vector((-4.0, 0.0, 2.30)),
    "from_pos_y": Vector((0.0, 4.0, 2.30)),
    "from_neg_y": Vector((0.0, -4.0, 2.30)),
}
for name, location in views.items():
    camera.location = location
    camera.rotation_mode = "QUATERNION"
    camera.rotation_quaternion = (target - location).to_track_quat("-Z", "Y")
    scene.render.filepath = "%s/%s.png" % (OUT, name)
    bpy.ops.render.render(write_still=True)
    print("SOURCE_HEAD_AXIS", name, scene.render.filepath)
