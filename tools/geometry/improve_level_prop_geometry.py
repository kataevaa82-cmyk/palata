"""Rebuild the seven level props whose geometry read worst in the isolation
renders (build/prop_review/sheet_before_*.png).

Judged on silhouette, not on part count: props that merely looked flat at the
review angle (the bix, the operating lamp, the fridge, the extinguisher) already
carry the detail and are left alone. These seven were actually modelled as a
single scaled primitive or a stack of slabs:

    oxygen_pillow      one scaled sphere - read as an egg, not a rubber bladder
    body_bag           one scaled sphere - read as a zeppelin on the gurney
    window_latch       a solid slab sash with a pane buried inside it
    blanket_stack      three flat boards
    hospital_slippers  two loaf-shaped blobs
    muddy_trail        nine oval smudges with no foot in them
    radiator_valve     a lump on the radiator instead of a bleed tap

Rules this file obeys, all of them load-bearing (see main.gd):

* the `interaction_*` root object is never touched - its name, transform and
  care_item property are the binding contract with LEVEL_PROP_IDS;
* child mesh names avoid _needs_collision()'s substrings ("floor", "wall",
  "door", "counter", "cabinet", "bed_", "desk"), or the prop would grow an
  invisible box collider in the middle of the ward;
* the interaction volume is fitted to the mesh bounds at load, so each rebuild
  stays inside the old bounding box (the body bag especially: the gurney's
  volume cap at y=1.00 only leaves the ray the bag's top surface);
* every new mesh gets its bevels applied and smooth-by-angle shading, so it
  matches the surrounding props, which carry baked custom normals and no
  modifiers.

Run: blender --background hospital_models_work.blend --python this_file.py
"""

import math

import bpy
from mathutils import Vector

SMOOTH_ANGLE = math.radians(37.0)
NEW_OBJECTS = []


# --------------------------------------------------------------- helpers ----

def mat(name):
    material = bpy.data.materials.get(name)
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


def cube(name, location, size, material, collection, parent, rotation=(0, 0, 0), bevel=0.02, segments=2):
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


def cylinder(name, location, radius, depth, material, collection, parent, rotation=(0, 0, 0), vertices=20, scale=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                        location=location, rotation=rotation)
    obj = bpy.context.object
    if scale:
        obj.scale = scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return _register(obj, name, collection, parent)


def sphere(name, location, scale, material, collection, parent, segments=20, rings=12, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                         location=location, rotation=rotation)
    obj = bpy.context.object
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return _register(obj, name, collection, parent)


def torus(name, location, major, minor, material, collection, parent, rotation=(0, 0, 0),
          major_segments=20, minor_segments=8, scale=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, location=location,
                                     rotation=rotation, major_segments=major_segments,
                                     minor_segments=minor_segments)
    obj = bpy.context.object
    if scale:
        obj.scale = scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return _register(obj, name, collection, parent)


def clear(root):
    """Drop the old child meshes. The root empty itself survives untouched."""
    for child in reversed(list(root.children_recursive)):
        bpy.data.objects.remove(child, do_unlink=True)


def collection_of(root):
    return root.users_collection[0]


def bounds(root):
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for obj in root.children_recursive:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            lo = Vector(min(lo[i], world[i]) for i in range(3))
            hi = Vector(max(hi[i], world[i]) for i in range(3))
    return lo, hi


# ------------------------------------------------------------ the props -----

