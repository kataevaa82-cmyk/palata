import bpy
from mathutils import Vector


root = bpy.data.objects.get("ward_4_bed_1_patient_v3")
head = bpy.data.objects.get("ward_4_bed_1_patient_v3_patient_head")
if root is None or head is None:
    raise RuntimeError("Updated ward 4 patient was not found")


def nose_tip_world(head_obj):
    """The nose is sculpted into the head mesh, so there is no nose_tip object.

    In the head's local space the face always points +Y (see HEAD_PROFILE in
    build_care_gameplay_v2.py), so the frontmost local vertex is the nose tip
    regardless of which way the bed is rotated in the ward.
    """
    tip = max((vertex.co for vertex in head_obj.data.vertices), key=lambda co: co.y)
    return head_obj.matrix_world @ tip

props_collection = bpy.data.collections.get("PROPS")
if props_collection:
    props_collection.hide_viewport = False

patient_objects = {root, *root.children_recursive}
for obj in bpy.context.scene.objects:
    obj.hide_set(obj not in patient_objects)

for obj in bpy.context.view_layer.objects:
    obj.select_set(False)
face_tokens = (
    "_patient_head",
    "_patient_ear_",
    "_patient_closed_eye_",
    "_patient_brow_",
    "_patient_nostril",
    "_patient_upper_lip",
    "_patient_lower_lip",
    "_patient_hair_cap",
)
for obj in root.children_recursive:
    if any(token in obj.name for token in face_tokens):
        obj.hide_set(False)
        obj.select_set(True)
bpy.context.view_layer.objects.active = head

workspace = bpy.data.workspaces.get("Modeling") or bpy.data.workspaces.get("Layout")
if workspace:
    bpy.context.window.workspace = workspace

bpy.context.view_layer.update()
target = nose_tip_world(head) + Vector((0.0, 0.0, 0.025))
basis = root.matrix_world.to_3x3()
forward = (basis @ Vector((0.0, 1.0, 0.0))).normalized()
right = (basis @ Vector((1.0, 0.0, 0.0))).normalized()
up = (basis @ Vector((0.0, 0.0, 1.0))).normalized()
eye_position = target + forward * 0.72 + right * 0.16 + up * 0.09
view_rotation = (target - eye_position).to_track_quat("-Z", "Y")

for area in bpy.context.window.screen.areas:
    if area.type != "VIEW_3D":
        continue
    space = area.spaces.active
    space.shading.type = "SOLID"
    space.shading.color_type = "MATERIAL"
    space.shading.light = "STUDIO"
    space.shading.show_shadows = True
    space.shading.show_cavity = True
    space.overlay.show_floor = False
    region_3d = space.region_3d
    region_3d.view_location = target
    region_3d.view_distance = 0.72
    region_3d.view_rotation = view_rotation

print("PATIENT_FOCUSED", root.name, "face_parts", len(bpy.context.selected_objects))
