# -*- coding: utf-8 -*-
"""Settle everything that stands on a storage rack onto its shelf.

The proximity probe flagged four folded-linen stacks as floating; measuring the
racks showed the same 62 mm gap under every stack on every shelf - the stacks
were placed by shelf index rather than by the shelf surface. The same pass
covers the sanitary and medical racks, and lowers the sanitary rack top shelf,
which sat 33 mm above the tops of its own uprights.

Run: blender --background hospital_models_work.blend --python this_file.py
"""
import bpy
from mathutils import Vector

RACKS = ("linen_rack_left_v2", "linen_rack_right_v2", "sanitary_rack_v2",
         "medical_storage_rack")
MIN_GAP = 0.004
MAX_GAP = 0.20


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


meshes = [o for o in bpy.data.objects if o.type == "MESH"]
settled = 0

# The sanitary rack top shelf hovered above its uprights; drop it onto them
# before anything is settled onto it.
shelf = bpy.data.objects.get("sanitary_rack_v2_shelf.004")
uprights = [o for o in meshes if o.name.startswith("sanitary_rack_v2_upright")]
if shelf and uprights:
    slo, shi = world_box([shelf])
    _ulo, uhi = world_box(uprights)
    delta_z = uhi.z - shi.z
    if abs(delta_z) > 1e-4:
        move_world(shelf, Vector((0.0, 0.0, delta_z)))
        print("SHELF sanitary_rack_v2_shelf.004 dz=%+.3f (onto uprights at %.3f)"
              % (delta_z, uhi.z))

for rack in RACKS:
    parts = [o for o in meshes if o.name.startswith(rack)]
    shelves = [o for o in parts if "_shelf" in o.name]
    items = [o for o in parts if "_shelf" not in o.name and "_upright" not in o.name]
    if not shelves or not items:
        continue
    shelf_boxes = [(world_box([s]), s.name) for s in shelves]
    for item in sorted(items, key=lambda o: o.name):
        ilo, ihi = world_box([item])
        centre = (ilo + ihi) * 0.5
        candidates = []
        for (slo, shi), name in shelf_boxes:
            over = (slo.x - 0.02 <= centre.x <= shi.x + 0.02
                    and slo.y - 0.02 <= centre.y <= shi.y + 0.02)
            if over and shi.z <= ilo.z + 0.001:
                candidates.append((shi.z, name))
        if not candidates:
            continue
        top, name = max(candidates)
        gap = ilo.z - top
        if not (MIN_GAP < gap <= MAX_GAP):
            continue
        move_world(item, Vector((0.0, 0.0, -gap + 0.002)))
        settled += 1
        print("SETTLE %-44s dz=%+.3f onto %s" % (item.name, -gap + 0.002, name))

print("SETTLED count=%d" % settled)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print("SETTLE_SAVED", bpy.data.filepath)
