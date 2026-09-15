import math

import bpy


BLEND_PATH = "C:/palata/palata_zero.blend"
GLB_PATH = "C:/palata/violent_patient_v1.glb"
COLLECTION_NAME = "ASSET_violent_patient_v1"
RIG_NAME = "violent_patient_rig"


def radians(values):
    return tuple(math.radians(value) for value in values)


def key_rotation(bone, frame, degrees):
    bone.rotation_mode = "XYZ"
    bone.rotation_euler = radians(degrees)
    bone.keyframe_insert("rotation_euler", frame=frame, group=bone.name)


def key_location(bone, frame, values):
    bone.location = values
    bone.keyframe_insert("location", frame=frame, group=bone.name)


collection = bpy.data.collections.get(COLLECTION_NAME)
rig = bpy.data.objects.get(RIG_NAME)
if collection is None or rig is None or rig.type != "ARMATURE":
    raise RuntimeError("The violent patient collection or armature was not found")
patient_objects = [obj for obj in list(collection.all_objects) if obj is not None]

old_action = rig.animation_data.action if rig.animation_data else None
rig.animation_data_clear()
for bone in rig.pose.bones:
    bone.rotation_mode = "XYZ"
    bone.rotation_euler = (0.0, 0.0, 0.0)
    bone.location = (0.0, 0.0, 0.0)
    bone.scale = (1.0, 1.0, 1.0)

# A 24-frame asymmetric walk cycle. The model keeps the aggressive hunch and
# the bed rail in the right hand, while both feet still pass through clear
# contact, down, passing and up poses.
frames = (1, 4, 7, 10, 13, 16, 19, 22, 25)
rotations = {
    "thigh.L": ((27, 0, 2), (17, 0, 1), (2, 0, 0), (-17, 0, -1), (-28, 0, -2), (-14, 0, -1), (1, 0, 0), (16, 0, 1), (27, 0, 2)),
    "thigh.R": ((-28, 0, -2), (-14, 0, -1), (1, 0, 0), (16, 0, 1), (27, 0, 2), (17, 0, 1), (2, 0, 0), (-17, 0, -1), (-28, 0, -2)),
    "shin.L": ((5, 0, 0), (17, 0, 0), (39, 0, 0), (24, 0, 0), (8, 0, 0), (5, 0, 0), (11, 0, 0), (31, 0, 0), (5, 0, 0)),
    "shin.R": ((8, 0, 0), (5, 0, 0), (11, 0, 0), (31, 0, 0), (5, 0, 0), (17, 0, 0), (39, 0, 0), (24, 0, 0), (8, 0, 0)),
    "foot.L": ((-10, 0, 0), (-4, 0, 0), (14, 0, 0), (9, 0, 0), (5, 0, 0), (0, 0, 0), (-12, 0, 0), (-5, 0, 0), (-10, 0, 0)),
    "foot.R": ((5, 0, 0), (0, 0, 0), (-12, 0, 0), (-5, 0, 0), (-10, 0, 0), (-4, 0, 0), (14, 0, 0), (9, 0, 0), (5, 0, 0)),
    "hips": ((2, 0, 4), (0, 0, 2), (-2, 0, 0), (0, 0, -2), (2, 0, -4), (0, 0, -2), (-2, 0, 0), (0, 0, 2), (2, 0, 4)),
    "spine": ((10, 0, -3), (12, 0, -1), (11, 0, 2), (9, 0, 4), (10, 0, 3), (12, 0, 1), (11, 0, -2), (9, 0, -4), (10, 0, -3)),
    "chest": ((8, 0, -4), (10, 0, -2), (9, 0, 2), (7, 0, 5), (8, 0, 4), (10, 0, 2), (9, 0, -2), (7, 0, -5), (8, 0, -4)),
    "neck": ((-2, 0, 2), (-1, 0, 1), (0, 0, -1), (1, 0, -2), (-2, 0, -2), (-1, 0, -1), (0, 0, 1), (1, 0, 2), (-2, 0, 2)),
    "head": ((3, 0, 5), (1, 0, 3), (-1, 0, 0), (1, 0, -3), (3, 0, -5), (1, 0, -3), (-1, 0, 0), (1, 0, 3), (3, 0, 5)),
    "upper_arm.L": ((-25, 0, -8), (-14, 0, -4), (0, 0, 0), (14, 0, 5), (25, 0, 8), (14, 0, 4), (0, 0, 0), (-14, 0, -5), (-25, 0, -8)),
    "forearm.L": ((-18, 0, 0), (-24, 0, 0), (-31, 0, 0), (-25, 0, 0), (-18, 0, 0), (-24, 0, 0), (-31, 0, 0), (-25, 0, 0), (-18, 0, 0)),
    "upper_arm.R": ((15, 0, 6), (9, 0, 4), (1, 0, 2), (-8, 0, -2), (-16, 0, -6), (-9, 0, -4), (-1, 0, -2), (8, 0, 2), (15, 0, 6)),
    "forearm.R": ((-35, 0, 0), (-43, 0, 0), (-50, 0, 0), (-44, 0, 0), (-36, 0, 0), (-43, 0, 0), (-51, 0, 0), (-44, 0, 0), (-35, 0, 0)),
}

