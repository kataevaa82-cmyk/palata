# -*- coding: utf-8 -*-
"""List the scene's object families with size and triangle budget.

The crude-primitive heuristics come back almost empty on this file - an earlier
pass bevelled everything - so choosing what to improve has to be done by looking
at the objects. This is the shortlist that feeds the render sheet.
"""
import bpy
import collections
from mathutils import Vector

groups = collections.defaultdict(lambda: {"objs": [], "tris": 0})


def family_of(name):
    lowered = name.lower()
    parts = lowered.split("_")
    if parts[0] in ("ward", "corridor", "room", "interaction", "care", "procedure", "medical", "level"):
        return "_".join(parts[:2])
    return parts[0]


for obj in bpy.data.objects:
    if obj.type != "MESH" or not obj.data.polygons:
        continue
    entry = groups[family_of(obj.name)]
    entry["objs"].append(obj)
    entry["tris"] += sum(max(len(p.vertices) - 2, 1) for p in obj.data.polygons)

rows = []
for name, entry in groups.items():
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for obj in entry["objs"]:
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            lo = Vector(min(lo[i], world[i]) for i in range(3))
            hi = Vector(max(hi[i], world[i]) for i in range(3))
    span = hi - lo
    rows.append((name, len(entry["objs"]), entry["tris"], max(span), entry["tris"] / max(len(entry["objs"]), 1)))

rows.sort(key=lambda row: -row[2])
print("SCENE_ROOTS")
print("%-26s %6s %8s %8s %9s" % ("family", "meshes", "tris", "span_m", "tris/mesh"))
for name, count, tris, span, per in rows[:45]:
    print("%-26s %6d %8d %8.2f %9.0f" % (name, count, tris, span, per))
print("SCENE_ROOTS_END families=%d" % len(rows))
