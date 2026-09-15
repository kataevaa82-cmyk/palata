# -*- coding: utf-8 -*-
"""Fix what the player reported plus everything measurably floating with it.

1. PILLOWS. Every bed carried TWO pillows, each 0.837 x 0.538 x 0.240, on a
   1.34 m wide bed: they overlapped each other by 0.378 m and merged into one
   pale slab across the whole head end. Their material was
   MAT_offwhite_painted_wood - wood on a pillow. And the pillow top (z 1.030)
   was above the head bottom (z 0.960), so every head was buried 70 mm inside
   the slab.

   Fix: one pillow per bed, 0.70 x 0.42 x 0.18, seated on the mattress and
   sized so the head rests on it with about 15 mm of compression, in linen.
   Applied to all 12 beds, not only the 7 with patients - otherwise beds in
   the same ward would visibly disagree.

2. FLOATING SIGN TEXT. nurse_station_label is a bare text mesh with no backing
   plate and no parent, hanging 147 mm in front of the nurse-station doorframe,
   over the opening. room_zero_label hangs 97 mm off the corridor wall. Both
   get pushed back flush so they read as lettering applied to the surface; the
   nurse-station one also moves up onto its header, because the wall behind its
   lower half is the open doorway.

3. The same proximity probe found more floaters, all fixed by dropping them
   onto whatever they are supposed to rest on: two forehead bandages hovering
   42 mm above the heads they belong to, and three bandage rolls 62 mm above a
   storage shelf.

Run: blender --background hospital_models_work.blend --python this_file.py
"""
import bpy
from mathutils import Vector

PILLOW_DIMS = Vector((0.70, 0.42, 0.18))
PILLOW_SINK = 0.015          # how far the pillow settles into the mattress
PILLOW_EDGE_GAP = 0.020      # gap between pillow and the head end of the bed
PILLOW_MATERIAL = "MAT_faded_hospital_linen"


def world_box(objects):
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for obj in objects:
        for corner in obj.bound_box:
            p = obj.matrix_world @ Vector(corner)
            lo = Vector(min(lo[i], p[i]) for i in range(3))
            hi = Vector(max(hi[i], p[i]) for i in range(3))
    return lo, hi


def set_world_translation(obj, target):
    """Place the object origin at a world point, parent or no parent."""
    if obj.parent:
        obj.location = obj.parent.matrix_world.inverted() @ target
    else:
        obj.location = target


def move_world(obj, delta):
    if obj.parent:
        obj.location = obj.location + (obj.parent.matrix_world.to_3x3().inverted() @ delta)
    else:
        obj.location = obj.location + delta


meshes = [o for o in bpy.data.objects if o.type == "MESH"]
linen = bpy.data.materials.get(PILLOW_MATERIAL)
if linen is None:
    raise SystemExit("material %s not found" % PILLOW_MATERIAL)

# ---------------------------------------------------------------- pillows ----

removed = []
reshaped = []
for ward in range(1, 7):
    for bed in (1, 2):
        stem = "ward_%d_bed_%d_" % (ward, bed)
        keep = bpy.data.objects.get(stem + "pillow_left")
        drop = bpy.data.objects.get(stem + "pillow_right")
        mattress = [o for o in meshes
                    if o.name.startswith(stem) and "mattress" in o.name.lower()]
        if keep is None or not mattress:
            print("PILLOW_SKIPPED", stem)
            continue

        if drop is not None:
            removed.append(drop.name)

        mlo, mhi = world_box(mattress)
        plo, phi = world_box([keep])
        pillow_centre = (plo + phi) * 0.5
        mattress_centre = (mlo + mhi) * 0.5

        # The head end of the bed is the long end the pillow already sits at.
        if pillow_centre.y >= mattress_centre.y:
            head_end = mhi.y
            centre_y = head_end - PILLOW_EDGE_GAP - PILLOW_DIMS.y * 0.5
        else:
            head_end = mlo.y
            centre_y = head_end + PILLOW_EDGE_GAP + PILLOW_DIMS.y * 0.5

        target = Vector((mattress_centre.x,
                         centre_y,
                         mhi.z - PILLOW_SINK + PILLOW_DIMS.z * 0.5))

        current = Vector(keep.dimensions)          # scale is 1 on every pillow
        keep.scale = Vector((PILLOW_DIMS.x / current.x,
                             PILLOW_DIMS.y / current.y,
                             PILLOW_DIMS.z / current.z))
        set_world_translation(keep, target)
        keep.data.materials.clear()
        keep.data.materials.append(linen)
        reshaped.append((keep.name, target))

