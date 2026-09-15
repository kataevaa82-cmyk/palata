# -*- coding: utf-8 -*-
"""Where do the corridor wall panels actually end, and where exactly is the neck?

The sign coverage test returned zero for every sign, which is either a broken
test or fifteen floating signs. Print the panels near one sign so the answer is
visible instead of inferred, plus the full boxes needed to place the neck.
"""
import bpy
from mathutils import Vector


def box(obj):
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for corner in obj.bound_box:
        point = obj.matrix_world @ Vector(corner)
        lo = Vector(min(lo[i], point[i]) for i in range(3))
        hi = Vector(max(hi[i], point[i]) for i in range(3))
    return lo, hi


print("PANELS_BEGIN")
target_x, target_y = -2.50, 1.535
rows = []
for obj in bpy.data.objects:
    if obj.type != "MESH":
        continue
    lower = obj.name.lower()
    if not (lower.startswith(("corridor_n_", "corridor_s_")) or "wall" in lower
            or "header" in lower or "partition" in lower):
        continue
    lo, hi = box(obj)
    if lo.x - 1.2 <= target_x <= hi.x + 1.2 and lo.y <= 2.4 and hi.y >= 0.9:
        rows.append((round(lo.z, 3), round(hi.z, 3), obj.name,
                     (round(lo.x, 2), round(hi.x, 2)), (round(lo.y, 2), round(hi.y, 2))))
for row in sorted(rows)[:14]:
    print("  z %6.3f..%6.3f  %-30s x=%s y=%s" % row)
print("  sign sits at z 2.505..2.775, y=1.535")
print("PANELS_END")

print("BODY_BEGIN")
for part in ("neck", "head", "torso", "hips", "blanket"):
    obj = bpy.data.objects.get("ward_1_bed_1_patient_v3_patient_" + part)
    if not obj:
        continue
    lo, hi = box(obj)
    centre = (lo + hi) * 0.5
    print("  %-8s world x %6.3f..%6.3f  y %6.3f..%6.3f  z %6.3f..%6.3f  centre=(%.3f, %.3f, %.3f) loc=(%.3f, %.3f, %.3f)"
          % (part, lo.x, hi.x, lo.y, hi.y, lo.z, hi.z, centre.x, centre.y, centre.z,
             obj.location.x, obj.location.y, obj.location.z))
print("BODY_END")
