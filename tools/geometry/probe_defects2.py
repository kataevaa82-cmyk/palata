# -*- coding: utf-8 -*-
"""Pin down both defects exactly.

Signs: the earlier ray test was unreliable (it starts on the wall surface and
can pass straight through). Instead, for each sign look for a corridor wall
panel that actually covers the sign's footprint on that side of the corridor.
A sign with no panel behind it is the one hanging in the air.

Patient: print the transforms of neck, head and torso. The neck's box sits below
the hips and through the mattress, so it is either rotated or offset wrong.
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


walls = [o for o in bpy.data.objects
         if o.type == "MESH" and (o.name.lower().startswith(("corridor_n_", "corridor_s_"))
                                  or "wall" in o.name.lower())]
print("WALLS total=%d" % len(walls))

print("SIGN_COVER_BEGIN")
for plate in sorted((o for o in bpy.data.objects if o.name.startswith("sign_back")),
                    key=lambda o: (o.matrix_world.translation.y < 0, o.matrix_world.translation.x)):
    lo, hi = box(plate)
    origin = plate.matrix_world.translation
    side = "N" if origin.y > 0 else "S"
    covering = []
    for wall in walls:
        wlo, whi = box(wall)
        # same side of the corridor, and overlapping the sign in x and z
        if (wlo.y - 0.35) <= origin.y <= (whi.y + 0.35):
            if wlo.x <= hi.x and whi.x >= lo.x and wlo.z <= hi.z and whi.z >= lo.z:
                covering.append(wall.name)
    print("  %-18s %s x=%7.2f z=%.2f  covering_panels=%d %s"
          % (plate.name, side, origin.x, origin.z, len(covering), covering[:3]))
print("SIGN_COVER_END")

print("NECK_BEGIN")
for ward in (1, 2):
    for part in ("neck", "head", "torso", "hips"):
        obj = bpy.data.objects.get("ward_%d_bed_1_patient_v3_patient_%s" % (ward, part))
        if not obj:
            print("  missing", ward, part)
            continue
        lo, hi = box(obj)
        print("  w%d %-6s loc=(%.3f, %.3f, %.3f) rot=(%.1f, %.1f, %.1f) dim=(%.3f, %.3f, %.3f) z=%.3f..%.3f"
              % (ward, part, obj.location.x, obj.location.y, obj.location.z,
                 *[round(a * 57.2958, 1) for a in obj.rotation_euler],
                 obj.dimensions.x, obj.dimensions.y, obj.dimensions.z, lo.z, hi.z))
    root = bpy.data.objects.get("ward_%d_bed_1_patient_v3" % ward)
    if root:
        print("  w%d root loc=(%.3f, %.3f, %.3f) rot=(%.1f, %.1f, %.1f)"
              % (ward, root.location.x, root.location.y, root.location.z,
                 *[round(a * 57.2958, 1) for a in root.rotation_euler]))
print("NECK_END")
