import bpy
import math


BLEND_PATH = "C:/palata/palata_zero.blend"
GLB_PATH = "C:/palata/orderly_ghost_v6.glb"
COLLECTION_NAME = "ASSET_orderly_ghost_v5"


def rebuild_material(material, base, dark, roughness=0.9, metallic=0.0, emission=None, alpha=1.0):
    material.use_nodes = True
    material.diffuse_color = (*base, alpha)
    if alpha < 1.0:
        material.surface_render_method = "DITHERED"
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    noise = nodes.new("ShaderNodeTexNoise")
    ramp = nodes.new("ShaderNodeValToRGB")
    bump = nodes.new("ShaderNodeBump")
    noise.inputs["Scale"].default_value = 8.0
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.72
    ramp.color_ramp.elements[0].color = (*dark, alpha)
    ramp.color_ramp.elements[0].position = 0.22
    ramp.color_ramp.elements[1].color = (*base, alpha)
    ramp.color_ramp.elements[1].position = 0.78
    shader.inputs["Base Color"].default_value = (*base, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Alpha"].default_value = alpha
    if emission:
        if "Emission Color" in shader.inputs:
            shader.inputs["Emission Color"].default_value = (*emission, 1.0)
            shader.inputs["Emission Strength"].default_value = 7.0
        elif "Emission" in shader.inputs:
            shader.inputs["Emission"].default_value = (*emission, 1.0)
            shader.inputs["Emission Strength"].default_value = 7.0
    bump.inputs["Strength"].default_value = 0.16
    bump.inputs["Distance"].default_value = 0.018
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])


def rebuild_ghost_materials():
    settings = {
        "MAT_orderly_v5_old_uniform": ((0.105, 0.16, 0.125), (0.018, 0.035, 0.026), 0.97, 0.0, None, 1.0),
        "MAT_orderly_v5_old_apron": ((0.36, 0.34, 0.255), (0.075, 0.065, 0.040), 0.98, 0.0, None, 1.0),
        "MAT_orderly_v5_grey_hood": ((0.20, 0.215, 0.19), (0.025, 0.031, 0.026), 0.98, 0.0, None, 1.0),
        "MAT_orderly_v5_face_void": ((0.002, 0.002, 0.001), (0.0, 0.0, 0.0), 1.0, 0.0, None, 1.0),
        "MAT_orderly_v5_grey_hands": ((0.30, 0.30, 0.275), (0.075, 0.075, 0.062), 0.96, 0.0, None, 1.0),
        "MAT_orderly_v5_black_shoes": ((0.012, 0.013, 0.010), (0.001, 0.001, 0.001), 0.92, 0.0, None, 1.0),
        "MAT_orderly_v5_worn_metal": ((0.25, 0.27, 0.23), (0.045, 0.05, 0.038), 0.74, 0.42, None, 1.0),
        "MAT_orderly_v5_blue_bucket": ((0.025, 0.11, 0.19), (0.004, 0.016, 0.030), 0.68, 0.22, None, 1.0),
        "MAT_orderly_v5_rust": ((0.30, 0.055, 0.012), (0.055, 0.008, 0.002), 1.0, 0.12, None, 1.0),
        "MAT_orderly_v5_eye_glow": ((0.18, 0.015, 0.005), (0.04, 0.001, 0.0), 0.3, 0.0, (1.0, 0.045, 0.012), 1.0),
        "MAT_orderly_v5_mist": ((0.08, 0.10, 0.085), (0.005, 0.007, 0.006), 1.0, 0.0, None, 0.18),
    }
    for name, values in settings.items():
        material = bpy.data.materials.get(name)
        if material:
            rebuild_material(material, *values)


def add_bone(armature, name, head, tail, parent=None):
    bone = armature.edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    if parent:
        bone.parent = armature.edit_bones.get(parent)
    return bone


def bone_parent(obj, rig, bone_name):
    if not obj:
        return
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone_name
    obj.matrix_world = world
    obj.animation_data_clear()


def key_rotation(pose_bone, frame, xyz):
    pose_bone.rotation_mode = "XYZ"
    pose_bone.rotation_euler = tuple(math.radians(value) for value in xyz)
    pose_bone.keyframe_insert("rotation_euler", frame=frame, group=pose_bone.name)


