# -*- coding: utf-8 -*-
"""Tighten the orderly's silhouette: shoes on the floor, legs that meet them,
cloth that is actually subdivided.

The void face, pivot names, bucket parenting and walk bones stay exactly as
rig_orderly_ghost.py left them. This only replaces the primitive shoe spheres
and cone ankles, and bakes Catmull-Clark onto the uniform / hood / apron so
the cloth reads as fabric instead of a 32-sided loft.

Saves orderly_ghost_work.blend and exports orderly_ghost_v6.glb. Does NOT
touch palata_zero.blend (that file currently holds the violent patient).

Run: blender --background orderly_ghost_work.blend --python this_file.py
"""
import math
import shutil

import bpy
import bmesh
from mathutils import Vector

BLEND_PATH = "C:/palata/orderly_ghost_work.blend"
GLB_PATH = "C:/palata/orderly_ghost_v6.glb"
GODOT_GLB = "C:/palata/project/assets/models/orderly_ghost_v6.glb"
COLLECTION_NAME = "ASSET_orderly_ghost_v5"
ROOT_NAME = "orderly_anomaly_v5"
RIG_NAME = "orderly_v6_rig"
SMOOTH_ANGLE = math.radians(40.0)


def mat(name):
    material = bpy.data.materials.get(name)
    if material is None:
        raise KeyError(name)
    return material


def collection_of(obj):
    return obj.users_collection[0]


def shade_smooth(obj):
    if obj.type != "MESH":
        return
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if hasattr(bpy.ops.object, "shade_smooth_by_angle"):
        bpy.ops.object.shade_smooth_by_angle(angle=SMOOTH_ANGLE)


def ensure_uv(obj):
    if obj.type == "MESH" and obj.data and not obj.data.uv_layers:
        mesh = obj.data
        mesh.uv_layers.new(name="UVMap")
        layer = mesh.uv_layers[0]
        for polygon in mesh.polygons:
            for loop_index in polygon.loop_indices:
                co = mesh.vertices[mesh.loops[loop_index].vertex_index].co
                layer.data[loop_index].uv = (co.x * 1.6 + 0.5, co.z * 1.6 + 0.5)


