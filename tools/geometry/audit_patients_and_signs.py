# -*- coding: utf-8 -*-
"""Find the two reported defects by measurement rather than by eye.

1. A patient sunk into the bed: compare each ward patient's lowest point with
   the top of the mattress it lies on. A body whose underside is BELOW the
   mattress surface is inside it.

2. A sign floating off the wall: every sign has a back plate that is meant to
   sit against something. Cast a short ray straight back from the plate and
   report the gap; a sign with nothing behind it within a few centimetres is
   hanging in the air.

Run: blender --background hospital_models_work.blend --python this.py
"""
import bpy
from mathutils import Vector

depsgraph = bpy.context.evaluated_depsgraph_get()


def world_box(objects):
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for obj in objects:
        for corner in obj.bound_box:
            point = obj.matrix_world @ Vector(corner)
            lo = Vector(min(lo[i], point[i]) for i in range(3))
            hi = Vector(max(hi[i], point[i]) for i in range(3))
    return lo, hi


def group(prefix):
    return [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(prefix)]


print("PATIENTS_BEGIN")
for ward in range(1, 7):
    for bed in (1, 2):
        patient = group("ward_%d_bed_%d_patient" % (ward, bed))
        if not patient:
            continue
        mattress = [o for o in group("ward_%d_bed_%d_" % (ward, bed))
                    if "mattress" in o.name.lower()]
        sheet = [o for o in group("ward_%d_bed_%d_" % (ward, bed))
                 if "sheet" in o.name.lower() or "blanket" in o.name.lower()]
        if not mattress:
            print("  ward%d_bed%d NO_MATTRESS" % (ward, bed))
            continue
        plo, phi = world_box(patient)
        mlo, mhi = world_box(mattress)
        # Ignore the blanket that is meant to lie over the body.
        body = [o for o in patient if "blanket" not in o.name.lower()]
        blo, bhi = world_box(body) if body else (plo, phi)
        print("  ward%d_bed%d parts=%2d body_bottom=%.3f mattress_top=%.3f sink=%+.3f body_top=%.3f"
              % (ward, bed, len(patient), blo.z, mhi.z, mhi.z - blo.z, bhi.z))
print("PATIENTS_END")

print("SIGNS_BEGIN")
scene = bpy.context.scene
for plate in sorted(group("sign_back"), key=lambda o: o.name):
    origin = plate.matrix_world.translation
    # The plate is thin in one axis; that axis points at the wall.
    dims = plate.dimensions
    axis = min(range(3), key=lambda i: dims[i])
    normal = Vector((0, 0, 0))
    normal[axis] = 1.0
    normal = (plate.matrix_world.to_3x3() @ normal).normalized()
    best = None
    for direction in (normal, -normal):
        start = origin + direction * (dims[axis] * 0.5 + 0.002)
        hit, location, _n, _i, obj, _m = scene.ray_cast(depsgraph, start, direction, distance=0.60)
        if hit:
            gap = (location - origin).length - dims[axis] * 0.5
            if best is None or gap < best[0]:
                best = (gap, obj.name)
    if best is None:
        print("  %-22s FLOATING nothing within 0.60 m  at %s"
              % (plate.name, tuple(round(v, 2) for v in origin)))
    else:
        print("  %-22s gap=%.3f m behind=%s" % (plate.name, best[0], best[1]))
print("SIGNS_END")
