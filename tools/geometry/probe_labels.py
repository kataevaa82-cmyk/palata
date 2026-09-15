# -*- coding: utf-8 -*-
import bpy
from mathutils import Vector


def box(o):
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for c in o.bound_box:
        p = o.matrix_world @ Vector(c)
        lo = Vector(min(lo[i], p[i]) for i in range(3)); hi = Vector(max(hi[i], p[i]) for i in range(3))
    return lo, hi


print("LABEL_LIKE")
for o in sorted(bpy.context.scene.objects, key=lambda o: o.name):
    if "label" in o.name.lower() or "badge" in o.name.lower() or "plaque" in o.name.lower():
        lo, hi = box(o)
        mats = [m.name for m in o.data.materials] if o.type == "MESH" and o.data.materials else []
        print("   %-34s type=%-5s verts=%-4s x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f mats=%s"
              % (o.name, o.type,
                 len(o.data.vertices) if o.type == "MESH" else "-",
                 lo.x, hi.x, lo.y, hi.y, lo.z, hi.z, mats))
        print("        loc=%s rot=%s scale=%s parent=%s"
              % (tuple(round(v, 3) for v in o.location),
                 tuple(round(v, 3) for v in o.rotation_euler),
                 tuple(round(v, 3) for v in o.scale),
                 o.parent.name if o.parent else None))

print("NEIGHBOURS_nurse_station_label")
t = bpy.data.objects.get("nurse_station_label")
if t:
    tlo, thi = box(t)
    for o in bpy.context.scene.objects:
        if o.type != "MESH" or o is t:
            continue
        lo, hi = box(o)
        if lo.x - 0.6 <= thi.x and hi.x + 0.6 >= tlo.x and abs((lo.y + hi.y) / 2 - 1.38) < 1.0 and hi.z > 2.2 and lo.z < 3.1:
            print("   %-30s x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f" % (o.name, lo.x, hi.x, lo.y, hi.y, lo.z, hi.z))

print("NEIGHBOURS_room_zero_label")
t = bpy.data.objects.get("room_zero_label")
if t:
    tlo, thi = box(t)
    for o in bpy.context.scene.objects:
        if o.type != "MESH" or o is t:
            continue
        lo, hi = box(o)
        if lo.x - 0.6 <= thi.x and hi.x + 0.6 >= tlo.x and abs((lo.y + hi.y) / 2 - 1.45) < 1.0 and hi.z > 2.2 and lo.z < 3.1:
            print("   %-30s x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f" % (o.name, lo.x, hi.x, lo.y, hi.y, lo.z, hi.z))

print("BANDAGE")
for o in bpy.context.scene.objects:
    if o.name.endswith("forehead_bandage"):
        lo, hi = box(o)
        head = bpy.data.objects.get(o.name.replace("forehead_bandage", "head"))
        hlo, hhi = box(head) if head else (None, None)
        print("   %-52s z %.3f..%.3f  head z %.3f..%.3f y %.3f..%.3f | bandage y %.3f..%.3f"
              % (o.name, lo.z, hi.z, hlo.z, hhi.z, hlo.y, hhi.y, lo.y, hi.y))