def build_oxygen_pillow(root):
    """A rubberised gas bladder: a flat welded cushion with a seam welt all the
    way round and a brass spigot, instead of one ellipsoid."""
    col = collection_of(root)
    rubber = mat("MAT_procedure_old_rubber")
    metal = mat("MAT_care_worn_metal")
    paper = mat("MAT_care_old_paper")

    # Body: a rounded slab. Heavy bevel does the pillow corners; the two soft
    # bulges are the gas actually sitting in it.
    cube("level_oxygen_bladder", (0, 0, 0), (0.60, 0.17, 0.44), rubber, col, root, bevel=0.075, segments=5)
    for side in (-1, 1):
        sphere("level_oxygen_bulge", (0.0, side * 0.055, -0.02), (0.24, 0.055, 0.17), rubber, col, root)
    # Welded seam welt: the flange that runs round the perimeter of a real one.
    cube("level_oxygen_seam", (0, 0, 0), (0.645, 0.028, 0.475), rubber, col, root, bevel=0.012)
    # Creases where the emptied bladder folds.
    for index, z in enumerate((0.12, -0.05)):
        cube("level_oxygen_crease", (-0.04 + index * 0.06, -0.088, z), (0.42, 0.020, 0.016),
             rubber, col, root, rotation=(0, math.radians(3 - index * 6), 0), bevel=0.007)
    # Spigot and hose, top right corner.
    cylinder("level_oxygen_spigot_collar", (0.245, 0.0, 0.215), 0.032, 0.030, metal, col, root, vertices=16)
    cylinder("level_oxygen_spigot", (0.245, 0.0, 0.255), 0.019, 0.075, metal, col, root, vertices=14)
    cylinder("level_oxygen_hose", (0.288, 0.0, 0.205), 0.014, 0.155, rubber, col, root,
             rotation=(0, math.radians(62), 0), vertices=12)
    cylinder("level_oxygen_hose_tip", (0.333, 0.0, 0.070), 0.014, 0.190, rubber, col, root,
             rotation=(0, math.radians(14), 0), vertices=12)
    cylinder("level_oxygen_hose_nozzle", (0.339, 0.0, -0.030), 0.017, 0.045, metal, col, root,
             rotation=(0, math.radians(6), 0), vertices=12)
    cube("level_oxygen_tag", (-0.16, -0.10, 0.10), (0.15, 0.008, 0.085), paper, col, root,
         rotation=(0, math.radians(-6), 0), bevel=0.004)


def build_body_bag(root):
    """A transport bag: a rounded rectangular envelope with a body under it,
    a zip that ends in a pull, canvas straps and two carry handles."""
    col = collection_of(root)
    rubber = mat("MAT_procedure_old_rubber")
    canvas = mat("MAT_procedure_canvas")
    metal = mat("MAT_care_worn_metal")
    paper = mat("MAT_care_old_paper")

    cube("level_bodybag_shell", (0, 0, -0.01), (1.68, 0.52, 0.20), rubber, col, root, bevel=0.085, segments=5)
    # What is inside, read through the cover: head, chest, hips, feet.
    for name, x, scale in (("head", 0.66, (0.11, 0.10, 0.075)),
                           ("chest", 0.30, (0.24, 0.17, 0.085)),
                           ("hip", -0.16, (0.20, 0.16, 0.070)),
                           ("feet", -0.70, (0.11, 0.11, 0.060))):
        sphere("level_bodybag_form_" + name, (x, 0.0, 0.065), scale, rubber, col, root)
    # Zip: two tape halves, the teeth between them, and the pull at the head end.
    for side in (-1, 1):
        cube("level_bodybag_zip_tape", (0.0, side * 0.030, 0.118), (1.60, 0.032, 0.010),
             rubber, col, root, bevel=0.003)
    cube("level_bodybag_zip", (0.0, 0.0, 0.122), (1.58, 0.022, 0.012), metal, col, root, bevel=0.004)
    cube("level_bodybag_zip_pull", (0.74, 0.0, 0.132), (0.055, 0.018, 0.010), metal, col, root, bevel=0.004)
    for x in (-0.62, 0.0, 0.62):
        cube("level_bodybag_strap", (x, 0.0, 0.02), (0.055, 0.60, 0.022), canvas, col, root, bevel=0.006)
    # Carry handles, one each side, sunk so only the loop shows.
    for side in (-1, 1):
        torus("level_bodybag_handle", (side * 0.34, 0.0, 0.055), 0.085, 0.016, canvas, col, root,
              rotation=(math.radians(90), 0, 0), scale=(1.0, 0.55, 1.0))
    cube("level_bodybag_tag", (0.74, -0.15, 0.055), (0.15, 0.008, 0.095), paper, col, root,
         rotation=(math.radians(12), 0, 0), bevel=0.004)


