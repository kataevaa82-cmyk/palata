# -*- coding: utf-8 -*-
"""Work out which way the patient's face actually points.

The builder places the face on `face_surface_y()`, i.e. a face looking along +Y,
which is the pose of someone STANDING. The body is lying. Rather than trusting
either the code or the eye, measure the head's own frame from its features:

    ear axis      L ear  -> R ear      should end up along X (across the bed)
    face normal   head   -> nose       should end up +Z (up) for a supine patient
    chin axis     brow   -> lips       should end up -Y (toward the feet)
"""
import bpy
from mathutils import Vector

PATIENT = "ward_1_bed_1_patient_v3"


def centre(name_fragment, exact=None):
    picked = []
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.name.startswith(PATIENT):
            continue
        tail = obj.name[len(PATIENT):]
        if (exact and tail == exact) or (not exact and name_fragment in tail):
            picked.append(obj)
    if not picked:
        return None, []
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for obj in picked:
        for corner in obj.bound_box:
            point = obj.matrix_world @ Vector(corner)
            lo = Vector(min(lo[i], point[i]) for i in range(3))
            hi = Vector(max(hi[i], point[i]) for i in range(3))
    return (lo + hi) * 0.5, [o.name for o in picked]


print("HEAD_FRAME_BEGIN")
head, _ = centre(None, "_patient_head")
nose, _ = centre("_patient_nostril")
brow, _ = centre("_patient_brow")
lips, _ = centre("_patient_lip")
ear_l, _ = centre("_patient_ear_L")
ear_r, _ = centre("_patient_ear_R")
hair, _ = centre("_patient_hair")
for label, value in (("head", head), ("nose", nose), ("brow", brow), ("lips", lips),
                     ("ear_L", ear_l), ("ear_R", ear_r), ("hair", hair)):
    if value:
        print("  %-6s (%.3f, %.3f, %.3f)" % (label, value.x, value.y, value.z))

if head and nose:
    face_normal = (nose - head).normalized()
    print("  face_normal  (%+.2f, %+.2f, %+.2f)  <- wants (0, 0, +1) for a supine patient"
          % (face_normal.x, face_normal.y, face_normal.z))
if ear_l and ear_r:
    ear_axis = (ear_r - ear_l).normalized()
    print("  ear_axis     (%+.2f, %+.2f, %+.2f)  <- wants (+-1, 0, 0)"
          % (ear_axis.x, ear_axis.y, ear_axis.z))
if brow and lips:
    chin_axis = (lips - brow).normalized()
    print("  brow->lips   (%+.2f, %+.2f, %+.2f)  <- wants (0, -1, 0), chin toward the feet"
          % (chin_axis.x, chin_axis.y, chin_axis.z))

print("  --- every part of the patient ---")
rows = []
for obj in bpy.data.objects:
    if obj.type != "MESH" or not obj.name.startswith(PATIENT):
        continue
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for corner in obj.bound_box:
        point = obj.matrix_world @ Vector(corner)
        lo = Vector(min(lo[i], point[i]) for i in range(3))
        hi = Vector(max(hi[i], point[i]) for i in range(3))
    rows.append((round(((lo + hi) * 0.5).y, 3), obj.name[len(PATIENT) + 1:],
                 tuple(round(v, 3) for v in ((lo + hi) * 0.5)),
                 tuple(round(hi[i] - lo[i], 3) for i in range(3))))
for row in sorted(rows, reverse=True):
    print("   y=%7.3f %-26s centre=%s size=%s" % row)
print("HEAD_FRAME_END")
