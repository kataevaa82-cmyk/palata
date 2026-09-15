# -*- coding: utf-8 -*-
"""Fix the two defects the player reported.

1. THE PATIENT SUNK INTO THE BED.
   `*_patient_neck` has its object origin at z 1.035 but its vertices 0.355 m
   below and 0.355 m toward the feet - the signature of a part that was left
   behind when the body was rotated from standing to lying. The result: the neck
   lies at z 0.585..0.775 while the mattress surface is 0.810, so it pokes down
   through the mattress and out under the bed, dragging the whole body's
   bounding box with it.

   The mesh is offset from its own origin, so the fix moves the OBJECT by the
   difference between where the neck is and where the torso/head junction is,
   measured per patient rather than hard-coded.

2. THE SIGN HANGING IN THE AIR.
   Each door sign sits at z 2.505..2.775, but the wall panels stop at the edges
   of the doorway and the header above the opening only starts at z 2.590. The
   bottom 85 mm of every sign therefore overhangs into the open doorway with
   nothing behind it. Raise each sign (plate and text together) until it sits
   inside its own header.

Run: blender --background hospital_models_work.blend --python this_file.py
"""
import bpy
from mathutils import Vector

CLEARANCE = 0.015


def box(obj):
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for corner in obj.bound_box:
        point = obj.matrix_world @ Vector(corner)
        lo = Vector(min(lo[i], point[i]) for i in range(3))
        hi = Vector(max(hi[i], point[i]) for i in range(3))
    return lo, hi


# ------------------------------------------------------------------ necks ----

necks_fixed = []
for neck in [o for o in bpy.data.objects
             if o.type == "MESH" and o.name.endswith("_patient_neck")]:
    stem = neck.name[:-len("_neck")]
    torso = bpy.data.objects.get(stem + "_torso")
    head = bpy.data.objects.get(stem + "_head")
    if not torso or not head:
        print("NECK_SKIPPED no torso/head for", neck.name)
        continue

    tlo, thi = box(torso)
    hlo, hhi = box(head)
    nlo, nhi = box(neck)
    centre = (nlo + nhi) * 0.5

    # The body lies along whichever horizontal axis the head is displaced on.
    torso_centre = (tlo + thi) * 0.5
    head_centre = (hlo + hhi) * 0.5
    along_y = abs(head_centre.y - torso_centre.y) >= abs(head_centre.x - torso_centre.x)

    wanted = Vector(centre)
    if along_y:
        # Bridge the gap between the head end of the torso and the head itself.
        torso_end = thi.y if head_centre.y > torso_centre.y else tlo.y
        head_end = hlo.y if head_centre.y > torso_centre.y else hhi.y
        wanted.y = (torso_end + head_end) * 0.5
        wanted.x = torso_centre.x
    else:
        torso_end = thi.x if head_centre.x > torso_centre.x else tlo.x
        head_end = hlo.x if head_centre.x > torso_centre.x else hhi.x
        wanted.x = (torso_end + head_end) * 0.5
        wanted.y = torso_centre.y
    # Sit the neck between the top of the torso and the middle of the head, so
    # it reads as joining them instead of floating over or under either.
    wanted.z = (thi.z + head_centre.z) * 0.5

    delta = wanted - centre
    neck.location = neck.location + delta
    necks_fixed.append((neck.name, delta.length))

# ------------------------------------------------------------------ signs ----

headers = [o for o in bpy.data.objects
           if o.type == "MESH" and o.name.startswith("opening_header_")]
signs_fixed = []
for plate in [o for o in bpy.data.objects if o.name.startswith("sign_back")]:
    plo, phi = box(plate)
    centre = (plo + phi) * 0.5
    # The header for this doorway: same side of the corridor, overlapping in x.
    candidates = []
    for header in headers:
        hlo, hhi = box(header)
        if (hlo.y - 0.4) <= centre.y <= (hhi.y + 0.4) and hlo.x <= centre.x <= hhi.x:
            candidates.append((hlo, hhi, header.name))
    if not candidates:
        print("SIGN_SKIPPED no header behind", plate.name)
        continue
    hlo, hhi, header_name = candidates[0]
    lift = (hlo.z + CLEARANCE) - plo.z
    if lift <= 0.0:
        continue
    if phi.z + lift > hhi.z:
        print("SIGN_SKIPPED %s would rise above %s" % (plate.name, header_name))
        continue

    moved = [plate]
    # The text belongs to the same sign: sign_back_1_4 -> sign_text_1_4.
    suffix = plate.name[len("sign_back"):]
    for companion in bpy.data.objects:
        if companion.name.startswith("sign_text" + suffix) or \
                companion.name.startswith("sign_frame" + suffix):
            moved.append(companion)
    for obj in moved:
        obj.location.z += lift
    signs_fixed.append((plate.name, lift, len(moved), header_name))

print("FIX_NECKS count=%d" % len(necks_fixed))
for name, distance in necks_fixed:
    print("   %-46s moved %.3f m" % (name, distance))
print("FIX_SIGNS count=%d" % len(signs_fixed))
for name, lift, parts, header_name in signs_fixed:
    print("   %-18s raised %.3f m (%d parts) onto %s" % (name, lift, parts, header_name))

bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print("FIX_SAVED", bpy.data.filepath)
