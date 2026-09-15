# -*- coding: utf-8 -*-
"""Measure every pillow against its mattress, its bed frame and the patient
head that is supposed to rest on it."""
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


def fmt(lo, hi):
    return "x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f" % (lo.x, hi.x, lo.y, hi.y, lo.z, hi.z)


meshes = [o for o in bpy.data.objects if o.type == "MESH"]
pillows = sorted([o for o in meshes if "pillow" in o.name.lower()], key=lambda o: o.name)
print("PILLOW_COUNT", len(pillows))
for p in pillows:
    lo, hi = world_box([p])
    print("  %-46s %s  dims %.3f x %.3f x %.3f" % (p.name, fmt(lo, hi), *p.dimensions))

print("BEDS_BEGIN")
for ward in range(0, 8):
    for bed in (1, 2, 3, 4):
        stem = "ward_%d_bed_%d_" % (ward, bed)
        parts = [o for o in meshes if o.name.startswith(stem)]
        if not parts:
            continue
        mat = [o for o in parts if "mattress" in o.name.lower()]
        pil = [o for o in parts if "pillow" in o.name.lower()]
        head = [o for o in parts if o.name.endswith("_head")]
        pat = [o for o in parts if "_patient" in o.name]
        line = "  %s parts=%d patient=%d" % (stem, len(parts), len(pat))
        if mat:
            mlo, mhi = world_box(mat)
            line += " | mattress %s" % fmt(mlo, mhi)
        if pil:
            plo, phi = world_box(pil)
            line += " | pillow %s" % fmt(plo, phi)
        if head:
            hlo, hhi = world_box(head)
            line += " | head %s" % fmt(hlo, hhi)
        print(line)
        for o in sorted(pil, key=lambda o: o.name):
            olo, ohi = world_box([o])
            mats = [m.name for m in o.data.materials] if o.data.materials else []
            print("      %-46s %s verts=%d mats=%s" % (o.name, fmt(olo, ohi), len(o.data.vertices), mats))
print("BEDS_END")