for name in removed:
    bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

meshes = [o for o in bpy.data.objects if o.type == "MESH"]

# ----------------------------------------------------------------- labels ----

labels_fixed = []


def mount_flush(label_name, surface_name, proud=0.006, lift=None):
    label = bpy.data.objects.get(label_name)
    surface = bpy.data.objects.get(surface_name)
    if label is None or surface is None:
        print("LABEL_SKIPPED", label_name, surface_name)
        return
    llo, lhi = world_box([label])
    slo, shi = world_box([surface])
    # The corridor is on whichever side of the surface the label already faces.
    if (llo.y + lhi.y) * 0.5 < (slo.y + shi.y) * 0.5:
        delta_y = (slo.y - proud) - llo.y
    else:
        delta_y = (shi.y + proud) - lhi.y
    delta = Vector((0.0, delta_y, 0.0))
    if lift is not None:
        delta.z = lift
    move_world(label, delta)
    labels_fixed.append((label_name, surface_name, delta.y, delta.z))


# The nurse-station text had the open doorway behind its lower half, so it also
# rises onto the header, level with the door signs (their text is z 2.705..2.790).
nurse = bpy.data.objects.get("nurse_station_label")
if nurse is not None:
    nlo, nhi = world_box([nurse])
    mount_flush("nurse_station_label", "opening_header_N_5",
                lift=2.7475 - (nlo.z + nhi.z) * 0.5)

# The other one sits on a plain stretch of corridor wall; it only needs to touch it.
mount_flush("room_zero_label", "corridor_N_7_R_upper")

# --------------------------------------------------------------- floaters ----

dropped = []


def drop_onto(obj_name, support_names, clearance=0.002):
    obj = bpy.data.objects.get(obj_name)
    supports = [bpy.data.objects[n] for n in support_names if n in bpy.data.objects]
    if obj is None or not supports:
        print("DROP_SKIPPED", obj_name)
        return
    olo, _ohi = world_box([obj])
    _slo, shi = world_box(supports)
    delta_z = (shi.z - clearance) - olo.z
    if abs(delta_z) < 1e-6:
        return
    move_world(obj, Vector((0.0, 0.0, delta_z)))
    dropped.append((obj_name, delta_z))


for bandage in [o for o in meshes if o.name.endswith("_patient_forehead_bandage")]:
    head = bandage.name.replace("_forehead_bandage", "_head")
    # A forehead bandage belongs against the head, not floating over it.
    drop_onto(bandage.name, [head], clearance=0.010)

for roll in [o for o in meshes if o.name.startswith("medical_storage_bandage_roll")]:
    drop_onto(roll.name, ["medical_storage_rack_shelf.004"])

# ------------------------------------------------------------------ report ---

print("FIX_PILLOWS removed=%d reshaped=%d dims=%.2fx%.2fx%.2f material=%s"
      % (len(removed), len(reshaped), PILLOW_DIMS.x, PILLOW_DIMS.y, PILLOW_DIMS.z,
         PILLOW_MATERIAL))
for name, target in reshaped:
    print("   %-34s centre (%.3f, %.3f, %.3f)" % (name, target.x, target.y, target.z))
print("FIX_LABELS count=%d" % len(labels_fixed))
for name, surface, dy, dz in labels_fixed:
    print("   %-22s onto %-22s dy=%+.3f dz=%+.3f" % (name, surface, dy, dz))
print("FIX_DROPPED count=%d" % len(dropped))
for name, dz in dropped:
    print("   %-52s dz=%+.3f" % (name, dz))

bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print("FIX_SAVED", bpy.data.filepath)