def build_window_latch(root):
    """The transom itself: four rails round a pane, hinges, and the catch -
    rather than a solid board with the glass buried inside it."""
    col = collection_of(root)
    enamel = mat("MAT_care_old_enamel")
    glass = mat("MAT_care_cloudy_glass")
    metal = mat("MAT_care_worn_metal")
    linen = mat("MAT_care_dirty_linen")
    putty = mat("MAT_care_old_paper")

    # Rails: named _rail_ so nothing in _needs_collision() matches.
    for z in (0.195, -0.195):
        cube("level_transom_rail_h", (0.0, 0.0, z), (0.78, 0.055, 0.050), enamel, col, root, bevel=0.008)
    for x in (-0.365, 0.365):
        cube("level_transom_rail_v", (x, 0.0, 0.0), (0.050, 0.055, 0.34), enamel, col, root, bevel=0.008)
    # Glazing putty bead and the pane it holds, set back inside the rails.
    cube("level_transom_putty", (0.0, 0.014, 0.0), (0.70, 0.022, 0.32), putty, col, root, bevel=0.005)
    cube("level_transom_pane", (0.0, 0.006, 0.0), (0.665, 0.010, 0.285), glass, col, root, bevel=0.002)
    # Two hinges on the upper rail - a форточка swings inward from the top.
    for x in (-0.25, 0.25):
        cylinder("level_transom_hinge", (x, 0.030, 0.215), 0.016, 0.075, metal, col, root,
                 rotation=(0, math.radians(90), 0), vertices=12)
        cube("level_transom_hinge_leaf", (x, 0.020, 0.200), (0.075, 0.030, 0.016), metal, col, root, bevel=0.004)
    # Latch: base plate, pivot, and the swing arm resting in the catch.
    cube("level_transom_catch_plate", (0.33, -0.045, -0.12), (0.075, 0.028, 0.10), metal, col, root, bevel=0.006)
    cylinder("level_transom_handle_pivot", (0.33, -0.062, -0.12), 0.014, 0.030, metal, col, root,
             rotation=(math.radians(90), 0, 0), vertices=12)
    cube("level_transom_handle", (0.315, -0.072, -0.155), (0.024, 0.020, 0.115), metal, col, root,
         rotation=(0, math.radians(9), 0), bevel=0.005)
    cube("level_transom_draught_tape", (0.0, -0.030, 0.215), (0.74, 0.012, 0.030), linen, col, root, bevel=0.004)


def build_blanket_stack(root):
    """Folded blankets: each one a soft slab closed by a rounded fold, stacked
    slightly out of square the way a real pile sits."""
    col = collection_of(root)
    blue = mat("MAT_patient_blanket_blue")
    grey = mat("MAT_care_dirty_linen")
    hem = mat("MAT_care_clean_linen")

    for index in range(3):
        z = index * 0.112
        yaw = math.radians((-2.5, 1.8, -1.1)[index])
        offset = (-0.012, 0.010, 0.004)[index]
        cloth = blue if index != 1 else grey
        cube("level_blanket_fold", (offset, 0.0, z), (0.72, 0.44, 0.070), cloth, col, root,
             rotation=(0, 0, yaw), bevel=0.026, segments=3)
        # The closed fold: a half-round edge along the front of the pile.
        cylinder("level_blanket_fold_edge", (offset - math.sin(yaw) * 0.22, -0.22 + math.cos(yaw) * 0.0, z),
                 0.036, 0.72, cloth, col, root,
                 rotation=(0, math.radians(90), yaw), vertices=16, scale=(1.0, 0.62, 1.0))
        # ...and the loose corner of the top layer lifting off the stack.
        if index == 2:
            cube("level_blanket_corner", (0.24, 0.16, z + 0.048), (0.26, 0.20, 0.030), cloth, col, root,
                 rotation=(math.radians(-7), math.radians(6), yaw), bevel=0.018, segments=3)
        cube("level_blanket_hem", (offset, -0.215, z - 0.030), (0.60, 0.020, 0.020), hem, col, root,
             rotation=(0, 0, yaw), bevel=0.006)


