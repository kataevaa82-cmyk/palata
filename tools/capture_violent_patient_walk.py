import os

import bpy
from mathutils import Vector


OUTPUT_DIR = "C:/palata/build/violent_patient_walk"
COLLECTION_NAME = "ASSET_violent_patient_v1"
os.makedirs(OUTPUT_DIR, exist_ok=True)

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = 680
scene.render.resolution_y = 760
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.studio_light = "paint.sl"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.background_type = "VIEWPORT"
scene.display.shading.background_color = (0.025, 0.028, 0.025)

saved_collections = {collection.name: (collection.hide_viewport, collection.hide_render) for collection in scene.collection.children}
for collection in scene.collection.children:
    enabled = collection.name == COLLECTION_NAME
    collection.hide_viewport = not enabled
    collection.hide_render = not enabled

camera_data = bpy.data.cameras.new("violent_walk_camera_data")
camera = bpy.data.objects.new("violent_walk_camera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera.data.lens = 62.0
camera.location = (0.0, -3.25, 1.05)
camera.rotation_euler = (Vector((0.0, 0.0, 0.98)) - camera.location).to_track_quat("-Z", "Y").to_euler()

for frame in (0, 5, 10, 15):
    scene.frame_set(frame)
    scene.render.filepath = f"{OUTPUT_DIR}/walk_{frame:02d}.png"
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)
    print("VIOLENT_WALK_CAPTURE", frame, scene.render.filepath)

bpy.data.objects.remove(camera, do_unlink=True)
if camera_data.users == 0:
    bpy.data.cameras.remove(camera_data)
for collection in scene.collection.children:
    old = saved_collections.get(collection.name)
    if old:
        collection.hide_viewport, collection.hide_render = old
scene.frame_set(1)
