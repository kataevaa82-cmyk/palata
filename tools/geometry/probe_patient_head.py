# -*- coding: utf-8 -*-
import bpy
from mathutils import Vector


def world_box(objects):
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for obj in objects:
        for corner in obj.bound_box:
            p = obj.matrix_world @ Vector(corner)
            lo = Vector(min(lo[i], p[i]) for i in range(3))
            hi = Vector(max(hi[i], p[i]) for i in range(3))
    return lo, hi


stem = "ward_1_bed_1_patient"
for o in sorted([o for o in bpy.data.objects
                 if o.type == "MESH" and o.name.startswith(stem)], key=lambda o: o.name):
    lo, hi = world_box([o])
    print("   %-52s x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f parent=%s"
          % (o.name.replace(stem + "_v3_patient_", ""), lo.x, hi.x, lo.y, hi.y, lo.z, hi.z,
             o.parent.name if o.parent else None))