def build_hospital_slippers(root):
    """Ward slippers: a foot-shaped sole (wide toe pad, narrow waist, round
    heel) with an arched vamp over it, instead of two loaves."""
    col = collection_of(root)
    bakelite = mat("MAT_level_bakelite")
    cloth = mat("MAT_care_dirty_linen")
    dirt = mat("MAT_level_dirt")

    for index, y in enumerate((-0.10, 0.10)):
        yaw = math.radians(-7.0 if index == 0 else 5.0)
        base = Vector((0.0, y, 0.0))

        def place(local):
            """Rotate a slipper-local offset into the pair's own yaw."""
            x = local[0] * math.cos(yaw) - local[1] * math.sin(yaw)
            new_y = local[0] * math.sin(yaw) + local[1] * math.cos(yaw)
            return (base.x + x, base.y + new_y, base.z + local[2])

        # Sole: toe pad, waist, heel pad - the outline a foot actually leaves.
        cylinder("level_slipper_toe_pad", place((0.083, 0.0, 0.016)), 0.052, 0.028, bakelite, col, root,
                 vertices=20, scale=(1.0, 0.92, 1.0))
        cube("level_slipper_sole", place((0.0, 0.0, 0.016)), (0.17, 0.082, 0.028), bakelite, col, root,
             rotation=(0, 0, yaw), bevel=0.013, segments=3)
        cylinder("level_slipper_heel_pad", place((-0.086, 0.0, 0.016)), 0.045, 0.028, bakelite, col, root,
                 vertices=20, scale=(1.0, 0.88, 1.0))
        # Insole, a shade darker and set inside the sole edge.
        cube("level_slipper_insole", place((-0.005, 0.0, 0.032)), (0.20, 0.075, 0.008), cloth, col, root,
             rotation=(0, 0, yaw), bevel=0.006)
        # Vamp: an arch over the forefoot, sunk into the sole so only the band
        # above the foot opening shows.
        # Flattened so the half of the ring that is buried in the sole does not
        # reach through the floor - only the arch over the foot opening shows.
        torus("level_slipper_vamp", place((0.055, 0.0, 0.032)), 0.050, 0.016, cloth, col, root,
              rotation=(math.radians(90), 0, yaw), scale=(1.0, 0.85, 0.55))
        cube("level_slipper_vamp_lip", place((0.010, 0.0, 0.052)), (0.030, 0.086, 0.014), cloth, col, root,
             rotation=(0, math.radians(-14), yaw), bevel=0.006)
        # Heel counter, low and soft.
        cylinder("level_slipper_heel_cup", place((-0.086, 0.0, 0.040)), 0.045, 0.020, cloth, col, root,
                 vertices=18, scale=(1.0, 0.88, 1.0))

    cube("level_slipper_dirt_smear", (0.13, 0.0, 0.004), (0.17, 0.24, 0.004), dirt, col, root, bevel=0.0)


def build_muddy_trail(root):
    """Bare footprints: heel, ball and toes, alternating left and right down the
    corridor - previously two flat ovals per step, which read as smudges."""
    col = collection_of(root)
    dirt = mat("MAT_level_dirt")

    for index in range(9):
        x = -1.70 + index * 0.42
        side = -1 if index % 2 == 0 else 1
        y = side * 0.16
        # Feet toe slightly outward, and the print fades along the trail.
        yaw = math.radians(6.0 * side)
        fade = 1.0 - 0.045 * index

        def place(local):
            rx = local[0] * math.cos(yaw) - local[1] * math.sin(yaw)
            ry = local[0] * math.sin(yaw) + local[1] * math.cos(yaw)
            return (x + rx, y + ry, 0.0)

        sphere("level_dirt_patch_ball", place((0.055, 0.0, 0.0)), (0.052 * fade, 0.040 * fade, 0.004),
               dirt, col, root, segments=18, rings=8)
        sphere("level_dirt_patch_arch", place((0.0, side * 0.008, 0.0)), (0.045 * fade, 0.021 * fade, 0.003),
               dirt, col, root, segments=14, rings=6)
        sphere("level_dirt_patch_heel", place((-0.062, 0.0, 0.0)), (0.038 * fade, 0.032 * fade, 0.004),
               dirt, col, root, segments=18, rings=8)
        # Toes: the big one, then three smaller, splayed across the ball.
        for toe in range(4):
            toe_y = side * (-0.030 + toe * 0.021)
            radius = (0.017, 0.013, 0.011, 0.009)[toe] * fade
            sphere("level_dirt_patch_toe", place((0.105 - toe * 0.008, toe_y, 0.0)),
                   (radius * 1.15, radius, 0.0035), dirt, col, root, segments=12, rings=6)