def build_rig(collection, root):
    old = bpy.data.objects.get("orderly_v6_rig")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    old_data = bpy.data.armatures.get("orderly_v6_skeleton")
    if old_data and old_data.users == 0:
        bpy.data.armatures.remove(old_data)

    armature = bpy.data.armatures.new("orderly_v6_skeleton")
    rig = bpy.data.objects.new("orderly_v6_rig", armature)
    collection.objects.link(rig)
    rig.parent = root
    rig.show_in_front = True
    rig["rig_type"] = "humanoid_orderly_walk"

    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    add_bone(armature, "root", (0, 0, 0.02), (0, 0, 0.43))
    add_bone(armature, "pelvis", (0, 0, 0.43), (0, 0, 0.70), "root")
    add_bone(armature, "spine", (0, 0, 0.64), (0, 0, 1.30), "pelvis")
    add_bone(armature, "neck", (0, 0, 1.28), (0, 0, 1.53), "spine")
    add_bone(armature, "head", (0, 0, 1.50), (0, 0, 1.84), "neck")
    add_bone(armature, "upper_arm.L", (0, 0.255, 1.27), (0, 0.255, 0.94), "spine")
    add_bone(armature, "forearm.L", (0, 0.255, 0.94), (0.07, 0.255, 0.67), "upper_arm.L")
    add_bone(armature, "hand.L", (0.07, 0.255, 0.67), (0.11, 0.255, 0.49), "forearm.L")
    add_bone(armature, "upper_arm.R", (0, -0.270, 1.22), (0, -0.270, 0.89), "spine")
    add_bone(armature, "forearm.R", (0, -0.270, 0.89), (0.06, -0.270, 0.62), "upper_arm.R")
    add_bone(armature, "hand.R", (0.06, -0.270, 0.62), (0.11, -0.270, 0.44), "forearm.R")
    add_bone(armature, "thigh.L", (0, 0.11, 0.50), (0, 0.11, 0.20), "pelvis")
    add_bone(armature, "shin.L", (0, 0.11, 0.20), (0.02, 0.11, -0.08), "thigh.L")
    add_bone(armature, "foot.L", (0.02, 0.11, -0.08), (0.22, 0.11, -0.16), "shin.L")
    add_bone(armature, "thigh.R", (0, -0.11, 0.50), (0, -0.11, 0.20), "pelvis")
    add_bone(armature, "shin.R", (0, -0.11, 0.20), (0.02, -0.11, -0.08), "thigh.R")
    add_bone(armature, "foot.R", (0.02, -0.11, -0.08), (0.22, -0.11, -0.16), "shin.R")
    bpy.ops.object.mode_set(mode="POSE")

    poses = {
        "thigh.L": ((1, (0, -18, 0)), (17, (0, 18, 0)), (33, (0, -18, 0))),
        "thigh.R": ((1, (0, 18, 0)), (17, (0, -18, 0)), (33, (0, 18, 0))),
        "shin.L": ((1, (0, 5, 0)), (9, (0, 16, 0)), (17, (0, 4, 0)), (25, (0, 10, 0)), (33, (0, 5, 0))),
        "shin.R": ((1, (0, 4, 0)), (9, (0, 10, 0)), (17, (0, 5, 0)), (25, (0, 16, 0)), (33, (0, 4, 0))),
        "foot.L": ((1, (0, -3, 0)), (9, (0, 6, 0)), (17, (0, 2, 0)), (25, (0, -2, 0)), (33, (0, -3, 0))),
        "foot.R": ((1, (0, 2, 0)), (9, (0, -2, 0)), (17, (0, -3, 0)), (25, (0, 6, 0)), (33, (0, 2, 0))),
        "upper_arm.L": ((1, (0, 15, 2)), (17, (0, -15, -2)), (33, (0, 15, 2))),
        "upper_arm.R": ((1, (0, -8, -3)), (17, (0, 8, 3)), (33, (0, -8, -3))),
        "forearm.L": ((1, (0, 8, 0)), (17, (0, 16, 0)), (33, (0, 8, 0))),
        "forearm.R": ((1, (0, 14, 0)), (17, (0, 6, 0)), (33, (0, 14, 0))),
        "pelvis": ((1, (0, -1, -1.5)), (17, (0, 1, 1.5)), (33, (0, -1, -1.5))),
        "spine": ((1, (0, -2, -0.8)), (17, (0, 2, 0.8)), (33, (0, -2, -0.8))),
        "head": ((1, (0, 0, -2.5)), (17, (0, 0, 2.5)), (33, (0, 0, -2.5))),
    }
    for bone_name, keys in poses.items():
        for frame, rotation in keys:
            key_rotation(rig.pose.bones[bone_name], frame, rotation)
    root_bone = rig.pose.bones["root"]
    root_bone.location = (0, 0, 0)
    root_bone.keyframe_insert("location", frame=1, group="root")
    root_bone.location = (0, 0, 0.025)
    root_bone.keyframe_insert("location", frame=9, group="root")
    root_bone.location = (0, 0, 0)
    root_bone.keyframe_insert("location", frame=17, group="root")
    root_bone.location = (0, 0, 0.025)
    root_bone.keyframe_insert("location", frame=25, group="root")
    root_bone.location = (0, 0, 0)
    root_bone.keyframe_insert("location", frame=33, group="root")
    bpy.ops.object.mode_set(mode="OBJECT")

    if rig.animation_data and rig.animation_data.action:
        rig.animation_data.action.name = "Orderly_Walk"

    bpy.context.view_layer.update()
    bone_parent(bpy.data.objects.get("ghost_body_pivot"), rig, "spine")
    bone_parent(bpy.data.objects.get("ghost_head_pivot"), rig, "head")
    bone_parent(bpy.data.objects.get("ghost_l_arm_pivot"), rig, "upper_arm.L")
    bone_parent(bpy.data.objects.get("ghost_r_arm_pivot"), rig, "upper_arm.R")
    bone_parent(bpy.data.objects.get("ghost_l_leg_pivot"), rig, "thigh.L")
    bone_parent(bpy.data.objects.get("ghost_r_leg_pivot"), rig, "thigh.R")
    return rig


def run():
    collection = bpy.data.collections.get(COLLECTION_NAME)
    root = bpy.data.objects.get("orderly_anomaly_v5")
    if not collection or not root:
        raise RuntimeError("Orderly v5 collection/root missing")

    for child_collection in bpy.context.scene.collection.children:
        child_collection.hide_viewport = child_collection != collection
    collection.hide_viewport = False
    collection.hide_render = False
    for obj in collection.all_objects:
        obj.hide_viewport = False
        obj.hide_render = False
        obj.hide_set(False)
    bpy.context.view_layer.update()

    rebuild_ghost_materials()
    rig = build_rig(collection, root)
    root["version"] = 6
    root["armature"] = rig.name
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 32
    bpy.context.scene.frame_set(1)

    bpy.ops.object.select_all(action="DESELECT")
    for obj in collection.all_objects:
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
    )
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"ORDERLY_V6 rig_bones={len(rig.data.bones)} export={GLB_PATH}")


run()
