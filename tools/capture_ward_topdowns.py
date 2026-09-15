import bpy
import os


OUTPUT_DIR = "C:/palata/build/ward_topdowns"
os.makedirs(OUTPUT_DIR, exist_ok=True)

for collection in bpy.context.scene.collection.children:
    collection.hide_viewport = collection.name in {"ASSET_orderly_ghost_v5", "MODULE_LIBRARY", "ANOMALY_VARIANTS"}
    collection.hide_render = collection.hide_viewport

for obj in bpy.data.objects:
    lower = obj.name.lower()
    if "ceiling" in lower or "fluorescent" in lower or "room_diffuser" in lower:
        obj.hide_render = True

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = 720
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.studio_light = "paint.sl"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"
scene.display.shading.show_specular_highlight = True
scene.display.shading.background_type = "VIEWPORT"
scene.display.shading.background_color = (0.035, 0.04, 0.035)

camera_data = bpy.data.cameras.get("ward_top_camera_data") or bpy.data.cameras.new("ward_top_camera_data")
camera = bpy.data.objects.get("ward_top_camera") or bpy.data.objects.new("ward_top_camera", camera_data)
if not camera.users_collection:
    bpy.context.scene.collection.objects.link(camera)
camera.data.type = "ORTHO"
camera.data.ortho_scale = 5.8
camera.rotation_euler = (0.0, 0.0, 0.0)
scene.camera = camera

centers = {
    1: (-17.5, 3.82),
    2: (-12.5, 3.82),
    3: (-7.5, 3.82),
    4: (-17.5, -3.82),
    5: (-12.5, -3.82),
    6: (-7.5, -3.82),
}

for ward, (x, y) in centers.items():
    camera.location = (x, y, 9.0)
    bpy.context.view_layer.update()
    scene.render.filepath = f"{OUTPUT_DIR}/ward_{ward}_top.png"
    bpy.ops.render.render(write_still=True)
    print(f"WARD_CAPTURE {ward} {scene.render.filepath}")
