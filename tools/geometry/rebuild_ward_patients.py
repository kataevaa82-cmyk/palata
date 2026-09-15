# -*- coding: utf-8 -*-
"""Rebuild the 7 bedridden ward patients and seat their heads correctly.

Three defects this replaces, all visible in build/patient_before/*.png:

1. THE HEAD WAS MIRRORED, NOT ROTATED.
   tools/fix_patient_head_orientation.py laid the head down with a raw axis
   relabelling `y <-> z`. A swap is a reflection (determinant -1), not a
   rotation: it turns the head inside out, so every swept detail built by
   tube_mesh (ears, brows, lips) ends up wound backwards and renders as a dark
   hollow. It also ran on raw mesh vertices, which is only valid for objects
   whose own matrix is identity - `_patient_neck` is a cylinder with a 90 deg
   object rotation, so the swap flung it 1.2 m down the bed onto the blanket,
   where the player sees a bare skin-coloured drum lying on the sheets.
   Here the same lay-down is a proper rotation, `(x, y, z) -> (-x, z, y)`
   about the chin anchor, applied in the patient root's space to every part of
   the head assembly, so nothing is reflected and nothing is left behind.

2. THE HEAD WAS TWICE LIFE SIZE.
   HEAD_PROFILE authors a skull 0.31 m wide, 0.37 m chin-to-crown and 0.30 m
   deep - roughly double an adult head - which is why the patient read as a
   dummy with a pumpkin on the pillow. The assembly is scaled about the same
   chin anchor to 0.165 x 0.235 x 0.196 m before it is laid down. Scaling the
   whole assembly (rather than editing HEAD_PROFILE) keeps brows, lids, lips,
   nostrils and ears exactly on the face_surface_y() surface they were solved
   against.

3. THE CHEST HAD NO SHOULDERS.
   The torso was one ellipsoid 0.57 m wide and 0.84 m long that tapered to a
   point where the neck should be, so the part left uncovered above the
   blanket read as a white lump. It is replaced by a lofted chest with real
   shoulders (0.47 m across) that the neck cylinder now actually meets.

The head keeps the seating the pillows were fitted to (bottom at z 0.960,
15 mm into the pillow), so tools/geometry/fix_pillows_and_labels.py does not
have to run again.

Run:  blender --background hospital_models_work.blend --python this_file.py
  or via the Blender MCP addon with that file already open.
"""

import math

import bpy
from mathutils import Matrix, Vector

LIBRARY = "C:/palata/tools/build_care_gameplay_v2.py"
BLEND_PATH = "C:/palata/hospital_models_work.blend"

HEAD_Y = 0.600            # sagittal anchor, matches build_care_gameplay_v2
HEAD_CHIN_Z = 0.955       # chin ring - the joint the head pivots around

# Target head size in metres (width, depth incl. nose, chin-to-crown).
HEAD_TARGET = Vector((0.165, 0.196, 0.235))
HEAD_BOTTOM_Z = 0.960     # back of the skull, 15 mm into the existing pillow

# Parts that ride with the skull. `_neck` is deliberately absent: it is rebuilt
# afterwards to bridge whatever gap the new head leaves.
HEAD_PARTS = ("_head", "_hair_cap", "_ear_", "_brow_", "_closed_eye_",
              "_nostril", "_upper_lip", "_lower_lip", "_forehead_bandage",
              "_oxygen_line")

# Lofted chest: (y, half width, top z, bottom z). y runs foot -> head.
CHEST_SECTIONS = (
    (-0.160, 0.200, 0.972, 0.796),
    (-0.020, 0.198, 0.984, 0.798),
    (0.140, 0.210, 0.996, 0.802),
    (0.280, 0.224, 1.004, 0.808),
    (0.400, 0.235, 1.008, 0.818),
    (0.480, 0.222, 1.006, 0.842),
    (0.532, 0.170, 1.000, 0.876),
    (0.566, 0.108, 0.992, 0.906),
)

NECK_RADIUS = 0.046      # scaled for HEAD_TARGET.x=0.165; 0.062 (tuned for the old
                          # 0.31 m head) was almost as wide as the new skull and its
                          # cap punched a dark crease into the underside of the chin


