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


for prefix in ("linen_rack_left_v2", "linen_rack_right_v2", "sanitary_rack_v2"):
    print("RACK", prefix)
    parts = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(prefix)]
    for o in sorted(parts, key=lambda o: o.name):
        lo, hi = world_box([o])
        print("   %-42s x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f"
              % (o.name, lo.x, hi.x, lo.y, hi.y, lo.z, hi.z))
