import bpy
from mathutils import Vector


OUTPUT = "C:/palata/build/procedure_blender_preview.png"
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = 1100
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"
scene.display.shading.curvature_ridge_factor = 1.7
scene.display.shading.curvature_valley_factor = 1.4

camera_data = bpy.data.cameras.new("procedure_preview_camera_data")
camera = bpy.data.objects.new("procedure_preview_camera", camera_data)
scene.collection.objects.link(camera)
camera.location = (-2.05, 1.90, 1.55)
target = Vector((-3.05, 4.62, 1.12))
camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.lens = 33.0
camera.data.sensor_width = 36.0
scene.camera = camera
scene.render.filepath = OUTPUT
bpy.ops.render.render(write_still=True)
print("PROCEDURE_CAPTURE", OUTPUT)