def apply_modifiers(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for modifier in list(obj.modifiers):
        try:
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        except RuntimeError:
            obj.modifiers.remove(modifier)


def make_mesh(name, verts, faces, material, collection, parent):
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata([tuple(v) for v in verts], [], faces)
    mesh.validate(clean_customdata=False)
    mesh.update()
    if material:
        mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.parent = parent
    obj.matrix_parent_inverse.identity()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    ensure_uv(obj)
    shade_smooth(obj)
    return obj


def tube(points, radii, segments=18, squash=None):
    pts = [Vector(p) for p in points]
    rings = []
    for i, p in enumerate(pts):
        if i == 0:
            direction = pts[1] - pts[0]
        elif i == len(pts) - 1:
            direction = pts[-1] - pts[-2]
        else:
            direction = pts[i + 1] - pts[i - 1]
        d = direction.normalized()
        up = Vector((0.0, 0.0, 1.0))
        if abs(d.dot(up)) > 0.94:
            up = Vector((0.0, 1.0, 0.0))
        side = d.cross(up).normalized()
        up = side.cross(d).normalized()
        r = radii[i]
        sq = 1.0 if squash is None else squash[i]
        rings.append([
            p + side * (math.cos(a) * r) + up * (math.sin(a) * r * sq)
            for a in (math.tau * k / segments for k in range(segments))
        ])
    verts = []
    faces = []
    n = segments
    for ring in rings:
        verts.extend(ring)
    for i in range(len(rings) - 1):
        a = i * n
        b = (i + 1) * n
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((a + j, a + j2, b + j2, b + j))
    faces.append(tuple(range(n - 1, -1, -1)))
    base = (len(rings) - 1) * n
    faces.append(tuple(range(base, base + n)))
    return verts, faces


def replace_leg(side):
    """Proper shin + loafer parented to the existing leg pivot.

    The pivot sits at world z 0.48. The sole must rest on z = 0, so the shoe
    lives at local z ≈ -0.48. The old sphere sat at local z -0.34 and floated.
    """
    pivot = bpy.data.objects.get("ghost_%s_leg_pivot" % side)
    if pivot is None:
        raise RuntimeError("missing leg pivot " + side)
    collection = collection_of(pivot)
    shoe_mat = mat("MAT_orderly_v5_black_shoes")
    cloth_mat = mat("MAT_orderly_v5_old_uniform")

    for child in list(pivot.children_recursive):
        lowered = child.name.lower()
        if any(token in lowered for token in (
            "ghost_%s_ankle" % side,
            "ghost_%s_shoe" % side,
            "ghost_%s_trouser" % side,
        )):
            bpy.data.objects.remove(child, do_unlink=True)

    # Trouser leg: hip of the pivot down to the ankle, slightly flared at the hem.
    shin_verts, shin_faces = tube(
        [(0.0, 0.0, 0.02), (0.0, 0.0, -0.16), (0.01, 0.0, -0.32), (0.018, 0.0, -0.42)],
        [0.072, 0.060, 0.050, 0.046],
        segments=20,
        squash=[1.05, 1.0, 0.95, 0.92],
    )
    make_mesh("ghost_%s_trouser_leg" % side, shin_verts, shin_faces, cloth_mat, collection, pivot)

    hem_verts, hem_faces = tube(
        [(0.018, 0.0, -0.405), (0.020, 0.0, -0.430)],
        [0.050, 0.052],
        segments=20,
        squash=[0.95, 0.95],
    )
    make_mesh("ghost_%s_trouser_hem" % side, hem_verts, hem_faces, cloth_mat, collection, pivot)

    # Loafer: heel under the ankle, toe pointing +X (the walk cycle's forward).
    shoe_verts, shoe_faces = tube(
        [
            (0.000, 0.0, -0.445),
            (0.030, 0.0, -0.462),
            (0.090, 0.0, -0.470),
            (0.155, 0.0, -0.472),
            (0.210, 0.0, -0.468),
        ],
        [0.048, 0.052, 0.050, 0.044, 0.032],
        segments=20,
        squash=[0.88, 0.78, 0.64, 0.55, 0.48],
    )
    make_mesh("ghost_%s_shoe" % side, shoe_verts, shoe_faces, shoe_mat, collection, pivot)

    sole_verts, sole_faces = tube(
        [
            (0.005, 0.0, -0.478),
            (0.090, 0.0, -0.484),
            (0.200, 0.0, -0.480),
        ],
        [0.046, 0.048, 0.030],
        segments=16,
        squash=[0.90, 0.62, 0.50],
    )
    make_mesh("ghost_%s_shoe_sole" % side, sole_verts, sole_faces, shoe_mat, collection, pivot)


def subdivide_cloth():
    names = (
        "ghost_fitted_uniform",
        "ghost_anatomical_hood",
        "ghost_hood_shoulder_drape",
        "ghost_l_anatomical_sleeve",
        "ghost_r_anatomical_sleeve",
        "ghost_l_anatomical_forearm",
        "ghost_r_anatomical_forearm",
    )
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj is None or obj.type != "MESH":
            continue
        if len(obj.data.vertices) > 900:
            continue
        apply_modifiers(obj)
        modifier = obj.modifiers.new("cloth_quality", "SUBSURF")
        modifier.levels = 1
        modifier.render_levels = 1
        apply_modifiers(obj)
        shade_smooth(obj)
        ensure_uv(obj)


def convert_curves():
    """Bake curve-bevelled pipes (fingers, apron loop, bucket handle) to mesh."""
    ensure_object_mode()
    for obj in list(bpy.data.objects):
        if obj.type != "CURVE":
            continue
        if "ghost_" not in obj.name:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.convert(target="MESH")
        shade_smooth(obj)
        ensure_uv(obj)


def ensure_object_mode():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


def export_glb():
    collection = bpy.data.collections.get(COLLECTION_NAME)
    rig = bpy.data.objects.get(RIG_NAME)
    root = bpy.data.objects.get(ROOT_NAME)
    if collection is None or rig is None or root is None:
        # The work file parents objects under the scene collection; fall back
        # to exporting everything under the root empty.
        export_objects = [root] + list(root.children_recursive) if root else []
        if rig and rig not in export_objects:
            export_objects.append(rig)
    else:
        export_objects = [obj for obj in list(collection.all_objects) if obj is not None]
        if root not in export_objects:
            export_objects.append(root)
        if rig not in export_objects:
            export_objects.append(rig)

    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
    for obj in export_objects:
        obj.hide_viewport = False
        obj.hide_render = False
        obj.hide_set(False)
        if obj.type in {"MESH", "CURVE", "EMPTY", "ARMATURE"}:
            obj.select_set(True)
    bpy.context.view_layer.objects.active = rig or root
    bpy.ops.export_scene.gltf(
        filepath=GLB_PATH,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
        export_animations=True,
        export_animation_mode="ACTIVE_ACTIONS",
        export_nla_strips_merged_animation_name="Orderly_Walk",
    )
    shutil.copy2(GLB_PATH, GODOT_GLB)
    print("ORDERLY_GLB_EXPORTED", GLB_PATH, "godot", GODOT_GLB)


def run():
    ensure_object_mode()
    replace_leg("l")
    replace_leg("r")
    subdivide_cloth()
    convert_curves()
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    export_glb()
    print("ORDERLY_GEOMETRY_IMPROVED")


run()