def load_library():
    namespace = {"CARE_GAMEPLAY_LIBRARY_ONLY": True}
    exec(compile(open(LIBRARY, encoding="utf-8").read(),
                 "build_care_gameplay_v2.py", "exec"), namespace)
    return namespace


def head_matrix():
    """Scale about the chin anchor, then lay the head back onto the pillow.

    `(x, y, z) -> (-x, z, y)` has determinant +1, so it is the rotation that
    takes the standing head (face +Y, crown +Z) to a supine one (face +Z,
    crown pointing up the bed) without reflecting it.
    """
    anchor = Vector((0.0, HEAD_Y, HEAD_CHIN_Z))
    scale = Matrix.Diagonal(Vector((
        HEAD_TARGET.x / 0.306,      # HEAD_PROFILE half width 0.155 -> 0.306 across
        HEAD_TARGET.y / 0.305,      # back of skull to nose tip
        HEAD_TARGET.z / 0.370,      # HEAD_CHIN_Z .. HEAD_APEX_Z
    ))).to_4x4()
    lay = Matrix(((-1.0, 0.0, 0.0, 0.0),
                  (0.0, 0.0, 1.0, 0.0),
                  (0.0, 1.0, 0.0, 0.0),
                  (0.0, 0.0, 0.0, 1.0)))
    return Matrix.Translation(anchor) @ lay @ scale @ Matrix.Translation(-anchor)


def bake(obj, matrix):
    """Apply `matrix` in the parent's space and bake it into the geometry.

    The transform carries a non-uniform scale, and Blender cannot store the
    resulting shear in an object's loc/rot/scale channels, so it goes into the
    mesh instead - which is also the convention every patient part already
    follows (identity object matrix, absolute coordinates in the vertices).
    """
    combined = matrix @ obj.matrix_local
    if obj.type in {"MESH", "CURVE"}:
        if obj.data.users > 1:
            obj.data = obj.data.copy()
        obj.data.transform(combined)
        if obj.type == "MESH":
            obj.data.update()
        obj.matrix_local = Matrix.Identity(4)
    else:
        obj.matrix_local = combined
    # matrix_local is a derived property (matrix_basis vs. parent_inverse); a
    # later read in the same Python call can still see the pre-bake value
    # until the view layer settles it. Cheap here (small per-patient object
    # counts), and skipping it is what let the second bake pass in run() see
    # a stale matrix_local and re-apply `matrix` on top of already-baked cube
    # objects (forehead_bandage/blanket_top_fold/chart_card) - the bug that
    # sent the forehead bandage to z 2.26 instead of 1.03.
    bpy.context.view_layer.update()


def local_box(objects):
    """Bounds in the patient root's space, read from the geometry.

    `obj.bound_box` is a cached value and still holds the pre-transform corners
    right after `Mesh.transform()`, so the vertices are read directly.
    """
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for obj in objects:
        if obj.type == "MESH":
            points = (obj.matrix_local @ v.co for v in obj.data.vertices)
        else:
            points = (obj.matrix_local @ Vector(c) for c in obj.bound_box)
        for p in points:
            lo = Vector(min(lo[i], p[i]) for i in range(3))
            hi = Vector(max(hi[i], p[i]) for i in range(3))
    return lo, hi


def recalc_normals(objects):
    """Point every face outward - tube_mesh winds its ear rings backwards.

    Draped cloth is skipped: the blanket is an open sheet, so its enclosed
    volume carries no meaning and "outward" would be a coin toss.
    """
    import bmesh
    fixed = 0
    for obj in objects:
        if obj.type != "MESH" or not obj.data.polygons or "blanket" in obj.name:
            continue
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        if bm.calc_volume(signed=True) < 0.0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
            fixed += 1
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()
    return fixed


