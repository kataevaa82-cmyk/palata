import bpy
import os
import sys
from mathutils import Vector


OUTPUT_DIR = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "C:/palata/build/procedure_layout"
os.makedirs(OUTPUT_DIR, exist_ok=True)

for collection in bpy.context.scene.collection.children:
    collection.hide_render = collection.name in {"ASSET_orderly_ghost_v5", "MODULE_LIBRARY", "ANOMALY_VARIANTS"}
for obj in bpy.data.objects:
    lower = obj.name.lower()
    if "ceiling" in lower or "fluorescent" in lower or "room_diffuser" in lower:
        obj.hide_render = True

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = 1000
scene.render.resolution_y = 760
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.studio_light = "paint.sl"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"
scene.display.shading.background_type = "VIEWPORT"
scene.display.shading.background_color = (0.035, 0.04, 0.035)

camera_data = bpy.data.cameras.new("procedure_layout_camera_data")
camera = bpy.data.objects.new("procedure_layout_camera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera


def point_camera(position, target, lens=36.0):
    camera.data.type = "PERSP"
    camera.data.lens = lens
    camera.location = position
    camera.rotation_euler = (Vector(target) - Vector(position)).to_track_quat("-Z", "Y").to_euler()


def render(name):
    bpy.context.view_layer.update()
    scene.render.filepath = f"{OUTPUT_DIR}/{name}.png"
    bpy.ops.render.render(write_still=True)
    print("PROCEDURE_LAYOUT_CAPTURE", scene.render.filepath)


camera.data.type = "ORTHO"
camera.data.ortho_scale = 5.7
camera.location = (-2.5, 3.72, 9.0)
camera.rotation_euler = (0.0, 0.0, 0.0)
render("01_procedure_top")

point_camera((-2.55, 1.72, 1.62), (-2.75, 4.65, 1.02), 31.0)
render("02_procedure_entrance")

point_camera((-0.42, 5.48, 1.70), (-2.95, 3.70, 0.95), 32.0)
render("03_procedure_reverse")

point_camera((3.75, -0.25, 1.72), (3.75, 1.405, 1.72), 38.0)
render("04_assignment_board")

# Leave the working scene clean after the diagnostic renders.
bpy.data.objects.remove(camera, do_unlink=True)
if camera_data.users == 0:
    bpy.data.cameras.remove(camera_data)
