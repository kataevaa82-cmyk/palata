import os

import bpy
from mathutils import Vector


OUTPUT_PATH = "C:/palata/build/patient_face_after.png"
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = 900
scene.render.resolution_y = 700
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

# Collections must be cleared for *render*, not just viewport: a collection with
# hide_render=True suppresses its objects no matter what their own flags say,
# which silently produced an empty frame while the script still reported success.
# Per-object isolation is handled below, so opening everything here is safe.
collection_state = {
    collection.name: (collection.hide_viewport, collection.hide_render)
    for collection in bpy.context.scene.collection.children
}
for collection in bpy.context.scene.collection.children:
    collection.hide_viewport = False
    collection.hide_render = False
bpy.context.view_layer.update()

root = bpy.data.objects.get("ward_4_bed_1_patient_v3")
head = bpy.data.objects.get("ward_4_bed_1_patient_v3_patient_head")
if root is None or head is None:
    raise RuntimeError("Ward 4 lying patient was not found")


def nose_tip_world(head_obj):
    """The nose is sculpted into the head mesh, so there is no nose_tip object.

    In the head's local space the face always points +Y (see HEAD_PROFILE in
    build_care_gameplay_v2.py), so the frontmost local vertex is the nose tip
    regardless of which way the bed is rotated in the ward.
    """
    tip = max((vertex.co for vertex in head_obj.data.vertices), key=lambda co: co.y)
    return head_obj.matrix_world @ tip

# Isolate the actual patient plus mattress/pillows. Besides giving an honest,
# unobstructed review angle this avoids evaluating the full 2800-object ward.
keep = {root, *root.children_recursive}
for suffix in ("mattress", "pillow_left", "pillow_right"):
    obj = bpy.data.objects.get(f"ward_4_bed_1_{suffix}")
    if obj:
        keep.add(obj)
hidden_scene_objects = []
for obj in scene.objects:
    if obj not in keep:
        hidden_scene_objects.append((obj, obj.hide_render))
        obj.hide_render = True

target = nose_tip_world(head) + Vector((0.0, 0.0, 0.025))
basis = root.matrix_world.to_3x3()
forward = (basis @ Vector((0.0, 1.0, 0.0))).normalized()
right = (basis @ Vector((1.0, 0.0, 0.0))).normalized()
up = (basis @ Vector((0.0, 0.0, 1.0))).normalized()

camera_data = bpy.data.cameras.new("patient_face_review_camera_data")
camera = bpy.data.objects.new("patient_face_review_camera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera.data.lens = 62.0
camera.location = target + forward * 0.78 + right * 0.22 + up * 0.12
camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()

scene.render.filepath = OUTPUT_PATH
bpy.context.view_layer.update()
bpy.ops.render.render(write_still=True)
print("PATIENT_FACE_CAPTURE", OUTPUT_PATH)

bpy.data.objects.remove(camera, do_unlink=True)
if camera_data.users == 0:
    bpy.data.cameras.remove(camera_data)
for collection in bpy.context.scene.collection.children:
    previous = collection_state.get(collection.name)
    if previous:
        collection.hide_viewport, collection.hide_render = previous
for obj, was_hidden in hidden_scene_objects:
    obj.hide_render = was_hidden
