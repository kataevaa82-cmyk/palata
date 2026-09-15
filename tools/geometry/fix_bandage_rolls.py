# -*- coding: utf-8 -*-
"""Correct the bandage rolls.

fix_pillows_and_labels.py dropped them onto medical_storage_rack_shelf.004,
which turned out to be the shelf ABOVE them: they rose 335 mm and ended up
sitting on the wrong board. Put each roll on the nearest shelf whose top is
below it instead of trusting a hard-coded name.
"""
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


def move_world(obj, delta):
    if obj.parent:
        obj.location = obj.location + (obj.parent.matrix_world.to_3x3().inverted() @ delta)
    else:
        obj.location = obj.location + delta


shelves = [o for o in bpy.data.objects
           if o.type == "MESH" and o.name.startswith("medical_storage_rack_shelf")]
print("SHELVES")
for shelf in sorted(shelves, key=lambda o: o.name):
    lo, hi = world_box([shelf])
    print("   %-34s x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f"
          % (shelf.name, lo.x, hi.x, lo.y, hi.y, lo.z, hi.z))

rolls = [o for o in bpy.data.objects
         if o.type == "MESH" and o.name.startswith("medical_storage_bandage_roll")]
for roll in sorted(rolls, key=lambda o: o.name):
    rlo, rhi = world_box([roll])
    centre = (rlo + rhi) * 0.5
    # Shelves the roll actually stands over, ranked by how close their top is
    # below the roll.
    below = []
    for shelf in shelves:
        slo, shi = world_box([shelf])
        if slo.x - 0.05 <= centre.x <= shi.x + 0.05 and slo.y - 0.05 <= centre.y <= shi.y + 0.05:
            below.append((shi.z, shelf.name))
    # The rolls belong in the slot under the top shelf, not on top of the
    # rack: take the highest shelf that still leaves them clear of the one
    # above.
    below = [entry for entry in below if entry[0] + (rhi.z - rlo.z) <= 2.113 - 0.01]
    if not below:
        print("ROLL_SKIPPED no shelf under", roll.name)
        continue
    top, name = max(below)
    delta_z = (top - 0.002) - rlo.z
    move_world(roll, Vector((0.0, 0.0, delta_z)))
    print("ROLL %-38s dz=%+.3f onto %s (top %.3f)" % (roll.name, delta_z, name, top))

bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print("ROLLS_SAVED", bpy.data.filepath)