for bone_name, poses in rotations.items():
    bone = rig.pose.bones.get(bone_name)
    if bone is None:
        raise RuntimeError(f"Missing required walk bone: {bone_name}")
    for frame, pose in zip(frames, poses):
        key_rotation(bone, frame, pose)

root_bone = rig.pose.bones.get("root")
root_locations = (
    (0.015, 0.0, 0.000), (0.008, 0.0, -0.025), (0.000, 0.0, 0.000), (-0.008, 0.0, 0.022),
    (-0.015, 0.0, 0.000), (-0.008, 0.0, -0.025), (0.000, 0.0, 0.000), (0.008, 0.0, 0.022), (0.015, 0.0, 0.000),
)
for frame, location in zip(frames, root_locations):
    key_location(root_bone, frame, location)

action = rig.animation_data.action if rig.animation_data else None
if action is None:
    raise RuntimeError("Blender did not create an action for the walk cycle")
for other_action in list(bpy.data.actions):
    if other_action != action and other_action.name.startswith("Violent_"):
        bpy.data.actions.remove(other_action)
action.name = "Violent_Walk"
action.use_fake_user = True
action["locomotion"] = "walk"
action["loop_frames"] = 24

# Blender 5 uses layered actions. Smooth every generated key without relying
# on the legacy Action.fcurves API.
curve_count = 0
key_count = 0
for layer in action.layers:
    for strip in layer.strips:
        for channelbag in strip.channelbags:
            for curve in channelbag.fcurves:
                curve_count += 1
                for point in curve.keyframe_points:
                    key_count += 1
                    point.interpolation = "BEZIER"
                    point.handle_left_type = "AUTO_CLAMPED"
                    point.handle_right_type = "AUTO_CLAMPED"

root = bpy.data.objects.get("violent_patient_v1")
if root:
    root["version"] = 2
    root["walk_action"] = action.name

scene = bpy.context.scene
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 25
scene.frame_set(1)
bpy.context.view_layer.update()

collection_visibility = {
    child.name: (child.hide_viewport, child.hide_render)
    for child in scene.collection.children
}
object_visibility = {
    obj.name: (obj.hide_viewport, obj.hide_render, obj.hide_get())
    for obj in patient_objects
}
for child in scene.collection.children:
    child.hide_viewport = child != collection
    child.hide_render = child != collection
for obj in bpy.context.view_layer.objects:
    obj.select_set(False)
for obj in patient_objects:
    obj.hide_viewport = False
    obj.hide_render = False
    obj.hide_set(False)
    if obj.type in {"MESH", "CURVE", "EMPTY", "ARMATURE"}:
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
    # Default ACTIONS mode also exported Orderly_Walk, because the exporter
    # matches actions to any armature whose pose bones they touch, and both
    # rigs use generic names (thigh.L, chest, ...). Godot then matched
    # "orderly_walk" against its own "walk" filter and animated the patient
    # with the wrong cycle. ACTIVE_ACTIONS exports only this rig's assigned
    # action, but merges it under a generic name unless told otherwise.
    export_animation_mode="ACTIVE_ACTIONS",
    export_nla_strips_merged_animation_name=action.name,
)

for obj in patient_objects:
    old = object_visibility.get(obj.name)
    if old:
        obj.hide_viewport, obj.hide_render = old[:2]
        obj.hide_set(old[2])
for child in scene.collection.children:
    old = collection_visibility.get(child.name)
    if old:
        child.hide_viewport, child.hide_render = old

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print(
    "VIOLENT_WALK_REBUILT",
    "action=", action.name,
    "bones=", len(rotations) + 1,
    "fcurves=", curve_count,
    "keys=", key_count,
    "frames=", tuple(action.frame_range),
    "export=", GLB_PATH,
)
