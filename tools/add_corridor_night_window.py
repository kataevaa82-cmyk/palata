"""Put a night window into the blank west end wall of the corridor.

The corridor has a heavy fire door at the east end and nothing at all at the
west end - a flat painted wall the player stares at every time they turn round.
This adds a window built the same way as the medical storage one: layered
geometry behind glass (skyline, moon, bare tree), no raster textures.

Geometry notes:
  * `west_end_wall` spans x = [-20.61, -20.39]; the corridor side faces +X.
  * The builder authors the window facing local -Y (same convention as
    rebuild_clock_storage_window.py), so the root is rotated +90 deg about Z to
    turn that into world +X.
  * Materials are reused by name from the storage window so both read alike.
"""

import math

import bpy

COLLECTION_NAME = "EAST_MEDICAL_STORAGE_V1"   # where the sibling window already lives
ROOT_NAME = "corridor_night_window"
WALL_INNER_FACE_X = -20.39
# Frame front sits 0.05 m proud of the wall; frame half-depth is 0.065.
ROOT_X = WALL_INNER_FACE_X - 0.05 - 0.065
ROOT_Z = 1.62


def collection():
    existing = bpy.data.collections.get(COLLECTION_NAME)
    if existing:
        return existing
    created = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(created)
    return created


def material(name):
    found = bpy.data.materials.get(name)
    if found is None:
        raise RuntimeError("Missing material %s - run rebuild_clock_storage_window.py first" % name)
    return found


def link(obj, target_collection, parent):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    target_collection.objects.link(obj)
    obj.parent = parent
    return obj


def cube(name, location, size, mat, target_collection, parent, bevel=0.012):
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    obj = bpy.context.object
    obj.scale = tuple(value * 0.5 for value in size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.name = name
    obj.location = location
    link(obj, target_collection, parent)
    obj.data.materials.append(mat)
    if bevel:
        modifier = obj.modifiers.new("soft_edges", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
    return obj


def sphere(name, location, scale, mat, target_collection, parent, segments=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=16, location=(0, 0, 0))
    obj = bpy.context.object
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.name = name
    obj.location = location
    link(obj, target_collection, parent)
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def branch(name, points, depth, mat, target_collection, parent):
    data = bpy.data.curves.new(name + "_curve", "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = depth
    data.bevel_resolution = 2
    spline = data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, co in zip(spline.bezier_points, points):
        point.co = co
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, data)
    target_collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(mat)
    return obj


def _cut_opening():
    """Punch the glazed opening through west_end_wall.

    Without this the wall stays solid and the night backdrop is simply buried
    inside it - the frame would sit on a blank wall showing nothing. The cut
    matches the frame's inner edges (2.05 x 1.21) so the timber covers the raw
    boolean edge. main.gd still gives the wall a box collision from its AABB,
    so the opening stays solid to walk into, which is what a window should do.
    """
    wall = bpy.data.objects.get("west_end_wall")
    if wall is None:
        raise RuntimeError("west_end_wall not found")

    bpy.ops.mesh.primitive_cube_add(location=(ROOT_X, 0.0, ROOT_Z))
    cutter = bpy.context.object
    cutter.name = "corridor_window_cutter_tmp"
    cutter.scale = (0.60, 1.025, 0.605)   # X deep enough to pierce the 0.22 wall
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    modifier = wall.modifiers.new("corridor_window_opening", "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.object = cutter
    modifier.solver = "EXACT"
    bpy.context.view_layer.objects.active = wall
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def run():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    target = collection()
    old = bpy.data.objects.get(ROOT_NAME)
    if old:
        for child in list(old.children_recursive):
            bpy.data.objects.remove(child, do_unlink=True)
        bpy.data.objects.remove(old, do_unlink=True)

    night = material("MAT_storage_window_night")
    moon_mat = material("MAT_storage_window_moon")
    ink = material("MAT_clock_ink_v3")
    glass = material("MAT_storage_window_glass")
    wood = material("MAT_storage_old_wood")
    enamel = material("MAT_storage_enamel")

    root = bpy.data.objects.new(ROOT_NAME, None)
    target.objects.link(root)
    root.location = (ROOT_X, 0.0, ROOT_Z)
    root.rotation_euler = (0.0, 0.0, math.pi / 2.0)   # local -Y becomes world +X

    # Deep night behind everything. Deliberately larger than the opening cut
    # below so it covers it from behind with no sliver of outside void showing.
    cube("corridor_window_night", (0.0, 0.035, 0.0), (2.30, 0.028, 1.45), night, target, root, bevel=0.01)

    # A low skyline, slightly different from the storage room's so the two
    # windows do not look like the same view pasted twice.
    skyline = ((-0.82, 0.30, 0.50), (-0.47, 0.44, 0.34), (-0.07, 0.36, 0.62),
               (0.34, 0.50, 0.40), (0.79, 0.32, 0.54))
    for index, (x, width, height) in enumerate(skyline):
        cube("corridor_window_building_%d" % index, (x, 0.012, -0.60 + height * 0.5),
             (width, 0.018, height), ink, target, root, bevel=0.006)
    # A couple of lit windows in the far blocks.
    for x, z in ((-0.50, -0.44), (0.36, -0.36), (0.80, -0.42)):
        cube("corridor_window_far_light", (x, 0.004, z), (0.05, 0.010, 0.07),
             moon_mat, target, root, bevel=0.0)

    sphere("corridor_window_moon", (-0.62, -0.002, 0.36), (0.095, 0.010, 0.095),
           moon_mat, target, root)
    branch("corridor_window_tree", [(0.88, -0.006, -0.58), (0.84, -0.006, -0.12),
                                     (0.93, -0.006, 0.30), (0.79, -0.006, 0.55)],
           0.018, ink, target, root)
    branch("corridor_window_branch_a", [(0.86, -0.008, 0.02), (0.60, -0.008, 0.19),
                                         (0.45, -0.008, 0.40)], 0.012, ink, target, root)
    branch("corridor_window_branch_b", [(0.90, -0.008, 0.26), (1.02, -0.008, 0.46),
                                         (0.97, -0.008, 0.58)], 0.010, ink, target, root)

    cube("corridor_window_glass", (0.0, -0.025, 0.0), (2.08, 0.018, 1.23), glass, target, root, bevel=0.012)
    for x in (-1.09, 1.09):
        cube("corridor_window_frame_vertical", (x, -0.055, 0.0), (0.13, 0.13, 1.43), wood, target, root, bevel=0.022)
    for z in (-0.67, 0.67):
        cube("corridor_window_frame_horizontal", (0.0, -0.055, z), (2.31, 0.13, 0.13), wood, target, root, bevel=0.022)
    cube("corridor_window_mullion", (0.0, -0.060, 0.0), (0.075, 0.12, 1.31), wood, target, root, bevel=0.014)
    cube("corridor_window_transom", (0.0, -0.061, 0.25), (2.18, 0.12, 0.065), wood, target, root, bevel=0.012)
    # Shallower sill than the storage one: this is a through-corridor.
    cube("corridor_window_sill", (0.0, -0.16, -0.76), (2.48, 0.34, 0.09), enamel, target, root, bevel=0.022)

    for obj in [root] + list(root.children_recursive):
        obj.hide_viewport = False
        obj.hide_render = False

    _cut_opening()
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath="C:/palata/palata_zero.blend")
    print("CORRIDOR_NIGHT_WINDOW parts=", len(root.children_recursive),
          "root=", tuple(round(v, 3) for v in root.location))


run()
