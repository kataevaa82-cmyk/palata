import os

import bpy
from mathutils import Vector


OUTPUT_DIR = "C:/palata/build/assignment_board_context"
os.makedirs(OUTPUT_DIR, exist_ok=True)

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = 1000
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.studio_light = "paint.sl"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"
scene.display.shading.background_type = "VIEWPORT"
scene.display.shading.background_color = (0.035, 0.04, 0.035)

saved_collections = {collection.name: (collection.hide_viewport, collection.hide_render) for collection in scene.collection.children}
for collection in scene.collection.children:
    collection.hide_viewport = False
    collection.hide_render = collection.name in {"ASSET_orderly_ghost_v5", "ASSET_violent_patient_v1", "MODULE_LIBRARY", "ANOMALY_VARIANTS"}
saved_render = {obj.name: obj.hide_render for obj in scene.objects}
for obj in scene.objects:
    lower = obj.name.lower()
    if "ceiling" in lower or "fluorescent" in lower or "room_diffuser" in lower:
        obj.hide_render = True

camera_data = bpy.data.cameras.new("assignment_context_camera_data")
camera = bpy.data.objects.new("assignment_context_camera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera


def render(name, position, target, lens):
    camera.data.lens = lens
    camera.location = position
    camera.rotation_euler = (Vector(target) - Vector(position)).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = f"{OUTPUT_DIR}/{name}.png"
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)
    print("ASSIGNMENT_CONTEXT", scene.render.filepath)


render("01_front_wide", (4.50, -0.70, 1.85), (4.50, 1.50, 1.82), 52.0)
render("02_left_angle", (2.65, -0.45, 2.00), (4.50, 1.50, 1.82), 52.0)
render("03_right_angle", (6.35, -0.45, 2.00), (4.50, 1.50, 1.82), 52.0)
render("04_outlet_flush", (8.70, 0.20, 0.70), (9.35, 1.53, 0.42), 62.0)
render("05_switch_flush", (5.20, 0.20, 1.60), (5.85, 1.53, 1.38), 62.0)

bpy.data.objects.remove(camera, do_unlink=True)
if camera_data.users == 0:
    bpy.data.cameras.remove(camera_data)
for obj in scene.objects:
    if obj.name in saved_render:
        obj.hide_render = saved_render[obj.name]
for collection in scene.collection.children:
    collection.hide_viewport, collection.hide_render = saved_collections[collection.name]
