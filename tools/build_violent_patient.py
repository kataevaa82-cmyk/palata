import bpy
import math
from mathutils import Vector


BLEND_PATH = "C:/palata/palata_zero.blend"
GLB_PATH = "C:/palata/violent_patient_v1.glb"
COLLECTION_NAME = "ASSET_violent_patient_v1"


def material(name, base, dark, roughness=0.92, metallic=0.0, emission=None):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*base, 1.0)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    noise = nodes.new("ShaderNodeTexNoise")
    ramp = nodes.new("ShaderNodeValToRGB")
    bump = nodes.new("ShaderNodeBump")
    noise.inputs["Scale"].default_value = 9.0
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.74
    ramp.color_ramp.elements[0].color = (*dark, 1.0)
    ramp.color_ramp.elements[0].position = 0.20
    ramp.color_ramp.elements[1].color = (*base, 1.0)
    ramp.color_ramp.elements[1].position = 0.80
    shader.inputs["Base Color"].default_value = (*base, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    if emission:
        if "Emission Color" in shader.inputs:
            shader.inputs["Emission Color"].default_value = (*emission, 1.0)
            shader.inputs["Emission Strength"].default_value = 5.0
    bump.inputs["Strength"].default_value = 0.14
    bump.inputs["Distance"].default_value = 0.018
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return mat


def add_bone(armature, name, head, tail, parent=None):
    bone = armature.edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    if parent:
        bone.parent = armature.edit_bones.get(parent)
    return bone


def run():
    old_collection = bpy.data.collections.get(COLLECTION_NAME)
    if old_collection:
        for obj in list(old_collection.all_objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old_collection)
    collection = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(collection)

    gown = material("MAT_violent_patient_gown", (0.16, 0.29, 0.265), (0.025, 0.055, 0.045), 0.98)
    skin = material("MAT_violent_patient_skin", (0.46, 0.36, 0.27), (0.10, 0.055, 0.035), 0.96)
    bruise = material("MAT_violent_patient_bruise", (0.18, 0.055, 0.07), (0.035, 0.006, 0.012), 0.98)
    bandage = material("MAT_violent_patient_bandage", (0.58, 0.55, 0.40), (0.18, 0.14, 0.08), 0.99)
    hair = material("MAT_violent_patient_hair", (0.035, 0.025, 0.015), (0.003, 0.002, 0.001), 0.98)
    eye = material("MAT_violent_patient_eye", (0.46, 0.025, 0.01), (0.08, 0.002, 0.001), 0.34, emission=(0.70, 0.015, 0.003))
    shoe = material("MAT_violent_patient_shoe", (0.025, 0.028, 0.022), (0.002, 0.003, 0.002), 0.92)
    metal = material("MAT_violent_patient_metal", (0.30, 0.31, 0.27), (0.06, 0.055, 0.04), 0.72, 0.52)
    rust = material("MAT_violent_patient_rust", (0.34, 0.065, 0.012), (0.055, 0.006, 0.001), 1.0, 0.10)

    root = bpy.data.objects.new("violent_patient_v1", None)
    collection.objects.link(root)
    root["asset_type"] = "rigged_violent_patient"
    root["version"] = 1

    armature = bpy.data.armatures.new("violent_patient_skeleton")
    rig = bpy.data.objects.new("violent_patient_rig", armature)
    collection.objects.link(rig)
    rig.parent = root
    rig.show_in_front = True

    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    add_bone(armature, "root", (0, 0, 0.03), (0, 0, 0.38))
    add_bone(armature, "hips", (0, 0, 0.38), (0, 0, 0.78), "root")
    add_bone(armature, "spine", (0, 0, 0.72), (0, 0, 1.22), "hips")
    add_bone(armature, "chest", (0, 0, 1.12), (0, -0.035, 1.43), "spine")
    add_bone(armature, "neck", (0, -0.035, 1.40), (0, -0.06, 1.56), "chest")
    add_bone(armature, "head", (0, -0.06, 1.54), (0, -0.09, 1.82), "neck")
    add_bone(armature, "upper_arm.L", (0.25, -0.02, 1.36), (0.37, -0.05, 1.08), "chest")
    add_bone(armature, "forearm.L", (0.37, -0.05, 1.08), (0.34, -0.14, 0.82), "upper_arm.L")
    add_bone(armature, "hand.L", (0.34, -0.14, 0.82), (0.32, -0.20, 0.68), "forearm.L")
    add_bone(armature, "upper_arm.R", (-0.25, -0.02, 1.36), (-0.36, -0.12, 1.08), "chest")
    add_bone(armature, "forearm.R", (-0.36, -0.12, 1.08), (-0.27, -0.28, 0.84), "upper_arm.R")
    add_bone(armature, "hand.R", (-0.27, -0.28, 0.84), (-0.22, -0.36, 0.69), "forearm.R")
    add_bone(armature, "thigh.L", (0.11, 0, 0.72), (0.12, 0.01, 0.40), "hips")
    add_bone(armature, "shin.L", (0.12, 0.01, 0.40), (0.11, -0.02, 0.11), "thigh.L")
    add_bone(armature, "foot.L", (0.11, -0.02, 0.11), (0.11, -0.23, 0.055), "shin.L")
    add_bone(armature, "thigh.R", (-0.11, 0, 0.72), (-0.12, -0.01, 0.40), "hips")
    add_bone(armature, "shin.R", (-0.12, -0.01, 0.40), (-0.11, -0.02, 0.11), "thigh.R")
    add_bone(armature, "foot.R", (-0.11, -0.02, 0.11), (-0.11, -0.23, 0.055), "shin.R")
    bpy.ops.object.mode_set(mode="OBJECT")

    def link_object(obj, name, mat, bone=None):
        obj.name = name
        for owner in list(obj.users_collection):
            owner.objects.unlink(obj)
        collection.objects.link(obj)
        if mat:
            obj.data.materials.append(mat)
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
        if bone:
            world = obj.matrix_world.copy()
            obj.parent = rig
            obj.parent_type = "BONE"
            obj.parent_bone = bone
            obj.matrix_world = world
        else:
            obj.parent = root
        return obj

    def sphere(name, location, scale, mat, bone=None, segments=24):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=16, location=location)
        obj = bpy.context.object
        obj.scale = scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        return link_object(obj, name, mat, bone)

    def cube(name, location, size, mat, bone=None, rotation=(0, 0, 0)):
        bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
        obj = bpy.context.object
        obj.scale = tuple(value * 0.5 for value in size)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bevel = obj.modifiers.new("worn_edges", "BEVEL")
        bevel.width = 0.018
        bevel.segments = 2
        return link_object(obj, name, mat, bone)

    def cylinder_between(name, start, end, radius, mat, bone=None, vertices=20):
        start_v = Vector(start)
        end_v = Vector(end)
        direction = end_v - start_v
        midpoint = (start_v + end_v) * 0.5
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=direction.length, location=midpoint)
        obj = bpy.context.object
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
        obj.rotation_mode = "XYZ"
        return link_object(obj, name, mat, bone)

    # Crooked institutional gown and hunched torso.
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.29, radius2=0.23, depth=0.70, location=(0, 0, 0.98))
    link_object(bpy.context.object, "violent_gown_skirt", gown, "hips")
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.23, radius2=0.29, depth=0.53, location=(0, -0.01, 1.27))
    link_object(bpy.context.object, "violent_gown_torso", gown, "spine")
    cube("violent_gown_torn_hem", (0.03, -0.16, 0.66), (0.38, 0.025, 0.12), bandage, "hips", (0.0, 0.0, 0.08))

    sphere("violent_patient_head", (0, -0.055, 1.68), (0.135, 0.115, 0.16), skin, "head", 30)
    sphere("violent_patient_bruise", (0.065, -0.159, 1.70), (0.040, 0.008, 0.052), bruise, "head", 18)
    for x in (-0.043, 0.043):
        sphere("violent_patient_eye", (x, -0.165, 1.725), (0.016, 0.008, 0.012), eye, "head", 16)
    cube("violent_patient_clenched_mouth", (0, -0.168, 1.635), (0.065, 0.010, 0.015), hair, "head")
    for x, z, scale in ((-0.07, 1.80, (0.07, 0.07, 0.08)), (0.02, 1.825, (0.09, 0.07, 0.07)), (0.08, 1.77, (0.06, 0.06, 0.09))):
        sphere("violent_patient_matted_hair", (x, -0.01, z), scale, hair, "head", 18)

    # Arms and hands are separate rigid pieces driven by the arm bones.
    cylinder_between("violent_upper_arm_L", (0.25, -0.02, 1.36), (0.37, -0.05, 1.08), 0.075, gown, "upper_arm.L")
    cylinder_between("violent_forearm_L", (0.37, -0.05, 1.08), (0.34, -0.14, 0.82), 0.052, bandage, "forearm.L")
    sphere("violent_fist_L", (0.32, -0.20, 0.72), (0.065, 0.055, 0.08), skin, "hand.L", 20)
    cylinder_between("violent_upper_arm_R", (-0.25, -0.02, 1.36), (-0.36, -0.12, 1.08), 0.075, gown, "upper_arm.R")
    cylinder_between("violent_forearm_R", (-0.36, -0.12, 1.08), (-0.27, -0.28, 0.84), 0.052, skin, "forearm.R")
    sphere("violent_fist_R", (-0.22, -0.36, 0.73), (0.068, 0.058, 0.082), skin, "hand.R", 20)
    cylinder_between("violent_broken_bed_rail", (-0.23, -0.37, 0.73), (-0.16, -0.48, 1.42), 0.018, metal, "hand.R", 14)
    sphere("violent_rail_rust", (-0.18, -0.45, 1.20), (0.022, 0.018, 0.08), rust, "hand.R", 14)

    cylinder_between("violent_thigh_L", (0.11, 0, 0.72), (0.12, 0.01, 0.40), 0.090, gown, "thigh.L")
    cylinder_between("violent_shin_L", (0.12, 0.01, 0.40), (0.11, -0.02, 0.11), 0.065, skin, "shin.L")
    sphere("violent_shoe_L", (0.11, -0.13, 0.075), (0.095, 0.17, 0.060), shoe, "foot.L", 20)
    cylinder_between("violent_thigh_R", (-0.11, 0, 0.72), (-0.12, -0.01, 0.40), 0.090, gown, "thigh.R")
    cylinder_between("violent_shin_R", (-0.12, -0.01, 0.40), (-0.11, -0.02, 0.11), 0.065, skin, "shin.R")
    sphere("violent_shoe_R", (-0.11, -0.13, 0.075), (0.095, 0.17, 0.060), shoe, "foot.R", 20)

    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="POSE")
    animation = {
        "thigh.L": ((1, (24, 0, 0)), (9, (-24, 0, 0)), (17, (24, 0, 0)), (25, (-24, 0, 0)), (33, (24, 0, 0))),
        "thigh.R": ((1, (-24, 0, 0)), (9, (24, 0, 0)), (17, (-24, 0, 0)), (25, (24, 0, 0)), (33, (-24, 0, 0))),
        "upper_arm.L": ((1, (-42, 0, -10)), (9, (18, 0, 8)), (17, (-42, 0, -10)), (25, (18, 0, 8)), (33, (-42, 0, -10))),
        "upper_arm.R": ((1, (30, 0, 12)), (9, (-34, 0, -10)), (17, (30, 0, 12)), (25, (-34, 0, -10)), (33, (30, 0, 12))),
        "forearm.R": ((1, (-28, 0, 0)), (9, (-62, 0, 0)), (17, (-28, 0, 0)), (25, (-62, 0, 0)), (33, (-28, 0, 0))),
        "chest": ((1, (15, 0, -4)), (9, (20, 0, 5)), (17, (15, 0, -4)), (25, (20, 0, 5)), (33, (15, 0, -4))),
        "head": ((1, (8, 0, -8)), (9, (2, 0, 9)), (17, (8, 0, -8)), (25, (2, 0, 9)), (33, (8, 0, -8))),
    }
    for bone_name, keys in animation.items():
        bone = rig.pose.bones[bone_name]
        bone.rotation_mode = "XYZ"
        for frame, degrees in keys:
            bone.rotation_euler = tuple(math.radians(value) for value in degrees)
            bone.keyframe_insert("rotation_euler", frame=frame, group=bone_name)
    root_bone = rig.pose.bones["root"]
    for frame, z in ((1, 0.0), (5, 0.035), (9, 0.0), (13, 0.035), (17, 0.0), (21, 0.035), (25, 0.0), (29, 0.035), (33, 0.0)):
        root_bone.location = (0, 0, z)
        root_bone.keyframe_insert("location", frame=frame, group="root")
    bpy.ops.object.mode_set(mode="OBJECT")
    if rig.animation_data and rig.animation_data.action:
        rig.animation_data.action.name = "Violent_Run"

    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 32
    scene.frame_set(1)
    for child_collection in scene.collection.children:
        child_collection.hide_viewport = child_collection != collection
    collection.hide_viewport = False
    collection.hide_render = False

    bpy.ops.object.select_all(action="DESELECT")
    for obj in collection.all_objects:
        if obj.type in {"MESH", "CURVE", "EMPTY", "ARMATURE"}:
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
    )
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"VIOLENT_PATIENT bones={len(rig.data.bones)} meshes={sum(1 for o in collection.all_objects if o.type == 'MESH')} export={GLB_PATH}")


run()
