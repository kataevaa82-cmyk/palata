# -*- coding: utf-8 -*-
import bpy
from mathutils import Vector


def world_box(objs):
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in objs:
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            lo = Vector(min(lo[i], p[i]) for i in range(3)); hi = Vector(max(hi[i], p[i]) for i in range(3))
    return lo, hi


meshes = [o for o in bpy.data.objects if o.type == "MESH"]
for stem in ("sign_back_-1_4", "sign_back_-1_7", "sign_back_-1_6", "sign_back_-1_0", "sign_back_1_0"):
    suffix = stem[len("sign_back"):]
    parts = [o for o in bpy.data.objects if o.name.startswith("sign_back" + suffix)
             or o.name.startswith("sign_text" + suffix) or o.name.startswith("sign_frame" + suffix)]
    print("SIGN", stem, "parts=", [o.name for o in parts])
    for o in parts:
        lo, hi = world_box([o])
        body = o.data.body if o.type == "FONT" else ""
        print("   %-24s type=%-5s x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f  %s"
              % (o.name, o.type, lo.x, hi.x, lo.y, hi.y, lo.z, hi.z, body))

print("HEADERS")
for o in sorted([o for o in meshes if o.name.startswith("opening_header")], key=lambda o: o.name):
    lo, hi = world_box([o])
    print("   %-24s x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f" % (o.name, lo.x, hi.x, lo.y, hi.y, lo.z, hi.z))

print("NEAR_SIGN_-1_4")
target = bpy.data.objects.get("sign_back_-1_4")
if target:
    tlo, thi = world_box([target])
    c = (tlo + thi) * 0.5
    for o in meshes:
        lo, hi = world_box([o])
        if lo.x - 1.5 <= c.x <= hi.x + 1.5 and lo.y - 1.5 <= c.y <= hi.y + 1.5 and lo.z - 1.5 <= c.z <= hi.z + 1.5:
            print("   %-30s x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f" % (o.name, lo.x, hi.x, lo.y, hi.y, lo.z, hi.z))

print("MATERIALS")
for m in sorted(bpy.data.materials.keys()):
    print("   ", m)
