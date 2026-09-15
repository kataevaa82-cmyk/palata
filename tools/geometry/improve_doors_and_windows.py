# -*- coding: utf-8 -*-
"""Model the two things the player stands closest to: the doors and the windows.

Measured before touching anything (tools/geometry/render_family_sheet.py):

    door    6 meshes    972 tris     window  7 meshes   1408 tris
    sink   29 meshes  17564 tris     bed    72 meshes  23678 tris

A door leaf was a slab with a hole for the glass - no handle at all, no hinges,
no glazing bead, no panel. A proximity sweep of everything within 1.6 m of a
leaf confirmed it: jambs, header, glass, sign. Nothing to grab. The windows are
a single bevelled box with three bars laid over the pane.

Rules this file obeys:

* door parts are parented to `pivot_hospital_door_*`, the empty door.gd swings -
  a handle that stays behind when the door opens is worse than no handle;
* every door part carries `door_detail` in its name, which main.gd's
  _needs_collision() explicitly excludes, so 225 new decorative meshes do not
  become 225 new colliders inside a doorway that is already solid;
* window parts avoid every _needs_collision() token, exactly as the existing
  `window_mullion_*` do;
* positions are derived from each leaf's own bounding box in pivot space, so a
  mirrored south-side door gets its hinges and handle on the correct edges
  rather than inside the wall.

Run: blender --background hospital_models_work.blend --python this_file.py
"""

import math

import bpy
from mathutils import Vector

SMOOTH_ANGLE = math.radians(37.0)
NEW_OBJECTS = []


def mat(name, fallback=None):
    material = bpy.data.materials.get(name)
    if material is None and fallback:
        material = bpy.data.materials.get(fallback)
    if material is None:
        raise KeyError("material %s is not in this blend" % name)
    return material


def _register(obj, name, collection, parent):
    obj.name = name
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    obj.parent = parent
    obj.matrix_parent_inverse.identity()
    NEW_OBJECTS.append(obj)
    return obj


