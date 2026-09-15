# -*- coding: utf-8 -*-
"""Upgrade the seven CC0 ward patients from faceted mannequins to smooth sleepers.

The downloaded Quaternius body is already posed supine, but it ships as one
triangulated 1.5k-tri mesh named `*_patient_head`. In-game that reads as a
potato: hard facets, marble eyes staring at the ceiling, a jagged hair cap.

This pass, per patient:

* bakes the supine transform into unique mesh data (the seven currently share
  one datablock, so a later edit would hit all of them at once);
* joins triangles into quads where the source allows, then Catmull-Clark
  subdivides (skin twice, clothes/hair once);
* splits by material into named parts so Godot's material_system can colour
  skin / gown / hair / trousers / shoes from the object *and* the material;
* replaces the open eye spheres with closed lids (these people are sedated);
* keeps the patient root, chart card and blanket contract with main.gd.

The skin mesh keeps the `_patient_head` suffix because capture_ward_patient_ingame.gd
and the fitment test look for it.

Run: blender --background hospital_models_work.blend --python this_file.py
"""
import math

import bpy
import bmesh
from mathutils import Matrix, Vector

BLEND_PATH = "C:/palata/hospital_models_work.blend"
SMOOTH_ANGLE = math.radians(42.0)

PATIENT_ROOTS = (
    "ward_1_bed_1_patient_v3",
    "ward_2_bed_1_patient_v3",
    "ward_3_bed_1_patient_v3",
    "ward_4_bed_1_patient_v3",
    "ward_5_bed_1_patient_v3",
    "ward_6_bed_1_patient_v3",
    "ward_6_bed_2_patient_v3",
)

PRESERVE = ("blanket", "chart_card", "chart_red_stripe")

# Material-name token -> object suffix. Skin keeps `_patient_head` so existing
# review/capture scripts still find a face mesh.
MATERIAL_SUFFIX = (
    ("skin", "_patient_head"),
    ("gown", "_patient_gown"),
    ("trousers", "_patient_trousers"),
    ("shoes", "_patient_shoes"),
    ("hair", "_patient_hair"),
    ("eye_white", None),   # deleted, replaced with lids
    ("eye_pupil", None),
)

SUBDIV_LEVELS = {
    "_patient_head": 1,
    "_patient_gown": 1,
    "_patient_trousers": 1,
    "_patient_shoes": 1,
    "_patient_hair": 1,
}


def ensure_object_mode():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


def shade_smooth(obj, angle=SMOOTH_ANGLE):
    mesh = obj.data
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if hasattr(bpy.ops.object, "shade_smooth_by_angle"):
        bpy.ops.object.shade_smooth_by_angle(angle=angle)
    mesh.update()


def ensure_uv(obj):
    mesh = obj.data
    if mesh.uv_layers:
        return
    mesh.uv_layers.new(name="UVMap")
    layer = mesh.uv_layers[0]
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            co = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            layer.data[loop_index].uv = (co.x * 2.4 + 0.5, co.y * 2.4 + 0.5)


