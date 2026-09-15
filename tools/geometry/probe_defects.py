# -*- coding: utf-8 -*-
"""Zoom in on the two defects the player reported.

For the signs: the first sweep measured the gap to whatever the ray hit, and
most signs sit 0.198 m in front of a door header - but a header is recessed
inside the reveal, so that number does not say whether the sign touches the
CORRIDOR wall. Measure against the wall panels instead, and print the two that
hit nothing at all next to their neighbours for comparison.

For the patient: print every body part sorted by height so the pose is legible.
A lying body 0.67 m thick is not lying.
"""
import bpy
from mathutils import Vector

depsgraph = bpy.context.evaluated_depsgraph_get()
scene = bpy.context.scene


def box(obj):
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for corner in obj.bound_box:
        point = obj.matrix_world @ Vector(corner)
        lo = Vector(min(lo[i], point[i]) for i in range(3))
        hi = Vector(max(hi[i], point[i]) for i in range(3))
    return lo, hi


print("SIGN_DETAIL_BEGIN")
for name in ["sign_back_-1_3", "sign_back_-1_4", "sign_back_-1_5", "sign_back_-1_7",
             "sign_back_1_3", "sign_back_1_5"]:
    plate = bpy.data.objects.get(name)
    if not plate:
        print("  %-18s MISSING" % name)
        continue
    lo, hi = box(plate)
    origin = plate.matrix_world.translation
    # Corridor walls face the corridor at y = +-1.55; a sign on the north side
    # backs onto y > 0. Report the plate's own back face against that plane.
    side = 1.0 if origin.y > 0 else -1.0
    back_face = hi.y if side > 0 else lo.y
    print("  %-18s pos=(%.2f, %.3f, %.2f) size=(%.2f, %.3f, %.2f) back_face_y=%.3f wall_y=%.3f gap_to_wall=%.3f"
          % (name, origin.x, origin.y, origin.z,
             hi.x - lo.x, hi.y - lo.y, hi.z - lo.z, back_face, side * 1.55,
             abs(side * 1.55 - back_face)))
    # What solid geometry is actually nearby?
    near = []
    for other in bpy.data.objects:
        if other.type != "MESH" or other is plate or other.name.startswith("sign_"):
            continue
        distance = (other.matrix_world.translation - origin).length
        if distance < 1.3:
            near.append((round(distance, 2), other.name))
    print("      near:", sorted(near)[:6])
print("SIGN_DETAIL_END")

print("PATIENT_PARTS_BEGIN")
parts = [o for o in bpy.data.objects
         if o.type == "MESH" and o.name.startswith("ward_1_bed_1_patient")]
rows = []
for obj in parts:
    lo, hi = box(obj)
    rows.append((lo.z, hi.z, obj.name))
rows.sort()
for lo_z, hi_z, name in rows:
    print("  %-46s z %.3f .. %.3f" % (name, lo_z, hi_z))
mattress = [o for o in bpy.data.objects
            if o.type == "MESH" and o.name.startswith("ward_1_bed_1_") and "mattress" in o.name.lower()]
for obj in mattress:
    lo, hi = box(obj)
    print("  MATTRESS %-37s z %.3f .. %.3f  x %.2f..%.2f  y %.2f..%.2f"
          % (obj.name, lo.z, hi.z, lo.x, hi.x, lo.y, hi.y))
print("PATIENT_PARTS_END")