def cube(name, location, size, material, collection, parent, rotation=(0, 0, 0), bevel=0.004, segments=2):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.scale = tuple(v * 0.5 for v in size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("soft_worn_edges", "BEVEL")
        modifier.width = bevel
        modifier.segments = segments
        modifier.limit_method = "ANGLE"
    return _register(obj, name, collection, parent)


def cylinder(name, location, radius, depth, material, collection, parent,
             rotation=(0, 0, 0), vertices=20, scale=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                        location=location, rotation=rotation)
    obj = bpy.context.object
    if scale:
        obj.scale = scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return _register(obj, name, collection, parent)


def local_box(obj, parent):
    """The object's bounding box expressed in `parent`'s local space."""
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    to_parent = parent.matrix_world.inverted() @ obj.matrix_world
    for corner in obj.bound_box:
        point = to_parent @ Vector(corner)
        lo = Vector(min(lo[i], point[i]) for i in range(3))
        hi = Vector(max(hi[i], point[i]) for i in range(3))
    return lo, hi


# ------------------------------------------------------------------ doors ----

def build_door(pivot, leaf, glass):
    collection = leaf.users_collection[0]
    tag = leaf.name.replace("hospital_door_", "")
    paint = leaf.data.materials[0] if leaf.data.materials else mat("MAT_care_old_enamel")
    metal = mat("MAT_care_worn_metal")

    lo, hi = local_box(leaf, pivot)
    thickness = hi.y - lo.y
    # The pivot sits on the hinge edge, so whichever end of the leaf is nearer
    # x = 0 carries the hinges and the other one the handle. Doing it by sign
    # keeps mirrored doors correct.
    hinge_x = lo.x if abs(lo.x) < abs(hi.x) else hi.x
    handle_x = hi.x if hinge_x == lo.x else lo.x
    inward = -1.0 if handle_x > hinge_x else 1.0     # from the handle toward the hinge
    mid_y = (lo.y + hi.y) * 0.5
    face = thickness * 0.5

    # Hinges: barrel plus its two knuckle plates, at the three usual heights.
    for index, height in enumerate((lo.z + 0.30, (lo.z + hi.z) * 0.5, hi.z - 0.30)):
        barrel_x = hinge_x - inward * 0.012
        cylinder("door_detail_hinge_barrel_%s_%d" % (tag, index),
                 (barrel_x, mid_y, height), 0.016, 0.11, metal, collection, pivot, vertices=16)
        cube("door_detail_hinge_plate_%s_%d" % (tag, index),
             (hinge_x + inward * 0.035, mid_y, height), (0.075, thickness + 0.006, 0.085),
             metal, collection, pivot, bevel=0.003)

    # Lever handle on both faces: rose, neck, lever pointing back toward the
    # hinge the way a door lever actually hangs.
    handle_z = lo.z + 1.05
    rose_x = handle_x + inward * 0.075
    for side in (-1.0, 1.0):
        y_face = mid_y + side * face
        cylinder("door_detail_handle_rose_%s_%s" % (tag, "a" if side < 0 else "b"),
                 (rose_x, y_face + side * 0.008, handle_z), 0.034, 0.016, metal, collection, pivot,
                 rotation=(math.radians(90), 0, 0), vertices=20)
        cylinder("door_detail_handle_neck_%s_%s" % (tag, "a" if side < 0 else "b"),
                 (rose_x, y_face + side * 0.026, handle_z), 0.017, 0.030, metal, collection, pivot,
                 rotation=(math.radians(90), 0, 0), vertices=14)
        cube("door_detail_handle_lever_%s_%s" % (tag, "a" if side < 0 else "b"),
             (rose_x + inward * 0.055, y_face + side * 0.040, handle_z - 0.008),
             (0.135, 0.024, 0.026), metal, collection, pivot,
             rotation=(0, math.radians(-6.0 * inward), 0), bevel=0.008, segments=3)

    # Glazing bead around the pane, spanning the full leaf thickness so it reads
    # from both sides as one bead.
    if glass:
        glo, ghi = local_box(glass, pivot)
        bead = 0.030
        width = (ghi.x - glo.x) + bead * 2.0
        centre_x = (glo.x + ghi.x) * 0.5
        for name, position, size in (
                ("top", (centre_x, mid_y, ghi.z + bead * 0.5), (width, thickness + 0.010, bead)),
                ("bottom", (centre_x, mid_y, glo.z - bead * 0.5), (width, thickness + 0.010, bead)),
                ("left", (glo.x - bead * 0.5, mid_y, (glo.z + ghi.z) * 0.5),
                 (bead, thickness + 0.010, ghi.z - glo.z)),
                ("right", (ghi.x + bead * 0.5, mid_y, (glo.z + ghi.z) * 0.5),
                 (bead, thickness + 0.010, ghi.z - glo.z))):
            cube("door_detail_bead_%s_%s" % (name, tag), position, size, paint, collection, pivot,
                 bevel=0.005)
        panel_top = glo.z - bead - 0.06
    else:
        panel_top = hi.z - 0.9

    # Raised lower panel, and the kick plate under it.
    panel_bottom = lo.z + 0.22
    if panel_top - panel_bottom > 0.20:
        cube("door_detail_panel_%s" % tag,
             ((lo.x + hi.x) * 0.5, mid_y, (panel_top + panel_bottom) * 0.5),
             ((hi.x - lo.x) - 0.18, thickness + 0.016, panel_top - panel_bottom),
             paint, collection, pivot, bevel=0.010, segments=3)
    cube("door_detail_kickplate_%s" % tag,
         ((lo.x + hi.x) * 0.5, mid_y, lo.z + 0.105),
         ((hi.x - lo.x) - 0.10, thickness + 0.012, 0.17),
         metal, collection, pivot, bevel=0.005)


# ----------------------------------------------------------------- windows ---

def build_window(frame, pane, mullions):
    collection = frame.users_collection[0]
    tag = frame.name.replace("window_frame_", "")
    paint = frame.data.materials[0] if frame.data.materials else mat("MAT_care_old_enamel")
    metal = mat("MAT_care_worn_metal")

    lo, hi = local_box(pane if pane else frame, frame)
    depth_y = (lo.y + hi.y) * 0.5
    rail = 0.075
    # A sash inside the opening: two stiles and two rails standing proud of the
    # glass, which is what gives a window its depth from inside the ward.
    for name, position, size in (
            ("head", ((lo.x + hi.x) * 0.5, depth_y, hi.z - rail * 0.5),
             (hi.x - lo.x, 0.085, rail)),
            ("cill", ((lo.x + hi.x) * 0.5, depth_y, lo.z + rail * 0.5),
             (hi.x - lo.x, 0.085, rail)),
            ("stile_l", (lo.x + rail * 0.5, depth_y, (lo.z + hi.z) * 0.5),
             (rail, 0.085, hi.z - lo.z)),
            ("stile_r", (hi.x - rail * 0.5, depth_y, (lo.z + hi.z) * 0.5),
             (rail, 0.085, hi.z - lo.z))):
        cube("window_sash_%s_%s" % (name, tag), position, size, paint, collection, frame,
             bevel=0.006)

    # Glazing beads: a thinner lip in front of the pane, all the way round.
    bead = 0.022
    inset = rail
    for name, position, size in (
            ("top", ((lo.x + hi.x) * 0.5, depth_y - 0.030, hi.z - inset - bead * 0.5),
             (hi.x - lo.x - inset * 2.0, 0.022, bead)),
            ("bottom", ((lo.x + hi.x) * 0.5, depth_y - 0.030, lo.z + inset + bead * 0.5),
             (hi.x - lo.x - inset * 2.0, 0.022, bead)),
            ("left", (lo.x + inset + bead * 0.5, depth_y - 0.030, (lo.z + hi.z) * 0.5),
             (bead, 0.022, hi.z - lo.z - inset * 2.0)),
            ("right", (hi.x - inset - bead * 0.5, depth_y - 0.030, (lo.z + hi.z) * 0.5),
             (bead, 0.022, hi.z - lo.z - inset * 2.0))):
        cube("window_bead_%s_%s" % (name, tag), position, size, paint, collection, frame,
             bevel=0.004)

    # The catch: a base plate on the centre bar and the lever that drops into it.
    centre_x = (lo.x + hi.x) * 0.5
    latch_z = (lo.z + hi.z) * 0.5 - 0.05
    cube("window_latch_plate_%s" % tag, (centre_x, depth_y - 0.062, latch_z),
         (0.055, 0.020, 0.105), metal, collection, frame, bevel=0.004)
    cylinder("window_latch_pivot_%s" % tag, (centre_x, depth_y - 0.076, latch_z),
             0.013, 0.028, metal, collection, frame,
             rotation=(math.radians(90), 0, 0), vertices=14)
    cube("window_latch_lever_%s" % tag, (centre_x + 0.052, depth_y - 0.086, latch_z - 0.030),
         (0.115, 0.018, 0.024), metal, collection, frame,
         rotation=(0, math.radians(16.0), 0), bevel=0.006, segments=3)


# -------------------------------------------------------------------- run ----

def existing(prefix):
    return [obj for obj in bpy.data.objects if obj.name.startswith(prefix)]


# Idempotent: drop anything a previous run of this script added.
removed = 0
for obj in list(bpy.data.objects):
    if obj.name.startswith(("door_detail_", "window_sash_", "window_bead_", "window_latch_")):
        bpy.data.objects.remove(obj, do_unlink=True)
        removed += 1

doors = 0
for pivot in sorted(existing("pivot_hospital_door_"), key=lambda o: o.name):
    tag = pivot.name.replace("pivot_hospital_door_", "")
    leaf = bpy.data.objects.get("hospital_door_" + tag)
    if not leaf:
        print("DOOR_SKIPPED no leaf for", pivot.name)
        continue
    build_door(pivot, leaf, bpy.data.objects.get("door_glass_" + tag))
    doors += 1

windows = 0
for frame in sorted(existing("window_frame_"), key=lambda o: o.name):
    tag = frame.name.replace("window_frame_", "")
    build_window(frame, bpy.data.objects.get("window_night_" + tag),
                 existing("window_mullion_" + tag))
    windows += 1

for obj in bpy.context.view_layer.objects:
    obj.select_set(False)
for obj in NEW_OBJECTS:
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for modifier in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=modifier.name)
if NEW_OBJECTS:
    bpy.ops.object.shade_smooth_by_angle(angle=SMOOTH_ANGLE)

tris = sum(sum(max(len(p.vertices) - 2, 1) for p in obj.data.polygons) for obj in NEW_OBJECTS)
print("DOORS_WINDOWS_REBUILT doors=%d windows=%d removed_previous=%d new_meshes=%d new_tris=%d"
      % (doors, windows, removed, len(NEW_OBJECTS), tris))

BANNED = ("floor", "wall", "partition", "counter", "stair_step", "elevator",
          "interaction_", "corridor_n_", "corridor_s_", "bed_", "desk", "couch",
          "cabinet", "sink_unit", "toilet")
clashes = [obj.name for obj in NEW_OBJECTS
           if any(token in obj.name.lower() for token in BANNED)
           or ("door" in obj.name.lower() and "door_detail" not in obj.name.lower())]
if clashes:
    print("COLLIDER_NAME_CLASH", clashes[:8])

bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print("DOORS_WINDOWS_SAVED", bpy.data.filepath)