def apply_modifiers(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for modifier in list(obj.modifiers):
        try:
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        except RuntimeError:
            obj.modifiers.remove(modifier)


def recalc_normals(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bm.faces and bm.calc_volume(signed=True) < 0.0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def bake_transform(obj):
    """Fold loc/rot/scale into the vertices so the object matrix is identity."""
    mesh = obj.data
    if mesh.users > 1:
        obj.data = mesh.copy()
        mesh = obj.data
    mesh.transform(obj.matrix_local)
    obj.matrix_local = Matrix.Identity(4)
    mesh.update()


def weld(obj, dist=0.0004):
    """Merge coincident verts. glTF imports often split every triangle."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=dist)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def join_triangles(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    try:
        bmesh.ops.join_triangles(
            bm,
            faces=list(bm.faces),
            angle_face_threshold=math.radians(40.0),
            angle_shape_threshold=math.radians(40.0),
        )
    except Exception:
        pass
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def subdivide(obj, levels):
    if levels <= 0:
        return
    modifier = obj.modifiers.new("quality_subdiv", "SUBSURF")
    modifier.subdivision_type = "CATMULL_CLARK"
    modifier.levels = levels
    modifier.render_levels = levels
    modifier.quality = 3
    apply_modifiers(obj)


def material_token(material):
    if material is None:
        return ""
    return material.name.lower()


def suffix_for_material(material):
    name = material_token(material)
    for token, suffix in MATERIAL_SUFFIX:
        if token in name:
            return suffix
    return "_patient_part"


def extract_material_mesh(source_mesh, material_index):
    """New mesh holding only faces of `material_index`, with compact verts."""
    used = set()
    for polygon in source_mesh.polygons:
        if polygon.material_index == material_index:
            used.update(polygon.vertices)
    if not used:
        return None
    old_to_new = {old: new for new, old in enumerate(sorted(used))}
    verts = [source_mesh.vertices[old].co.copy() for old in sorted(used)]
    faces = []
    for polygon in source_mesh.polygons:
        if polygon.material_index != material_index:
            continue
        faces.append(tuple(old_to_new[index] for index in polygon.vertices))
    mesh = bpy.data.meshes.new(source_mesh.name + "_slot_%d" % material_index)
    mesh.from_pydata(verts, [], faces)
    mesh.validate(clean_customdata=False)
    mesh.update()
    if source_mesh.materials:
        material = source_mesh.materials[material_index]
        if material:
            mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return mesh


def almond_lid(center, tangent, bitangent, normal, width, height, thickness, segments=14):
    """Closed eyelid: a flattened almond sitting on the socket."""
    verts = []
    faces = []
    rings = 4
    for ring in range(rings):
        t = ring / (rings - 1)
        ring_w = width * (0.22 + 0.78 * math.sin(math.pi * t))
        ring_h = height * math.sin(math.pi * t)
        lift = thickness * (1.0 - (2.0 * t - 1.0) ** 2)
        for i in range(segments):
            a = math.tau * i / segments
            offset = tangent * (math.cos(a) * ring_w) + bitangent * (math.sin(a) * ring_h)
            verts.append(center + offset + normal * lift)
    for ring in range(rings - 1):
        a = ring * segments
        b = (ring + 1) * segments
        for i in range(segments):
            j = (i + 1) % segments
            faces.append((a + i, a + j, b + j, b + i))
    # Caps.
    start = len(verts)
    verts.append(center + tangent * 0.0 + normal * (thickness * 0.15) - bitangent * 0.001)
    end = len(verts)
    verts.append(center + tangent * 0.0 + normal * (thickness * 0.15) + bitangent * 0.001)
    for i in range(segments):
        j = (i + 1) % segments
        faces.append((start, j, i))
        base = (rings - 1) * segments
        faces.append((end, base + i, base + j))
    return verts, faces


def eye_centers_from_source(mesh):
    """World-local centres of the two eye-white clusters, before those faces are dropped."""
    points = []
    for index, material in enumerate(mesh.materials):
        token = material_token(material)
        if "eye_white" not in token and "eye_pupil" not in token:
            continue
        for polygon in mesh.polygons:
            if polygon.material_index == index:
                points.append(polygon.center.copy())
    left = [p for p in points if p.x >= 0.0]
    right = [p for p in points if p.x < 0.0]
    centres = []
    for cluster in (left, right):
        if cluster:
            centres.append(sum(cluster, Vector((0.0, 0.0, 0.0))) / len(cluster))
    return centres


def build_closed_lids(centers, collection, parent, material):
    """Place two closed lids on the baked eye centres."""
    lids = []
    for center in centers:
        suffix = "L" if center.x >= 0.0 else "R"
        placed = Vector(center)
        placed.z += 0.004
        tangent = Vector((1.0, 0.0, 0.0))
        bitangent = Vector((0.0, 0.55, 0.35)).normalized()
        normal = tangent.cross(bitangent).normalized()
        if normal.z < 0.0:
            normal = -normal
        verts, faces = almond_lid(
            placed, tangent, bitangent, normal,
            width=0.018, height=0.007, thickness=0.0035, segments=14,
        )
        name = parent.name + "_patient_closed_eye_" + suffix
        lid_mesh = bpy.data.meshes.new(name + "_mesh")
        lid_mesh.from_pydata([tuple(v) for v in verts], [], faces)
        lid_mesh.validate(clean_customdata=False)
        lid_mesh.update()
        if material:
            lid_mesh.materials.append(material)
        obj = bpy.data.objects.new(name, lid_mesh)
        collection.objects.link(obj)
        obj.parent = parent
        obj.matrix_parent_inverse.identity()
        for polygon in lid_mesh.polygons:
            polygon.use_smooth = True
        shade_smooth(obj)
        ensure_uv(obj)
        recalc_normals(obj)
        lids.append(obj)

        lash_verts, lash_faces = almond_lid(
            placed + normal * 0.0015, tangent, bitangent, normal,
            width=0.020, height=0.0028, thickness=0.0018, segments=12,
        )
        lash_name = parent.name + "_patient_closed_lash_" + suffix
        lash_mesh = bpy.data.meshes.new(lash_name + "_mesh")
        lash_mesh.from_pydata([tuple(v) for v in lash_verts], [], lash_faces)
        lash_mesh.validate(clean_customdata=False)
        lash_mesh.update()
        hair_mat = bpy.data.materials.get("MAT_patient_hair_textured")
        if hair_mat:
            lash_mesh.materials.append(hair_mat)
        lash = bpy.data.objects.new(lash_name, lash_mesh)
        collection.objects.link(lash)
        lash.parent = parent
        lash.matrix_parent_inverse.identity()
        for polygon in lash_mesh.polygons:
            polygon.use_smooth = True
        shade_smooth(lash)
        ensure_uv(lash)
        lids.append(lash)
    return lids


def finish_part(obj, levels):
    weld(obj, 0.0005)
    join_triangles(obj)
    weld(obj, 0.0005)
    subdivide(obj, levels)
    shade_smooth(obj)
    ensure_uv(obj)
    recalc_normals(obj)


def improve_blanket(root):
    """Apply any live cloth modifiers and shade the existing fitted sheet."""
    blanket = bpy.data.objects.get(root.name + "_patient_blanket")
    if blanket is None or blanket.type != "MESH":
        return
    if blanket.modifiers:
        apply_modifiers(blanket)
    shade_smooth(blanket, math.radians(50.0))
    ensure_uv(blanket)


def delete_eye_faces(obj):
    """Drop the marble eye spheres; closed lids replace them."""
    mesh = obj.data
    drop = set()
    for index, material in enumerate(mesh.materials):
        token = material_token(material)
        if "eye_white" in token or "eye_pupil" in token:
            drop.add(index)
    if not drop:
        return
    bm = bmesh.new()
    bm.from_mesh(mesh)
    faces = [f for f in bm.faces if f.material_index in drop]
    bmesh.ops.delete(bm, geom=faces, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def improve_patient(root):
    """Keep the CC0 body as one mesh, weld, smooth, close the eyes."""
    body = bpy.data.objects.get(root.name + "_patient_head")
    if body is None or body.type != "MESH":
        raise RuntimeError("Missing CC0 body on " + root.name)
    collection = root.users_collection[0]
    bake_transform(body)
    weld(body, 0.0005)
    join_triangles(body)
    weld(body, 0.0005)
    eye_centers = eye_centers_from_source(body.data)
    delete_eye_faces(body)
    weld(body, 0.0005)
    subdivide(body, 1)
    shade_smooth(body)
    ensure_uv(body)
    recalc_normals(body)
    skin_mat = None
    for material in body.data.materials:
        if material and "skin" in material.name.lower():
            skin_mat = material
            break
    lids = build_closed_lids(eye_centers, collection, root, skin_mat)
    improve_blanket(root)
    return [body] + lids


def local_bounds(objects):
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for obj in objects:
        if obj.type != "MESH":
            continue
        for vertex in obj.data.vertices:
            p = obj.matrix_local @ vertex.co
            lo = Vector(min(lo[i], p[i]) for i in range(3))
            hi = Vector(max(hi[i], p[i]) for i in range(3))
    return lo, hi


def run():
    ensure_object_mode()
    report = []
    for root_name in PATIENT_ROOTS:
        root = bpy.data.objects.get(root_name)
        if root is None:
            report.append((root_name, "MISSING"))
            continue
        created = improve_patient(root)
        lo, hi = local_bounds(list(root.children_recursive))
        tris = sum(
            sum(max(len(p.vertices) - 2, 1) for p in obj.data.polygons)
            for obj in root.children_recursive if obj.type == "MESH"
        )
        report.append((
            root_name,
            "parts=%d tris=%d box=(%.3f,%.3f,%.3f)-(%.3f,%.3f,%.3f) names=%s" % (
                len(created), tris,
                lo.x, lo.y, lo.z, hi.x, hi.y, hi.z,
                ",".join(obj.name.replace(root_name, "") for obj in created),
            ),
        ))

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    for name, line in report:
        print("WARD_PATIENT_QUALITY", name, line)
    print("WARD_PATIENTS_IMPROVED", len(report))


run()
