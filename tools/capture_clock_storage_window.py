import os

import bpy
from mathutils import Vector


OUTPUT_DIR = "C:/palata/build/clock_storage_window"
os.makedirs(OUTPUT_DIR, exist_ok=True)

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = 1100
scene.render.resolution_y = 760
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.studio_light = "paint.sl"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"
scene.display.shading.background_type = "VIEWPORT"
scene.display.shading.background_color = (0.025, 0.030, 0.028)

saved_collections = {collection.name: (collection.hide_viewport, collection.hide_render) for collection in scene.collection.children}
for collection in scene.collection.children:
    collection.hide_viewport = False
    collection.hide_render = collection.name in {"ASSET_orderly_ghost_v5", "ASSET_violent_patient_v1", "MODULE_LIBRARY", "ANOMALY_VARIANTS"}
saved_render = {obj.name: obj.hide_render for obj in scene.objects}
for obj in scene.objects:
    lower = obj.name.lower()
    if "ceiling" in lower or "fluorescent" in lower or "room_diffuser" in lower:
        obj.hide_render = True

camera_data = bpy.data.cameras.new("clock_storage_capture_camera_data")
camera = bpy.data.objects.new("clock_storage_capture_camera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera


def render(name, position, target, lens, hide_glass=False):
    glass = bpy.data.objects.get("medical_storage_window_glass")
    old_glass = glass.hide_render if glass else False
    if glass and hide_glass:
        glass.hide_render = True
    camera.data.lens = lens
    camera.location = position
    camera.rotation_euler = (Vector(target) - Vector(position)).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = f"{OUTPUT_DIR}/{name}.png"
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)
    if glass:
        glass.hide_render = old_glass
    print("CLOCK_STORAGE_CAPTURE", scene.render.filepath)


render("01_clock_close", (0.0, -0.05, 2.36), (0.0, 1.40, 2.40), 66.0)
render("02_storage_from_door", (17.50, 1.95, 1.58), (17.50, 4.20, 1.26), 30.0, True)
render("03_storage_inside", (19.45, 5.30, 1.66), (16.25, 3.85, 1.18), 42.0, True)
render("04_restraints_clear", (18.34, 4.72, 1.55), (20.06, 4.72, 1.43), 62.0)
render("05_night_window", (17.50, 2.75, 1.58), (17.50, 5.76, 1.73), 58.0, True)
render("06_storage_topdown", (17.75, 3.85, 7.20), (17.75, 3.85, 0.15), 52.0, True)

bpy.data.objects.remove(camera, do_unlink=True)
if camera_data.users == 0:
    bpy.data.cameras.remove(camera_data)
for obj in scene.objects:
    if obj.name in saved_render:
        obj.hide_render = saved_render[obj.name]
for collection in scene.collection.children:
    old = saved_collections.get(collection.name)
    if old:
        collection.hide_viewport, collection.hide_render = old