def build_radiator_valve(root):
    """A Mayevsky bleed tap: hex body, knurled collar, square spindle and the
    spout it drips from - the old version was an unreadable lump."""
    col = collection_of(root)
    metal = mat("MAT_care_worn_metal")
    rust = mat("MAT_care_rust")

    # Screwed into the radiator plug, so the axis runs along +X out of the section.
    cylinder("level_radiator_bleed_plug", (0.0, 0.0, 0.0), 0.036, 0.026, rust, col, root,
             rotation=(0, math.radians(90), 0), vertices=18)
    cylinder("level_radiator_bleed_collar", (0.020, 0.0, 0.0), 0.030, 0.016, metal, col, root,
             rotation=(0, math.radians(90), 0), vertices=24)
    cylinder("level_radiator_bleed_body", (0.046, 0.0, 0.0), 0.026, 0.040, metal, col, root,
             rotation=(0, math.radians(90), 0), vertices=6)
    cylinder("level_radiator_bleed_shoulder", (0.068, 0.0, 0.0), 0.019, 0.014, metal, col, root,
             rotation=(0, math.radians(90), 0), vertices=16)
    # The square the key fits over.
    cube("level_radiator_bleed_square", (0.084, 0.0, 0.0), (0.026, 0.019, 0.019), metal, col, root,
         rotation=(math.radians(45), 0, 0), bevel=0.002)
    # Bleed spout, pointing down and forward, with the rust streak under it.
    cylinder("level_radiator_bleed_spout", (0.050, -0.026, -0.016), 0.008, 0.036, metal, col, root,
             rotation=(math.radians(58), 0, 0), vertices=12)
    cube("level_radiator_bleed_drip", (0.048, -0.034, -0.085), (0.020, 0.006, 0.150), rust, col, root,
         rotation=(math.radians(-4), 0, 0), bevel=0.004)
    torus("level_radiator_bleed_scale", (0.006, 0.0, 0.0), 0.034, 0.006, rust, col, root,
          rotation=(0, math.radians(90), 0), major_segments=18, minor_segments=6)


BUILDERS = {
    "interaction_oxygen_pillow": build_oxygen_pillow,
    "interaction_body_bag": build_body_bag,
    "interaction_window_latch": build_window_latch,
    "interaction_blanket_stack": build_blanket_stack,
    "interaction_hospital_slippers": build_hospital_slippers,
    "interaction_muddy_trail": build_muddy_trail,
    "interaction_radiator_valve": build_radiator_valve,
}

BANNED = ("floor", "wall", "door", "counter", "cabinet", "bed_", "desk")

before = {}
for name in BUILDERS:
    root = bpy.data.objects[name]
    lo, hi = bounds(root)
    before[name] = (lo.copy(), hi.copy())

for name, builder in BUILDERS.items():
    root = bpy.data.objects[name]
    clear(root)
    builder(root)

# Bevels applied and shading normalised, so the new meshes match the props
# around them (baked custom normals, no live modifiers).
for obj in bpy.context.view_layer.objects:
    obj.select_set(False)
for obj in NEW_OBJECTS:
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for modifier in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=modifier.name)
bpy.ops.object.shade_smooth_by_angle(angle=SMOOTH_ANGLE)

print("PROP_GEOMETRY_REBUILD")
for name in BUILDERS:
    root = bpy.data.objects[name]
    lo, hi = bounds(root)
    old_lo, old_hi = before[name]
    tris = sum(sum(max(len(p.vertices) - 2, 1) for p in child.data.polygons)
               for child in root.children_recursive if child.type == "MESH")
    bad = [child.name for child in root.children_recursive
           if any(token in child.name.lower() for token in BANNED)]
    print("  %-34s parts=%2d tris=%5d  size %s -> %s%s" % (
        name, len(root.children_recursive), tris,
        tuple(round(old_hi[i] - old_lo[i], 3) for i in range(3)),
        tuple(round(hi[i] - lo[i], 3) for i in range(3)),
        "  COLLIDER_NAME_CLASH=%s" % bad if bad else ""))
    print("      bbox %s -> %s" % (
        tuple(round(v, 3) for v in old_lo) + tuple(round(v, 3) for v in old_hi),
        tuple(round(v, 3) for v in lo) + tuple(round(v, 3) for v in hi)))

bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print("PROP_GEOMETRY_SAVED", bpy.data.filepath)
