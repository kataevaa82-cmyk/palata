# -*- coding: utf-8 -*-
"""Replace the seven procedural ward bodies with one downloaded CC0 human.

The patient roots and their gameplay metadata are preserved.  Blankets and
chart cards are also preserved; every old procedural body/face mesh is removed.
The downloaded mesh is centred, scaled to 1.66 m and rotated supine so its head
rests on the existing pillow at local +Y.

Run:
  blender --background hospital_models_work.blend --python this_file.py
"""

import math
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, "C:/palata/tools")
from patient_textures import apply_static_patient_materials
from window_textures import apply_window_textures


SOURCE_GLB = "C:/palata/assets/third_party/supine-human-model/human_posed.glb"
BLEND_PATH = "C:/palata/hospital_models_work.blend"
EXPORT_SCRIPT = "C:/palata/tools/geometry/export_hospital_glb.py"

PATIENT_ROOTS = (
    "ward_1_bed_1_patient_v3",
    "ward_2_bed_1_patient_v3",
    "ward_3_bed_1_patient_v3",
    "ward_4_bed_1_patient_v3",
    "ward_5_bed_1_patient_v3",
    "ward_6_bed_1_patient_v3",
    "ward_6_bed_2_patient_v3",
)

# The source mesh is 5.535 units from sole to crown.
PATIENT_SCALE = 1.66 / 5.535
PATIENT_LOCATION = Vector((0.0, -0.02, 1.00))
PRESERVE_PARTS = ("blanket", "chart_card", "chart_red_stripe")

# Source axes: crown +Z, face +X. Target axes in the bed: crown +Y,
# face +Z, body width along X. This proper rotation (determinant +1) lays the
# patient on the back instead of leaving the face pointing sideways.
SUPINE_ROTATION = Matrix(((0.0, 1.0, 0.0),
                          (0.0, 0.0, 1.0),
                          (1.0, 0.0, 0.0))).to_4x4()


def import_source_mesh():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=SOURCE_GLB)
    imported = [obj for obj in bpy.data.objects if obj not in before]
    source = next((obj for obj in imported if obj.type == "MESH" and "human" in obj.name.lower()), None)
    if source is None:
        raise RuntimeError("Downloaded CC0 human mesh was not found after import")
    mesh = source.data.copy()
    mesh.name = "CC0_supine_patient_mesh"
    for obj in imported:
        bpy.data.objects.remove(obj, do_unlink=True)
    return mesh


def world_bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return tuple(min(point[i] for point in points) for i in range(3)), tuple(
        max(point[i] for point in points) for i in range(3)
    )


def rebuild_blanket(root):
    """Replace the old 5x5 angular sheet with a smooth fitted cloth shell."""
    name = root.name + "_patient_blanket"
    blanket = bpy.data.objects.get(name)
    if blanket is None:
        raise RuntimeError("Missing blanket for " + root.name)
    material = blanket.data.materials[0] if blanket.data.materials else None

    columns, rows = 17, 25
    x_min, x_max = -0.385, 0.385
    y_min, y_max = -0.94, 0.25
    verts = []
    faces = []
    for j in range(rows):
        y = y_min + (y_max - y_min) * j / (rows - 1)
        # Slightly fuller over the torso; smoothly lower toward the feet.
        if y < -0.72:
            rise = 0.285
        elif y < -0.28:
            rise = 0.300
        elif y < 0.10:
            rise = 0.325
        else:
            rise = 0.300
        for i in range(columns):
            x = x_min + (x_max - x_min) * i / (columns - 1)
            edge = abs(x) / x_max
            arch = max(0.0, 1.0 - edge ** 1.8) ** 1.18
            wrinkle = math.sin(y * 24.0 + x * 11.0) * 0.006 * arch
            z = 0.865 + rise * arch + wrinkle
            verts.append((x, y, z))
    for j in range(rows - 1):
        for i in range(columns - 1):
            a = j * columns + i
            b = a + 1
            c = a + columns + 1
            d = a + columns
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new(name + "_smooth_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.validate(clean_customdata=False)
    mesh.update()
    if material:
        mesh.materials.append(material)
    old_mesh = blanket.data
    blanket.data = mesh
    blanket.location = (0.0, 0.0, 0.0)
    blanket.rotation_euler = (0.0, 0.0, 0.0)
    blanket.scale = (1.0, 1.0, 1.0)
    blanket.modifiers.clear()
    subdivision = blanket.modifiers.new("Soft_cloth_surface", "SUBSURF")
    subdivision.subdivision_type = "CATMULL_CLARK"
    subdivision.levels = 1
    subdivision.render_levels = 1
    solidify = blanket.modifiers.new("Blanket_thickness", "SOLIDIFY")
    solidify.thickness = 0.018
    solidify.offset = -0.65
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    if old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)
    return blanket


mesh = import_source_mesh()
apply_static_patient_materials(mesh)
apply_window_textures()
report = []

for root_name in PATIENT_ROOTS:
    root = bpy.data.objects.get(root_name)
    if root is None:
        raise RuntimeError("Missing ward patient root: " + root_name)

    old_body = [
        obj for obj in list(root.children_recursive)
        if not any(token in obj.name.lower() for token in PRESERVE_PARTS)
    ]
    for obj in sorted(old_body, key=lambda item: len(item.children_recursive), reverse=True):
        if bpy.data.objects.get(obj.name) is not None:
            bpy.data.objects.remove(obj, do_unlink=True)

    collection = root.users_collection[0]
    patient = bpy.data.objects.new(root_name + "_patient_head", mesh)
    collection.objects.link(patient)
    patient.parent = root
    patient.matrix_parent_inverse = Matrix.Identity(4)
    patient.location = PATIENT_LOCATION
    patient.rotation_mode = "QUATERNION"
    patient.rotation_quaternion = SUPINE_ROTATION.to_quaternion()
    patient.scale = (PATIENT_SCALE,) * 3
    patient["asset_source"] = "UMRAM-Bilkent/supine-human-model"
    patient["license"] = "CC0-1.0"

    # The old procedural torso was flatter. Refit its 5x5 draped sheet around
    # the downloaded body: the centre arches over the chest/legs while the
    # side columns still fall toward the mattress. This avoids both clipping
    # and the appearance of a rigid blanket floating above the patient.
    blanket = rebuild_blanket(root)
    fold = bpy.data.objects.get(root_name + "_patient_blanket_top_fold")
    # The old decorative top fold reads as a separate bar on the blanket with
    # this body. Remove it completely, as requested.
    if fold:
        bpy.data.objects.remove(fold, do_unlink=True)

    bpy.context.view_layer.update()
    lo, hi = world_bounds(patient)

    # Face +X must end above back -X. This guards against laying the body on
    # its side in future rebuilds.
    face_point = patient.matrix_world @ Vector((0.34, 0.0, 2.36))
    back_point = patient.matrix_world @ Vector((-0.30, 0.0, 2.36))
    if face_point.z <= back_point.z + 0.12:
        raise RuntimeError(root_name + " is not lying face-up on its back")
    report.append((root_name, len(old_body), lo, hi))

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
exec(compile(open(EXPORT_SCRIPT, encoding="utf-8").read(), EXPORT_SCRIPT, "exec"))

for root_name, removed, lo, hi in report:
    print(
        "CC0_WARD_PATIENT",
        root_name,
        "removed=", removed,
        "bounds=", tuple(round(value, 3) for value in lo), tuple(round(value, 3) for value in hi),
    )
print("CC0_WARD_PATIENTS_REPLACED", len(report))
