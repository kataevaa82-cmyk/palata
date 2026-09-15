# -*- coding: utf-8 -*-
"""Round off the remaining crude furniture in the ward, without touching architecture.

Previous passes already bevelled level props, doors and windows. What is left
are the large raw boxes and coarse cylinders that still read as primitives
under the fluorescent lights: cabinet carcasses, desk slabs, bed-adjacent
furniture that was never on the isolation sheets.

Rules:

* never touch floors, walls, partitions, corridor panels, ceilings, skirting -
  those are architecture and their hard edges are the building;
* never touch patient / character / door_detail / window_detail meshes;
* skip anything already carrying a bevel, subsurf or more than 24 verts;
* names must not pick up _needs_collision() tokens they did not already have;
* bevels are applied and shaded, matching the rest of the baked scene.

Run: blender --background hospital_models_work.blend --python this_file.py
"""
import math

import bpy
import bmesh

BLEND_PATH = "C:/palata/hospital_models_work.blend"
SMOOTH_ANGLE = math.radians(37.0)
RAW_BOX_VERTS = 8
COARSE_RING = 12
MIN_SIZE = 0.14

SKIP_TOKENS = (
    "floor", "wall", "partition", "ceiling", "skirting", "corridor_n_", "corridor_s_",
    "opening_header", "doorframe", "hospital_door_", "door_glass", "door_detail",
    "window_", "patient", "ghost_", "violent_", "sign_text", "sign_back",
    "wear_decal", "stain", "scuff", "crack", "mount_trace", "label",
    "mattress", "pillow", "whitewash", "linoleum",
)


def should_skip(name):
    lowered = name.lower()
    return any(token in lowered for token in SKIP_TOKENS)


def is_raw_box(mesh, size):
    return (
        len(mesh.vertices) == RAW_BOX_VERTS
        and len(mesh.polygons) == 6
        and size >= MIN_SIZE
    )


def is_coarse_round(mesh, size):
    if size < MIN_SIZE or not mesh.polygons:
        return False
    ring = max(len(p.vertices) for p in mesh.polygons)
    return 4 < ring <= COARSE_RING


def shade_smooth(obj):
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if hasattr(bpy.ops.object, "shade_smooth_by_angle"):
        bpy.ops.object.shade_smooth_by_angle(angle=SMOOTH_ANGLE)


def ensure_uv(obj):
    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name="UVMap")


def bevel_mesh(obj, width, segments=2):
    mesh = obj.data
    if mesh.users > 1:
        obj.data = mesh.copy()
        mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.edges.ensure_lookup_table()
    geom = list(bm.verts) + list(bm.edges)
    try:
        bmesh.ops.bevel(
            bm,
            geom=geom,
            offset=width,
            offset_type="OFFSET",
            segments=segments,
            profile=0.5,
            affect="EDGES",
            clamp_overlap=True,
        )
    except TypeError:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=width, segments=segments)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def subdivide_simple(obj, cuts=1):
    mesh = obj.data
    if mesh.users > 1:
        obj.data = mesh.copy()
        mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=cuts, use_grid_fill=True)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def run():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    bevelled = 0
    rounded = 0
    skipped = 0
    for obj in list(bpy.data.objects):
        if obj.type != "MESH" or not obj.data.polygons:
            continue
        if should_skip(obj.name):
            skipped += 1
            continue
        if obj.modifiers:
            continue
        size = max(obj.dimensions)
        mesh = obj.data
        if is_raw_box(mesh, size):
            width = min(0.018, max(0.004, min(obj.dimensions) * 0.08))
            bevel_mesh(obj, width, segments=2)
            shade_smooth(obj)
            ensure_uv(obj)
            bevelled += 1
        elif is_coarse_round(mesh, size):
            subdivide_simple(obj, cuts=1)
            shade_smooth(obj)
            ensure_uv(obj)
            rounded += 1

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("SCENE_GEOMETRY_SOFTENED bevelled=%d rounded=%d skipped=%d" % (
        bevelled, rounded, skipped))


run()
