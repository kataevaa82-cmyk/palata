# -*- coding: utf-8 -*-
"""Build the running patient from the rigged version of the CC0 ward human."""

import sys

import bpy

sys.path.insert(0, "C:/palata/tools")
from patient_textures import apply_rigged_patient_materials


SOURCE_GLB = "C:/palata/assets/third_party/supine-human-model/human_rigged.glb"
BLEND_PATH = "C:/palata/violent_patient_work.blend"
GLB_PATH = "C:/palata/violent_patient_v1.glb"
COLLECTION_NAME = "ASSET_violent_patient_v1"
TARGET_HEIGHT = 1.75
SOURCE_HEIGHT = 5.299046


# The script is intended to run with --factory-startup, but clearing explicitly
# also makes reruns deterministic.
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

bpy.ops.import_scene.gltf(filepath=SOURCE_GLB)

root = bpy.data.objects.get("RootNode")
rig = bpy.data.objects.get("Human Armature")
mesh = bpy.data.objects.get("Human_Mesh")
if root is None or rig is None or mesh is None or rig.type != "ARMATURE":
    raise RuntimeError("The downloaded rigged human did not contain the expected hierarchy")

# Remove the source preview sphere and bone-tip helper empties.  They are not
# part of the character and should not be exported into Godot.
for obj in list(bpy.data.objects):
    if obj == root or obj == rig or obj == mesh:
        continue
    if obj.name == "Icosphere" or (obj.type == "EMPTY" and obj.parent == rig):
        bpy.data.objects.remove(obj, do_unlink=True)

root.name = "violent_patient_v1"
rig.name = "violent_patient_rig"
mesh.name = "violent_patient_human_mesh"
apply_rigged_patient_materials(mesh)
root.scale = (TARGET_HEIGHT / SOURCE_HEIGHT,) * 3
root["asset_type"] = "rigged_violent_patient"
root["asset_source"] = "UMRAM-Bilkent/supine-human-model"
root["license"] = "CC0-1.0"

run_action = next((action for action in bpy.data.actions if action.name.lower().endswith("|run")), None)
if run_action is None:
    raise RuntimeError("The downloaded rig has no Run animation")
run_action.name = "Violent_Run"
run_action.use_fake_user = True
rig.animation_data_create()
rig.animation_data.action = run_action
root["run_action"] = run_action.name

collection = bpy.data.collections.get(COLLECTION_NAME)
if collection is None:
    collection = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(collection)
for obj in (root, rig, mesh):
    for old_collection in list(obj.users_collection):
        old_collection.objects.unlink(obj)
    collection.objects.link(obj)

scene = bpy.context.scene
scene.render.fps = 24
scene.frame_start = int(run_action.frame_range[0])
scene.frame_end = int(run_action.frame_range[1])
scene.frame_set(scene.frame_start)
bpy.context.view_layer.update()

for obj in bpy.context.view_layer.objects:
    obj.select_set(False)
for obj in (root, rig, mesh):
    obj.hide_viewport = False
    obj.hide_render = False
    obj.hide_set(False)
    obj.select_set(True)
bpy.context.view_layer.objects.active = rig

bpy.ops.export_scene.gltf(
    filepath=GLB_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_cameras=False,
    export_lights=False,
    export_animations=True,
    export_animation_mode="ACTIVE_ACTIONS",
    export_nla_strips_merged_animation_name=run_action.name,
)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

print(
    "CC0_VIOLENT_PATIENT_BUILT",
    "height=", round(TARGET_HEIGHT, 3),
    "bones=", len(rig.data.bones),
    "action=", run_action.name,
    "frames=", tuple(round(value, 3) for value in run_action.frame_range),
    "glb=", GLB_PATH,
)
