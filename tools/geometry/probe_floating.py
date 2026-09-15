# -*- coding: utf-8 -*-
"""Find genuinely floating small objects by proximity, not by ray casting.

For every reasonably small mesh whose bottom is above the floor, measure the
shortest distance from its bounding box to any other mesh's bounding box.
Anything with no neighbour within a few centimetres is hanging in the air.
"""
import bpy
from mathutils import Vector

EXPORT_TYPES = {"MESH", "CURVE", "FONT", "EMPTY", "LIGHT"}
skipped = bpy.data.collections.get("glTF_not_exported")
skipped_objects = set(skipped.all_objects) if skipped else set()

print("EXCLUDED_FROM_GLB count=%d" % len(skipped_objects))
for o in sorted(skipped_objects, key=lambda o: o.name)[:40]:
    print("   ", o.name)

print("SIGN_OBJECTS")
for o in sorted([o for o in bpy.data.objects if o.name.startswith("sign_")], key=lambda o: o.name):
    print("   %-24s type=%-5s in_glb=%s hide_render=%s hide_viewport=%s"
          % (o.name, o.type, o not in skipped_objects, o.hide_render, o.hide_viewport))

print("HEADER_STATUS")
for name in ("opening_header_S_5", "opening_header_S_8", "opening_header_S_7"):
    o = bpy.data.objects.get(name)
    if o is None:
        print("   %s MISSING" % name)
        continue
    print("   %-22s in_glb=%s hide_render=%s hide_viewport=%s in_view_layer=%s"
          % (name, o not in skipped_objects, o.hide_render, o.hide_viewport,
             o.name in bpy.context.view_layer.objects))


def box(o):
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for c in o.bound_box:
        p = o.matrix_world @ Vector(c)
        lo = Vector(min(lo[i], p[i]) for i in range(3)); hi = Vector(max(hi[i], p[i]) for i in range(3))
    return lo, hi


meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and o not in skipped_objects]
boxes = {o.name: box(o) for o in meshes}


def gap(a, b):
    alo, ahi = a
    blo, bhi = b
    d = 0.0
    for i in range(3):
        if alo[i] > bhi[i]:
            d += (alo[i] - bhi[i]) ** 2
        elif blo[i] > ahi[i]:
            d += (blo[i] - ahi[i]) ** 2
    return d ** 0.5


print("FLOATING_BEGIN")
found = 0
for o in meshes:
    lo, hi = boxes[o.name]
    size = hi - lo
    volume = size.x * size.y * size.z
    if lo.z < 0.9 or volume > 1.5 or max(size) > 2.5:
        continue
    best = 1e9
    best_name = ""
    for other in meshes:
        if other is o:
            continue
        # ignore parts of the same fixture: same name stem before the last _
        d = gap((lo, hi), boxes[other.name])
        if d < best:
            best, best_name = d, other.name
        if best <= 0.0:
            break
    if best > 0.03:
        found += 1
        print("   FLOATING %-34s gap=%.3f nearest=%-28s x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f"
              % (o.name, best, best_name, lo.x, hi.x, lo.y, hi.y, lo.z, hi.z))
print("FLOATING_END count=%d" % found)