def build_chest(root, gown_material, collection):
    """Loft the chest through CHEST_SECTIONS - an ellipsoid has no shoulders."""
    name = "%s_patient_torso" % root.name
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

    segments = 24
    rings = []
    for y, half_width, top, bottom in CHEST_SECTIONS:
        centre_z = (top + bottom) * 0.5
        half_height = (top - bottom) * 0.5
        ring = []
        for j in range(segments):
            theta = math.tau * j / segments
            s, c = math.sin(theta), math.cos(theta)
            # Squared-off underside: the back is flattened by the mattress.
            flat = 1.0 if c > 0 else 0.82
            ring.append((half_width * s, y, centre_z + half_height * c * flat))
        rings.append(ring)

    verts = []
    faces = []
    for ring in rings:
        verts.extend(ring)
    for i in range(len(rings) - 1):
        a, b = i * segments, (i + 1) * segments
        for j in range(segments):
            j2 = (j + 1) % segments
            faces.append((a + j, a + j2, b + j2, b + j))
    foot = len(verts)
    verts.append((0.0, CHEST_SECTIONS[0][0] - 0.02,
                  (CHEST_SECTIONS[0][2] + CHEST_SECTIONS[0][3]) * 0.5))
    for j in range(segments):
        faces.append((foot, (j + 1) % segments, j))
    neck = len(verts)
    verts.append((0.0, CHEST_SECTIONS[-1][0] + 0.02,
                  (CHEST_SECTIONS[-1][2] + CHEST_SECTIONS[-1][3]) * 0.5))
    base = (len(rings) - 1) * segments
    for j in range(segments):
        faces.append((neck, base + j, base + (j + 1) % segments))

    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.validate(clean_customdata=False)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.parent = root
    mesh.materials.append(gown_material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return obj


def rebuild_neck(root, library, collection, skin_material, head_parts):
    """A cylinder that actually spans chest to chin, sized to the new head."""
    name = "%s_patient_neck" % root.name
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

    hlo, hhi = local_box(head_parts)
    start = CHEST_SECTIONS[-1][0] - 0.060        # buried in the chest
    end = hlo.y + 0.040                          # buried in the jaw
    centre_z = HEAD_BOTTOM_Z + 0.030              # just proud of the pillow,
                                                   # under the jaw rather than
                                                   # mid-face
    return library["cylinder"](name, (0.0, (start + end) * 0.5, centre_z),
                               NECK_RADIUS, end - start, skin_material, collection,
                               root, rotation=(math.radians(90), 0, 0), vertices=24)


def run():
    library = load_library()
    matrix = head_matrix()

    report = []
    for object_name, patient_id, display_name, variant in library["PATIENTS"]:
        bed = bpy.data.objects.get(object_name.removesuffix("_patient_v3"))
        root = bpy.data.objects.get(object_name)
        if root is None or bed is None:
            report.append((object_name, "MISSING"))
            continue
        library["build_patient"](root, patient_id, display_name, variant)
        root = bpy.data.objects[object_name]

        # build_patient copies the bed's rotation_euler, but every bed root is
        # in QUATERNION mode, where that channel reads (0, 0, 0). Copying it
        # would silently drop the 180 deg turn on wards 4-6 and swing those
        # three patients round to face the wrong way down the bed.
        root.rotation_mode = bed.rotation_mode
        if bed.rotation_mode == "QUATERNION":
            root.rotation_quaternion = bed.rotation_quaternion.copy()
        else:
            root.rotation_euler = bed.rotation_euler.copy()

        collection = root.users_collection[0]
        parts = [o for o in root.children_recursive
                 if any(key in o.name for key in HEAD_PARTS)]
        for obj in parts:
            bake(obj, matrix)

        lo, hi = local_box(parts)
        lift = Matrix.Translation(Vector((0.0, 0.0, HEAD_BOTTOM_Z - lo.z)))
        for obj in parts:
            bake(obj, lift)

        gown = bpy.data.objects["%s_patient_hips" % root.name].data.materials[0]
        skin = bpy.data.objects["%s_patient_forearm_L" % root.name].data.materials[0]
        build_chest(root, gown, collection)
        rebuild_neck(root, library, collection, skin, parts)

        flipped = recalc_normals(list(root.children_recursive))
        hlo, hhi = local_box(parts)
        report.append((object_name,
                       "head y %.3f..%.3f z %.3f..%.3f width %.3f normals_fixed %d"
                       % (hlo.y, hhi.y, hlo.z, hhi.z, hhi.x - hlo.x, flipped)))

    bpy.context.view_layer.update()
    bpy.context.scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    for name, line in report:
        print("PATIENT", name, line)
    print("WARD_PATIENTS_REBUILT", len(report))


run()
