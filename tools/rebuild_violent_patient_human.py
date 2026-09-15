"""Rebuild the violent patient as an anatomically proportioned, skinned humanoid.

The original asset was rigid primitives bone-parented to the rig, so limbs floated
apart and the silhouette read as a mannequin. The skeleton stays byte-identical
(the walk cycle euler keys are tuned to that rest pose); only geometry is replaced.

Head and gown are built from explicit cross-section profiles rather than sculpted
spheres - blend-sphere displacement on an ellipsoid washed out into a featureless
egg, and a swept-radius tube read as a bell dress with shoulder pads.
"""

import math

import bpy
import bmesh
from mathutils import Vector

COLLECTION_NAME = "ASSET_violent_patient_v1"
RIG_NAME = "violent_patient_rig"
ROOT_NAME = "violent_patient_v1"

TAU = math.pi * 2.0


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def sample_table(table, key):
    """Linear interpolation through a table of (key, *values) rows."""
    if key <= table[0][0]:
        return table[0][1:]
    if key >= table[-1][0]:
        return table[-1][1:]
    for i in range(len(table) - 1):
        k0, k1 = table[i][0], table[i + 1][0]
        if k0 <= key <= k1:
            f = (key - k0) / (k1 - k0)
            return tuple(lerp(a, b, f) for a, b in zip(table[i][1:], table[i + 1][1:]))
    return table[-1][1:]


# --------------------------------------------------------------------------
# materials (procedural only - this project uses no raster textures)
# --------------------------------------------------------------------------

def material(name, base, dark, roughness=0.92, metallic=0.0, emission=None,
             emission_strength=5.0, noise_scale=9.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*base, 1.0)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    noise = nodes.new("ShaderNodeTexNoise")
    ramp = nodes.new("ShaderNodeValToRGB")
    bump = nodes.new("ShaderNodeBump")
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.74
    ramp.color_ramp.elements[0].color = (*dark, 1.0)
    ramp.color_ramp.elements[0].position = 0.22
    ramp.color_ramp.elements[1].color = (*base, 1.0)
    ramp.color_ramp.elements[1].position = 0.80
    shader.inputs["Base Color"].default_value = (*base, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    if emission and "Emission Color" in shader.inputs:
        shader.inputs["Emission Color"].default_value = (*emission, 1.0)
        shader.inputs["Emission Strength"].default_value = emission_strength
    bump.inputs["Strength"].default_value = 0.12
    bump.inputs["Distance"].default_value = 0.015
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return mat


# --------------------------------------------------------------------------
# mesh helpers
# --------------------------------------------------------------------------

def frame_for(direction):
    d = Vector(direction).normalized()
    up = Vector((0.0, 0.0, 1.0))
    if abs(d.dot(up)) > 0.94:
        up = Vector((0.0, 1.0, 0.0))
    side = d.cross(up).normalized()
    return side, side.cross(d).normalized()


def tube_rings(points, radii, segments=18, squash=None):
    pts = [Vector(p) for p in points]
    rings = []
    for i, p in enumerate(pts):
        if i == 0:
            d = pts[1] - pts[0]
        elif i == len(pts) - 1:
            d = pts[-1] - pts[-2]
        else:
            d = pts[i + 1] - pts[i - 1]
        side, up = frame_for(d)
        r = radii[i]
        sq = 1.0 if squash is None else squash[i]
        rings.append([p + side * (math.cos(a) * r) + up * (math.sin(a) * r * sq)
                      for a in (TAU * k / segments for k in range(segments))])
    return rings


def sweep_closed_curve(curve, radius, segments=8):
    """Tube swept around a closed 3D curve - used for the gown neckline roll."""
    count = len(curve)
    rings = []
    for i, p in enumerate(curve):
        d = Vector(curve[(i + 1) % count]) - Vector(curve[(i - 1) % count])
        side, up = frame_for(d)
        rings.append([Vector(p) + side * (math.cos(a) * radius) + up * (math.sin(a) * radius)
                      for a in (TAU * k / segments for k in range(segments))])
    verts = []
    faces = []
    for ring in rings:
        verts.extend(ring)
    for i in range(count):
        a = i * segments
        b = ((i + 1) % count) * segments
        for j in range(segments):
            j2 = (j + 1) % segments
            faces.append((a + j, a + j2, b + j2, b + j))
    return verts, faces


def mesh_from_rings(rings, cap_start=True, cap_end=True):
    verts = []
    faces = []
    n = len(rings[0])
    for ring in rings:
        verts.extend(ring)
    for i in range(len(rings) - 1):
        a = i * n
        b = (i + 1) * n
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((a + j, a + j2, b + j2, b + j))
    if cap_start:
        faces.append(tuple(range(n - 1, -1, -1)))
    if cap_end:
        base = (len(rings) - 1) * n
        faces.append(tuple(range(base, base + n)))
    return verts, faces


def mesh_from_rings_capped_points(rings, bottom_point=None, top_point=None):
    """Loft that closes onto single apex vertices instead of n-gon caps."""
    verts = []
    faces = []
    n = len(rings[0])
    for ring in rings:
        verts.extend(ring)
    for i in range(len(rings) - 1):
        a = i * n
        b = (i + 1) * n
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((a + j, a + j2, b + j2, b + j))
    if bottom_point is not None:
        index = len(verts)
        verts.append(Vector(bottom_point))
        for j in range(n):
            faces.append((index, (j + 1) % n, j))
    if top_point is not None:
        index = len(verts)
        verts.append(Vector(top_point))
        base = (len(rings) - 1) * n
        for j in range(n):
            faces.append((index, base + j, base + (j + 1) % n))
    return verts, faces


def spherical_cap(center, radius, axis, half_angle_deg, rings=6, segments=16):
    """Cap of a sphere around `axis` - used for eyelids over the eyeballs."""
    axis = Vector(axis).normalized()
    side, up = frame_for(axis)
    limit = math.radians(half_angle_deg)
    ring_list = []
    for i in range(1, rings + 1):
        phi = limit * i / rings
        sp, cp = math.sin(phi), math.cos(phi)
        ring_list.append([Vector(center) + (axis * cp + side * (sp * math.cos(a))
                                            + up * (sp * math.sin(a))) * radius
                          for a in (TAU * k / segments for k in range(segments))])
    return mesh_from_rings_capped_points(ring_list, top_point=None,
                                         bottom_point=Vector(center) + axis * radius)


def make_object(name, verts, faces, mat, collection, smooth=True):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    mesh.validate(clean_customdata=False)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    if mat:
        mesh.materials.append(mat)
    if smooth:
        for polygon in mesh.polygons:
            polygon.use_smooth = True
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return obj


def ellipsoid_object(name, center, half, mat, collection, segments=24, rings=18):
    verts = []
    faces = []
    cx, cy, cz = center
    hx, hy, hz = half
    for i in range(1, rings):
        phi = math.pi * i / rings
        sp, cp = math.sin(phi), math.cos(phi)
        for j in range(segments):
            theta = TAU * j / segments
            verts.append((cx + hx * sp * math.cos(theta),
                          cy + hy * sp * math.sin(theta),
                          cz + hz * cp))
    top = len(verts)
    verts.append((cx, cy, cz + hz))
    bottom = len(verts)
    verts.append((cx, cy, cz - hz))
    for i in range(rings - 2):
        a = i * segments
        b = (i + 1) * segments
        for j in range(segments):
            j2 = (j + 1) % segments
            faces.append((a + j, a + j2, b + j2, b + j))
    for j in range(segments):
        j2 = (j + 1) % segments
        faces.append((top, j2, j))
        base = (rings - 2) * segments
        faces.append((bottom, base + j, base + j2))
    return make_object(name, verts, faces, mat, collection)


def add_uv(obj, scale=3.0):
    """glTF export in Blender 5 refuses meshes that carry no UV layer at all."""
    mesh = obj.data
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    layer = mesh.uv_layers[0]
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            co = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            layer.data[loop_index].uv = (co.x * scale + 0.5, co.z * scale + 0.5)


def subdivide(obj, levels=1):
    modifier = obj.modifiers.new("smooth_subdiv", "SUBSURF")
    modifier.levels = levels
    modifier.render_levels = levels
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def solidify(obj, thickness, offset=-1.0):
    modifier = obj.modifiers.new("cloth_thickness", "SOLIDIFY")
    modifier.thickness = thickness
    modifier.offset = offset
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def join_into(target, others):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in others:
        obj.select_set(True)
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.join()
    return target


# --------------------------------------------------------------------------
# skinning
# --------------------------------------------------------------------------

def segment_distance(point, head, tail):
    axis = tail - head
    length_squared = axis.length_squared
    if length_squared < 1e-9:
        return (point - head).length
    t = max(0.0, min(1.0, (point - head).dot(axis) / length_squared))
    return (point - (head + axis * t)).length


def bind(obj, rig, bone_names, power=3.4, max_bones=3):
    """Deterministic proximity weighting.

    Bone-heat (ARMATURE_AUTO) fails often enough on generated geometry that a
    predictable falloff is worth more here than its slightly nicer shoulders.
    """
    for group in list(obj.vertex_groups):
        obj.vertex_groups.remove(group)
    groups = {name: obj.vertex_groups.new(name=name) for name in bone_names}
    segments = [(name, Vector(rig.data.bones[name].head_local),
                 Vector(rig.data.bones[name].tail_local)) for name in bone_names]
    for vertex in obj.data.vertices:
        p = Vector(vertex.co)
        scored = sorted(((1.0 / max(segment_distance(p, h, t), 0.004) ** power, name)
                         for name, h, t in segments), reverse=True)[:max_bones]
        total = sum(weight for weight, _ in scored)
        for weight, name in scored:
            groups[name].add([vertex.index], weight / total, "REPLACE")
    _attach(obj, rig)


def bind_rigid(obj, rig, bone_name):
    for group in list(obj.vertex_groups):
        obj.vertex_groups.remove(group)
    group = obj.vertex_groups.new(name=bone_name)
    group.add([v.index for v in obj.data.vertices], 1.0, "REPLACE")
    _attach(obj, rig)


def _attach(obj, rig):
    obj.parent = rig
    obj.matrix_parent_inverse = rig.matrix_world.inverted()
    modifier = obj.modifiers.new("armature", "ARMATURE")
    modifier.object = rig
    modifier.use_vertex_groups = True


# --------------------------------------------------------------------------
# skeleton - must stay byte-identical to the pose the walk cycle was tuned on
# --------------------------------------------------------------------------

BONES = [
    ("root", (0, 0, 0.03), (0, 0, 0.38), None),
    ("hips", (0, 0, 0.38), (0, 0, 0.78), "root"),
    ("spine", (0, 0, 0.72), (0, 0, 1.22), "hips"),
    ("chest", (0, 0, 1.12), (0, -0.035, 1.43), "spine"),
    ("neck", (0, -0.035, 1.40), (0, -0.06, 1.56), "chest"),
    ("head", (0, -0.06, 1.54), (0, -0.09, 1.82), "neck"),
    ("upper_arm.L", (0.25, -0.02, 1.36), (0.37, -0.05, 1.08), "chest"),
    ("forearm.L", (0.37, -0.05, 1.08), (0.34, -0.14, 0.82), "upper_arm.L"),
    ("hand.L", (0.34, -0.14, 0.82), (0.32, -0.20, 0.68), "forearm.L"),
    ("upper_arm.R", (-0.25, -0.02, 1.36), (-0.36, -0.12, 1.08), "chest"),
    ("forearm.R", (-0.36, -0.12, 1.08), (-0.27, -0.28, 0.84), "upper_arm.R"),
    ("hand.R", (-0.27, -0.28, 0.84), (-0.22, -0.36, 0.69), "forearm.R"),
    ("thigh.L", (0.11, 0, 0.72), (0.12, 0.01, 0.40), "hips"),
    ("shin.L", (0.12, 0.01, 0.40), (0.11, -0.02, 0.11), "thigh.L"),
    ("foot.L", (0.11, -0.02, 0.11), (0.11, -0.23, 0.055), "shin.L"),
    ("thigh.R", (-0.11, 0, 0.72), (-0.12, -0.01, 0.40), "hips"),
    ("shin.R", (-0.12, -0.01, 0.40), (-0.11, -0.02, 0.11), "thigh.R"),
    ("foot.R", (-0.11, -0.02, 0.11), (-0.11, -0.23, 0.055), "shin.R"),
]

DEFORM_BONES = [name for name, _, _, _ in BONES if name != "root"]
TORSO_BONES = ["hips", "spine", "chest", "thigh.L", "thigh.R"]


def build_rig(collection, root):
    armature = bpy.data.armatures.new("violent_patient_skeleton")
    rig = bpy.data.objects.new(RIG_NAME, armature)
    collection.objects.link(rig)
    rig.parent = root
    rig.show_in_front = True
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for name, head, tail, parent in BONES:
        bone = armature.edit_bones.new(name)
        bone.head = head
        bone.tail = tail
        if parent:
            bone.parent = armature.edit_bones[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig


# --------------------------------------------------------------------------
# body
# --------------------------------------------------------------------------

BODY_NODES = [
    ("pelvis", (0.000, 0.000, 0.790), 0.108),
    ("waist", (0.000, 0.012, 0.985), 0.096),
    ("ribs", (0.000, 0.000, 1.095), 0.112),
    ("chest", (0.000, -0.008, 1.205), 0.138),
    ("clavicle", (0.000, -0.022, 1.345), 0.126),
    ("neck", (0.000, -0.046, 1.462), 0.072),
    ("head_base", (0.000, -0.056, 1.552), 0.062),

    ("deltoid.L", (0.145, -0.018, 1.355), 0.092),
    ("shoulder.L", (0.250, -0.020, 1.360), 0.070),
    ("upper_mid.L", (0.310, -0.035, 1.220), 0.056),
    ("elbow.L", (0.370, -0.050, 1.080), 0.048),
    ("forearm_mid.L", (0.355, -0.095, 0.950), 0.042),
    ("wrist.L", (0.340, -0.140, 0.820), 0.036),
    ("fist.L", (0.322, -0.196, 0.702), 0.052),

    ("deltoid.R", (-0.145, -0.022, 1.355), 0.092),
    ("shoulder.R", (-0.250, -0.020, 1.360), 0.070),
    ("upper_mid.R", (-0.305, -0.070, 1.220), 0.056),
    ("elbow.R", (-0.360, -0.120, 1.080), 0.048),
    ("forearm_mid.R", (-0.315, -0.200, 0.960), 0.042),
    ("wrist.R", (-0.270, -0.280, 0.840), 0.036),
    ("fist.R", (-0.224, -0.352, 0.700), 0.054),

    ("hip.L", (0.112, 0.000, 0.720), 0.098),
    ("thigh_mid.L", (0.116, 0.006, 0.560), 0.078),
    ("knee.L", (0.120, 0.010, 0.400), 0.066),
    ("shin_mid.L", (0.115, -0.005, 0.255), 0.052),
    ("ankle.L", (0.110, -0.020, 0.110), 0.044),
    ("toe.L", (0.110, -0.180, 0.062), 0.038),

    ("hip.R", (-0.112, 0.000, 0.720), 0.098),
    ("thigh_mid.R", (-0.116, -0.006, 0.560), 0.078),
    ("knee.R", (-0.120, -0.010, 0.400), 0.066),
    ("shin_mid.R", (-0.115, -0.015, 0.255), 0.052),
    ("ankle.R", (-0.110, -0.020, 0.110), 0.044),
    ("toe.R", (-0.110, -0.180, 0.062), 0.038),
]

BODY_EDGES = [
    ("pelvis", "waist"), ("waist", "ribs"), ("ribs", "chest"), ("chest", "clavicle"),
    ("clavicle", "neck"), ("neck", "head_base"),
    ("clavicle", "deltoid.L"), ("deltoid.L", "shoulder.L"),
    ("shoulder.L", "upper_mid.L"), ("upper_mid.L", "elbow.L"),
    ("elbow.L", "forearm_mid.L"), ("forearm_mid.L", "wrist.L"), ("wrist.L", "fist.L"),
    ("clavicle", "deltoid.R"), ("deltoid.R", "shoulder.R"),
    ("shoulder.R", "upper_mid.R"), ("upper_mid.R", "elbow.R"),
    ("elbow.R", "forearm_mid.R"), ("forearm_mid.R", "wrist.R"), ("wrist.R", "fist.R"),
    ("pelvis", "hip.L"), ("hip.L", "thigh_mid.L"), ("thigh_mid.L", "knee.L"),
    ("knee.L", "shin_mid.L"), ("shin_mid.L", "ankle.L"), ("ankle.L", "toe.L"),
    ("pelvis", "hip.R"), ("hip.R", "thigh_mid.R"), ("thigh_mid.R", "knee.R"),
    ("knee.R", "shin_mid.R"), ("shin_mid.R", "ankle.R"), ("ankle.R", "toe.R"),
]


def build_body(collection, skin_mat):
    mesh = bpy.data.meshes.new("violent_body_skin")
    obj = bpy.data.objects.new("violent_body_skin", mesh)
    collection.objects.link(obj)

    order = {name: index for index, (name, _, _) in enumerate(BODY_NODES)}
    bm = bmesh.new()
    verts = [bm.verts.new(position) for _, position, _ in BODY_NODES]
    bm.verts.ensure_lookup_table()
    for a, b in BODY_EDGES:
        bm.edges.new((verts[order[a]], verts[order[b]]))
    bm.to_mesh(mesh)
    bm.free()

    skin = obj.modifiers.new("skin", "SKIN")
    skin.use_smooth_shade = True
    skin.branch_smoothing = 0.35
    layer = mesh.skin_vertices[0].data
    for index, (_, _, radius) in enumerate(BODY_NODES):
        layer[index].radius = (radius, radius)
    layer[order["pelvis"]].use_root = True

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier="skin")
    subdivide(obj, 2)
    obj.data.materials.append(skin_mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def skin_envelope(name, nodes, edges, root_name, mat, collection, subdiv=1):
    """Continuous cloth via the Skin modifier - covers shoulders, unlike a spine loft."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    order = {n: i for i, (n, _, _) in enumerate(nodes)}
    bm = bmesh.new()
    verts = [bm.verts.new(position) for _, position, _ in nodes]
    bm.verts.ensure_lookup_table()
    for a, b in edges:
        bm.edges.new((verts[order[a]], verts[order[b]]))
    bm.to_mesh(mesh)
    bm.free()
    skin = obj.modifiers.new("skin", "SKIN")
    skin.use_smooth_shade = True
    skin.branch_smoothing = 0.45
    layer = mesh.skin_vertices[0].data
    for index, (_, _, radius) in enumerate(nodes):
        layer[index].radius = (radius, radius)
    layer[order[root_name]].use_root = True
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier="skin")
    subdivide(obj, subdiv)
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


# --------------------------------------------------------------------------
# head - built from explicit skull cross-sections plus analytic face features
# --------------------------------------------------------------------------

HEAD_Y = -0.055          # sagittal axis of the skull
HEAD_CHIN_Z = 1.566      # lowest ring is the under-jaw, not the chin point
HEAD_APEX_Z = 1.814

# z, half-width, front depth, back depth, squareness (<1 = boxier cross-section)
HEAD_PROFILE = [
    (1.566, 0.050, 0.038, 0.068, 0.86),
    (1.580, 0.042, 0.060, 0.063, 0.75),
    (1.596, 0.049, 0.070, 0.068, 0.70),
    (1.614, 0.060, 0.078, 0.084, 0.68),
    (1.632, 0.070, 0.082, 0.095, 0.70),
    (1.650, 0.076, 0.084, 0.102, 0.74),
    (1.668, 0.080, 0.085, 0.106, 0.78),
    (1.686, 0.083, 0.086, 0.109, 0.82),
    (1.704, 0.085, 0.087, 0.110, 0.86),
    (1.722, 0.084, 0.089, 0.110, 0.88),
    (1.740, 0.082, 0.087, 0.109, 0.92),
    (1.758, 0.078, 0.083, 0.106, 0.95),
    (1.776, 0.070, 0.076, 0.099, 0.98),
    (1.794, 0.056, 0.061, 0.080, 1.00),
    (1.808, 0.034, 0.038, 0.049, 1.00),
    (1.814, 0.010, 0.012, 0.016, 1.00),
]

NOSE_PROFILE = [
    (0.00, 0.002), (0.22, 0.009), (0.44, 0.018),
    (0.66, 0.027), (0.82, 0.032), (0.93, 0.026), (1.00, 0.004),
]
NOSE_TOP_Z = 1.748
NOSE_BASE_Z = 1.652


def face_surface_y(x, z):
    """Front surface of the finished face at (x, z) - seats brows and lips on it."""
    w, f, b, k = sample_table(HEAD_PROFILE, z)
    sn = min(1.0, (min(abs(x), w * 0.999) / w) ** (1.0 / k))
    cn = math.sqrt(max(0.0, 1.0 - sn * sn))
    y = HEAD_Y - f * (cn ** k)
    forward = (nose_push(x, z) + brow_push(x, z) + chin_push(x, z)
               + cheek_shape(x, z) + mouth_shape(x, z) - socket_pull(x, z))
    return y - forward * (cn ** 1.35)


def nose_push(x, z):
    if z > NOSE_TOP_Z or z < NOSE_BASE_Z:
        return 0.0
    t = (NOSE_TOP_Z - z) / (NOSE_TOP_Z - NOSE_BASE_Z)
    amount = sample_table(NOSE_PROFILE, t)[0]
    half = 0.0085 + 0.019 * (t ** 1.7)
    span = half * 1.85
    if abs(x) > span:
        return 0.0
    return amount * (1.0 - (abs(x) / span) ** 2) ** 1.1


def brow_push(x, z):
    dz = (z - 1.7255) / 0.017
    ax = abs(x)
    if abs(dz) >= 1.0 or ax > 0.072:
        return 0.0
    across = 1.0 if ax < 0.048 else max(0.0, 1.0 - (ax - 0.048) / 0.024)
    glabella = 0.55 + 0.45 * min(1.0, ax / 0.011)
    return 0.012 * (1.0 - dz * dz) * across * glabella


def socket_pull(x, z):
    total = 0.0
    for cx in (0.036, -0.036):
        dx = (x - cx) / 0.032
        dz = (z - 1.7065) / 0.020
        d = dx * dx + dz * dz
        if d < 1.0:
            total += 0.015 * (1.0 - d) ** 1.25
    return total


def cheek_shape(x, z):
    """Positive pushes the face forward, negative hollows it out."""
    total = 0.0
    for cx in (0.059, -0.059):
        dx = (x - cx) / 0.036
        dz = (z - 1.678) / 0.026
        d = dx * dx + dz * dz
        if d < 1.0:
            total += 0.009 * (1.0 - d)
    for cx in (0.055, -0.055):
        dx = (x - cx) / 0.034
        dz = (z - 1.642) / 0.026
        d = dx * dx + dz * dz
        if d < 1.0:
            total -= 0.013 * (1.0 - d)
    return total


def mouth_shape(x, z):
    if abs(x) > 0.036:
        return 0.0
    across = (1.0 - (abs(x) / 0.036) ** 2)
    total = 0.0
    dz = (z - 1.6325) / 0.007
    if abs(dz) < 1.0:
        total -= 0.008 * (1.0 - dz * dz) * across
    dz = (z - 1.6425) / 0.009
    if abs(dz) < 1.0:
        total += 0.006 * (1.0 - dz * dz) * across
    dz = (z - 1.6215) / 0.009
    if abs(dz) < 1.0:
        total += 0.005 * (1.0 - dz * dz) * across
    if abs(x) < 0.010 and 1.650 < z < 1.664:
        total -= 0.004 * (1.0 - (abs(x) / 0.010) ** 2)
    return total


def chin_push(x, z):
    dz = (z - 1.6005) / 0.022
    ax = abs(x)
    if abs(dz) >= 1.0 or ax > 0.032:
        return 0.0
    return 0.014 * (1.0 - dz * dz) * (1.0 - (ax / 0.032) ** 2)


def lateral_shift(x, z):
    """Sideways shaping: jaw corners out, temples in, nostril wings out."""
    total = 0.0
    dz = (z - 1.6225) / 0.026
    if abs(dz) < 1.0:
        total += 0.006 * (1.0 - dz * dz)
    dz = (z - 1.7525) / 0.028
    if abs(dz) < 1.0:
        total -= 0.010 * (1.0 - dz * dz)
    if 1.654 < z < 1.676 and 0.010 < abs(x) < 0.032:
        total += 0.006
    return total


def head_ring(z, segments):
    w, f, b, k = sample_table(HEAD_PROFILE, z)
    points = []
    for j in range(segments):
        theta = TAU * j / segments          # 0 points at the face (-Y)
        s, c = math.sin(theta), math.cos(theta)
        sx = math.copysign(abs(s) ** k, s) if s else 0.0
        cx = math.copysign(abs(c) ** k, c) if c else 0.0
        x = w * sx
        y = HEAD_Y - (f if c > 0 else b) * cx
        front = max(0.0, c) ** 1.35
        side = abs(s) ** 1.3

        forward = (nose_push(x, z) + brow_push(x, z) + chin_push(x, z)
                   + cheek_shape(x, z) + mouth_shape(x, z) - socket_pull(x, z))
        y -= forward * front
        if x:
            x += math.copysign(lateral_shift(x, z), x) * side
        points.append(Vector((x, y, z)))
    return points


def build_head(collection, skin_mat):
    segments = 48
    levels = 36
    rings = []
    for i in range(levels):
        t = i / (levels - 1)
        z = lerp(HEAD_CHIN_Z, HEAD_APEX_Z - 0.004, smoothstep(t) * 0.5 + t * 0.5)
        rings.append(head_ring(z, segments))
    verts, faces = mesh_from_rings_capped_points(
        rings,
        bottom_point=(0.0, HEAD_Y + 0.038, 1.558),
        top_point=(0.0, HEAD_Y + 0.004, HEAD_APEX_Z),
    )
    head = make_object("violent_head_skin", verts, faces, skin_mat, collection)

    ears = []
    for side in (1.0, -1.0):
        points = [
            (side * 0.068, HEAD_Y + 0.022, 1.698),
            (side * 0.079, HEAD_Y + 0.018, 1.700),
            (side * 0.082, HEAD_Y + 0.012, 1.688),
            (side * 0.080, HEAD_Y + 0.008, 1.673),
            (side * 0.074, HEAD_Y + 0.006, 1.662),
        ]
        radii = [0.019, 0.021, 0.020, 0.016, 0.010]
        squash = [0.30, 0.28, 0.30, 0.34, 0.42]
        ring_set = tube_rings(points, radii, segments=12, squash=squash)
        v, f = mesh_from_rings(ring_set)
        ears.append(make_object("violent_ear_%s" % ("L" if side > 0 else "R"),
                                v, f, skin_mat, collection))

    head = join_into(head, ears)
    head.name = "violent_head_skin"
    subdivide(head, 1)
    for polygon in head.data.polygons:
        polygon.use_smooth = True
    return head


def hairline_z(theta):
    """High, receding and ragged at the front; drops behind the ears at the back."""
    front = max(0.0, math.cos(theta))
    side = abs(math.sin(theta))
    base = 1.752 - 0.070 * (1.0 - front ** 0.7) + 0.055 * side ** 3
    return base + 0.006 * math.sin(theta * 3.0 + 0.4)


def skull_point(theta, z, swell=0.0):
    w, f, b, k = sample_table(HEAD_PROFILE, z)
    s, c = math.sin(theta), math.cos(theta)
    sx = math.copysign(abs(s) ** k, s) if s else 0.0
    cx = math.copysign(abs(c) ** k, c) if c else 0.0
    return Vector(((w + swell) * sx, HEAD_Y - ((f if c > 0 else b) + swell) * cx, z))


def build_hair(collection, hair_mat):
    segments = 40
    levels = 12
    rings = []
    for i in range(levels):
        t = smoothstep(i / (levels - 1)) * 0.86 + (i / (levels - 1)) * 0.14
        ring = []
        for j in range(segments):
            theta = TAU * j / segments
            z = lerp(hairline_z(theta), HEAD_APEX_Z - 0.006, t)
            clump = (0.006 + 0.0060 * math.sin(theta * 3.0 + 0.5) * math.sin(1.2 + t * 3.0)
                     + 0.0040 * math.sin(theta * 5.0 - 0.8) * (0.4 + 0.6 * t))
            ring.append(skull_point(theta, z, clump))
        rings.append(ring)
    verts, faces = mesh_from_rings_capped_points(
        rings, top_point=(0.0, HEAD_Y + 0.004, HEAD_APEX_Z + 0.003))
    scalp = make_object("violent_hair_scalp", verts, faces, hair_mat, collection)
    solidify(scalp, 0.009, offset=0.0)

    # Matted clumps lie back across the skull - never over the eyes.
    strands = []
    layout = (
        ("a", 2.62, 1.744, 0.052),
        ("b", 3.14, 1.736, 0.062),
        ("c", 3.68, 1.746, 0.050),
    )
    for suffix, theta0, z0, drop in layout:
        points = []
        radii = []
        for k in range(6):
            t = k / 5.0
            theta = theta0 + 0.34 * t
            z = z0 - drop * t
            points.append(skull_point(theta, z, 0.012 + 0.004 * t))
            radii.append(0.012 - 0.005 * t)
        v, f2 = mesh_from_rings(tube_rings(points, radii, segments=8, squash=[0.42] * 6))
        strands.append(make_object("violent_hair_strand_%s" % suffix, v, f2,
                                   hair_mat, collection))
    return [scalp] + strands


def build_face_details(collection, materials):
    parts = []
    # Eyeball sits flush in the socket with a lid over it, so the glow reads as an
    # eye rather than a dot painted on the cheek.
    for side, suffix in ((1.0, "L"), (-1.0, "R")):
        x = side * 0.036
        z = 1.7065
        radius = 0.0155
        centre = Vector((x, face_surface_y(x, z) + 0.0100, z))
        parts.append(ellipsoid_object("violent_eye_%s" % suffix, centre,
                                      (radius, radius, radius * 0.94),
                                      materials["eye"], collection,
                                      segments=16, rings=12))
        axis = Vector((side * 0.16, -0.34, 0.93)).normalized()
        verts, faces = spherical_cap(centre, radius * 1.13, axis, 62.0)
        lid = make_object("violent_socket_lid_%s" % suffix, verts, faces,
                          materials["skin"], collection)
        solidify(lid, 0.0022, offset=1.0)
        parts.append(lid)

    for side, name in ((1.0, "violent_brow_L"), (-1.0, "violent_brow_R")):
        points = []
        radii = []
        for k in range(7):
            t = k / 6.0
            x = side * (0.011 + 0.050 * t)
            z = 1.7285 + 0.004 * math.sin(math.pi * t) - 0.009 * t * t
            points.append((x, face_surface_y(x, z) - 0.0015, z))
            radii.append(0.0050 - 0.0020 * t)
        v, fc = mesh_from_rings(tube_rings(points, radii, segments=8,
                                           squash=[0.50] * 7))
        parts.append(make_object(name, v, fc, materials["hair"], collection))

    points = []
    radii = []
    for k in range(9):
        t = k / 8.0
        x = -0.030 + 0.060 * t
        z = 1.6325 - 0.004 * math.sin(math.pi * t)
        points.append((x, face_surface_y(x, z) + 0.0016, z))
        radii.append(0.0032 + 0.0012 * math.sin(math.pi * t))
    v, fc = mesh_from_rings(tube_rings(points, radii, segments=8, squash=[0.58] * 9))
    parts.append(make_object("violent_mouth_line", v, fc, materials["hair"], collection))
    return parts


# --------------------------------------------------------------------------
# gown - a straight institutional shift, not a fitted dress
# --------------------------------------------------------------------------

# z, radius, front-back squash. The squash must never pull the shell inside the
# body: the skin-modifier torso is circular at radius 0.131, so radius * squash
# has to stay clear of that or the chest pokes through the cloth.
GOWN_PROFILE = [
    (1.404, 0.174, 0.90),
    (1.340, 0.180, 0.90),
    (1.260, 0.181, 0.90),
    (1.160, 0.178, 0.91),
    (1.060, 0.176, 0.92),
    (0.960, 0.176, 0.93),
    (0.860, 0.179, 0.94),
    (0.760, 0.185, 0.95),
    (0.660, 0.192, 0.96),
    (0.560, 0.199, 0.97),
    (0.500, 0.203, 0.98),
]

GOWN_AXIS = [(1.404, 0.0, -0.028), (1.100, 0.0, -0.004), (0.500, 0.0, 0.012)]


def gown_top(theta):
    """Crew neck that meets the throat, then flares onto the deltoids.

    A low wide hole left the head floating and the chest bare. Front stays
    high and tight; sides drop and widen so the sleeve can start inside the
    gown instead of next to a keyhole.
    """
    c = math.cos(theta)
    s = abs(math.sin(theta))
    z = 1.438 + 0.022 * max(0.0, -c) - 0.055 * s ** 1.55
    radius = 0.086 + 0.102 * s ** 0.80
    return z, radius


def gown_hem_z(theta):
    jag = (0.5 + 0.5 * math.sin(theta * 7.3 + 0.9)) * (0.6 + 0.4 * math.sin(theta * 3.1))
    return 0.500 + 0.066 * jag


def gown_fold(theta, z):
    return (1.0 + 0.028 * math.sin(theta * 5.0 + 0.6)
            + 0.016 * math.sin(theta * 9.0 - 1.2)
            + 0.011 * math.sin(theta * 3.0 + z * 6.0))


def gown_point(theta, z, radius_override=None):
    radius, squash = sample_table(GOWN_PROFILE, z)
    if radius_override is not None:
        radius = radius_override
    axis_y = sample_table(GOWN_AXIS, z)[0]
    radius *= gown_fold(theta, z)
    return Vector((radius * math.sin(theta),
                   axis_y + radius * squash * math.cos(theta),
                   z))


SHIRT_NODES = [
    ("hem", (0.000, 0.012, 0.530), 0.178),
    ("seat", (0.000, 0.008, 0.680), 0.158),
    ("waist", (0.000, 0.012, 0.900), 0.138),
    ("ribs", (0.000, 0.000, 1.080), 0.152),
    ("chest", (0.000, -0.008, 1.220), 0.170),
    ("yoke", (0.000, -0.020, 1.338), 0.168),
    ("collar", (0.000, -0.040, 1.448), 0.080),
    ("cap.L", (0.168, -0.018, 1.342), 0.108),
    ("sleeve.L", (0.258, -0.022, 1.338), 0.092),
    ("cuff.L", (0.348, -0.048, 1.145), 0.080),
    ("cap.R", (-0.168, -0.022, 1.342), 0.108),
    ("sleeve.R", (-0.258, -0.028, 1.338), 0.092),
    ("cuff.R", (-0.348, -0.110, 1.145), 0.080),
]
SHIRT_EDGES = [
    ("hem", "seat"), ("seat", "waist"), ("waist", "ribs"),
    ("ribs", "chest"), ("chest", "yoke"), ("yoke", "collar"),
    ("yoke", "cap.L"), ("cap.L", "sleeve.L"), ("sleeve.L", "cuff.L"),
    ("yoke", "cap.R"), ("cap.R", "sleeve.R"), ("sleeve.R", "cuff.R"),
]
PANT_NODES = [
    ("crotch", (0.000, 0.000, 0.800), 0.122),
    ("hip.L", (0.110, 0.000, 0.720), 0.112),
    ("thigh.L", (0.116, 0.006, 0.540), 0.098),
    ("knee.L", (0.120, 0.010, 0.400), 0.084),
    ("calf.L", (0.115, -0.006, 0.240), 0.072),
    ("hem.L", (0.110, -0.018, 0.128), 0.064),
    ("hip.R", (-0.110, 0.000, 0.720), 0.112),
    ("thigh.R", (-0.116, -0.006, 0.540), 0.098),
    ("knee.R", (-0.120, -0.010, 0.400), 0.084),
    ("calf.R", (-0.115, -0.016, 0.240), 0.072),
    ("hem.R", (-0.110, -0.018, 0.128), 0.064),
]
PANT_EDGES = [
    ("crotch", "hip.L"), ("hip.L", "thigh.L"), ("thigh.L", "knee.L"),
    ("knee.L", "calf.L"), ("calf.L", "hem.L"),
    ("crotch", "hip.R"), ("hip.R", "thigh.R"), ("thigh.R", "knee.R"),
    ("knee.R", "calf.R"), ("calf.R", "hem.R"),
]


def build_clothes(collection, gown_mat):
    """A full hospital outfit: short-sleeve shirt that covers the shoulders,
    loose trousers, a waist tie. Replaces the old spine-loft gown that left
    the chest and deltoids bare.
    """
    shirt = skin_envelope("violent_gown_shirt", SHIRT_NODES, SHIRT_EDGES,
                          "hem", gown_mat, collection, subdiv=1)
    pants = skin_envelope("violent_fitted_pants", PANT_NODES, PANT_EDGES,
                          "crotch", gown_mat, collection, subdiv=1)
    # Finished round neck - a cloth roll at the throat, not a chimney.
    collar_rings = tube_rings(
        [(0.0, -0.038, 1.430), (0.0, -0.042, 1.458), (0.0, -0.046, 1.478)],
        [0.086, 0.080, 0.074], segments=20, squash=[0.95, 0.98, 1.0],
    )
    cverts, cfaces = mesh_from_rings(collar_rings, cap_start=False, cap_end=False)
    collar = make_object("violent_gown_collar", cverts, cfaces, gown_mat, collection)
    solidify(collar, 0.010, offset=0.0)
    # A flat sash: reuse a thin torus.
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.142, minor_radius=0.016, major_segments=28, minor_segments=8,
        location=(0.0, 0.010, 0.900), rotation=(math.radians(8.0), 0.0, 0.0),
    )
    belt = bpy.context.object
    belt.name = "violent_gown_belt"
    for owner in list(belt.users_collection):
        owner.objects.unlink(belt)
    collection.objects.link(belt)
    belt.data.materials.append(gown_mat)
    for polygon in belt.data.polygons:
        polygon.use_smooth = True
    return [shirt, pants, collar, belt]


def build_gown_legacy_unused(collection, gown_mat):
    parts = []
    segments = 36
    levels = 26
    rings = []
    neckline = []
    for i in range(levels):
        t = i / (levels - 1)
        ring = []
        for j in range(segments):
            theta = TAU * j / segments
            top_z, top_radius = gown_top(theta)
            hem = gown_hem_z(theta)
            # Cloth over the shoulders descends far more slowly than cloth hanging
            # off the chest, which is what turns the yoke into a shoulder rather
            # than a horizontal ledge.
            side = abs(math.sin(theta))
            z = lerp(top_z, hem, t ** (1.0 + 1.15 * side ** 2))
            blend = smoothstep(min(1.0, (top_z - z) / 0.075))
            body_radius = sample_table(GOWN_PROFILE, z)[0]
            point = gown_point(theta, z, lerp(top_radius, body_radius, blend))
            ring.append(point)
            if i == 0:
                neckline.append(point)
        rings.append(ring)
    verts, faces = mesh_from_rings(rings, cap_start=False, cap_end=False)
    gown = make_object("violent_gown_torso", verts, faces, gown_mat, collection)
    solidify(gown, 0.012, offset=-1.0)
    subdivide(gown, 1)
    parts.append(gown)

    verts, faces = sweep_closed_curve(neckline, 0.024, segments=10)
    parts.append(make_object("violent_gown_collar", verts, faces, gown_mat, collection))

    # Stub collar up to the jaw so the head is not a floating egg on a stick.
    turtle = []
    for i in range(5):
        t = i / 4.0
        z = lerp(1.430, 1.545, t)
        radius = lerp(0.092, 0.068, t)
        ring = []
        for j in range(segments):
            theta = TAU * j / segments
            squash = lerp(0.92, 1.0, t)
            ring.append(Vector((
                radius * math.sin(theta),
                -0.040 + radius * squash * math.cos(theta),
                z,
            )))
        turtle.append(ring)
    tverts, tfaces = mesh_from_rings(turtle, cap_start=False, cap_end=False)
    turtle_obj = make_object("violent_gown_turtleneck", tverts, tfaces, gown_mat, collection)
    solidify(turtle_obj, 0.010, offset=0.0)
    parts.append(turtle_obj)

    hem_rings = []
    for i in range(3):
        t = i / 2.0
        ring = []
        for j in range(segments):
            theta = TAU * j / segments
            hem = gown_hem_z(theta)
            tear = 0.022 * (0.3 + 0.7 * math.sin(theta * 5.7) ** 2)
            z = max(0.440, lerp(hem + 0.050, hem - tear, t))
            ring.append(gown_point(theta, z))
        hem_rings.append(ring)
    verts, faces = mesh_from_rings(hem_rings, cap_start=False, cap_end=False)
    hem = make_object("violent_gown_hem_torn", verts, faces, gown_mat, collection)
    solidify(hem, 0.009, offset=0.0)
    parts.append(hem)

    sleeves = (
        ("violent_gown_sleeve_L", 1.0, (0.250, -0.020, 1.360), (0.370, -0.050, 1.080)),
        ("violent_gown_sleeve_R", -1.0, (-0.250, -0.020, 1.360), (-0.360, -0.120, 1.080)),
    )
    for name, side, shoulder, elbow in sleeves:
        origin = Vector(shoulder)
        axis = Vector(elbow) - origin
        # First ring sits on the gown surface at the shoulder, not in the hole
        # beside it. theta = ±90° is the side seam.
        armhole_theta = side * math.pi * 0.50
        armhole = gown_point(armhole_theta, 1.355, 0.188)
        points = [armhole] + [origin + axis * t for t in (0.08, 0.28, 0.50, 0.72)]
        radii = [0.108, 0.096, 0.086, 0.078, 0.074]
        ring_set = tube_rings(points, radii, segments=22,
                              squash=[1.12, 1.00, 0.96, 0.95, 0.95])
        for index, ring in enumerate(ring_set):
            centre = points[index]
            for j, point in enumerate(ring):
                fold = 1.0 + 0.028 * math.sin(j * 1.9 + index * 0.8)
                ring[j] = centre + (point - centre) * fold
        verts, faces = mesh_from_rings(ring_set, cap_start=False, cap_end=False)
        sleeve = make_object(name, verts, faces, gown_mat, collection)
        solidify(sleeve, 0.012, offset=0.0)
        subdivide(sleeve, 1)
        parts.append(sleeve)
    return parts


# --------------------------------------------------------------------------
# dressings, marks, footwear, weapon
# --------------------------------------------------------------------------

def build_wraps_and_marks(collection, materials):
    parts = []
    wraps = (
        ("violent_bandage_forearm_L",
         [(0.366, -0.058, 1.062), (0.352, -0.100, 0.940), (0.340, -0.140, 0.822)],
         [0.052, 0.046, 0.041], 0.007),
        ("violent_bandage_hand_L",
         [(0.336, -0.152, 0.796), (0.328, -0.176, 0.748)],
         [0.045, 0.050], 0.006),
        ("violent_bandage_ankle_R",
         [(-0.110, -0.014, 0.168), (-0.110, -0.020, 0.112)],
         [0.049, 0.049], 0.006),
    )
    for name, points, radii, thickness in wraps:
        verts, faces = mesh_from_rings(tube_rings(points, radii, segments=18),
                                       cap_start=False, cap_end=False)
        wrap = make_object(name, verts, faces, materials["bandage"], collection)
        solidify(wrap, thickness, offset=0.0)
        parts.append(wrap)

    # Half-buried so only a discoloured patch of skin shows through.
    marks = (
        ("violent_bruise_temple", (0.300, -0.036, 1.230), (0.030, 0.028, 0.032)),
        ("violent_bruise_cheek", (0.112, -0.052, 0.300), (0.030, 0.028, 0.034)),
        ("violent_bruise_shoulder", (-0.246, -0.052, 1.346), (0.034, 0.030, 0.028)),
        ("violent_bruise_forearm", (-0.318, -0.196, 0.950), (0.026, 0.026, 0.028)),
    )
    for name, center, half in marks:
        parts.append(ellipsoid_object(name, center, half, materials["bruise"],
                                      collection, segments=14, rings=10))
    return parts


def build_hands(collection, skin_mat):
    """Mittens with a thumb, bound rigidly to the hand bones.

    The skin-modifier fists are spherical blobs; these sit over them and give
    the silhouette actual palms instead of drumsticks.
    """
    parts = []
    specs = (
        ("violent_hand_L", 1.0, Vector((0.328, -0.168, 0.760)), Vector((0.318, -0.210, 0.668)),
         Vector((0.305, -0.168, 0.700))),
        ("violent_hand_R", -1.0, Vector((-0.255, -0.305, 0.790)), Vector((-0.218, -0.365, 0.668)),
         Vector((-0.200, -0.318, 0.710))),
    )
    for name, side, wrist, knuckles, thumb_tip in specs:
        palm_dir = knuckles - wrist
        points = [wrist, wrist + palm_dir * 0.35, knuckles]
        radii = [0.038, 0.046, 0.042]
        rings = tube_rings(points, radii, segments=16, squash=[0.78, 0.70, 0.62])
        verts, faces = mesh_from_rings(rings)
        palm = make_object(name + "_palm", verts, faces, skin_mat, collection)
        thumb_points = [wrist + Vector((side * 0.012, -0.008, -0.010)), thumb_tip]
        thumb_rings = tube_rings(thumb_points, [0.016, 0.012], segments=10, squash=[0.85, 0.80])
        tverts, tfaces = mesh_from_rings(thumb_rings)
        thumb = make_object(name + "_thumb", tverts, tfaces, skin_mat, collection)
        parts.extend([palm, thumb])
    return parts


def build_shoes(collection, shoe_mat):
    parts = []
    for side, name in ((1.0, "violent_shoe_L"), (-1.0, "violent_shoe_R")):
        points = [
            (side * 0.110, 0.006, 0.104),
            (side * 0.110, -0.052, 0.062),
            (side * 0.110, -0.140, 0.044),
            (side * 0.110, -0.214, 0.040),
        ]
        rings = tube_rings(points, [0.052, 0.058, 0.054, 0.040], segments=18,
                           squash=[0.86, 0.72, 0.60, 0.54])
        verts, faces = mesh_from_rings(rings)
        shoe = make_object(name, verts, faces, shoe_mat, collection)
        subdivide(shoe, 1)
        parts.append(shoe)
    return parts


def build_weapon(collection, materials):
    rings = tube_rings(
        [(-0.230, -0.372, 0.716), (-0.196, -0.428, 1.070), (-0.162, -0.482, 1.424)],
        [0.019, 0.018, 0.017], segments=12)
    verts, faces = mesh_from_rings(rings)
    bar = make_object("violent_bed_rail", verts, faces, materials["metal"], collection)
    rust = ellipsoid_object("violent_rail_rust", (-0.182, -0.450, 1.205),
                            (0.023, 0.021, 0.072), materials["rust"], collection,
                            segments=12, rings=10)
    return [bar, rust]


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def run():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    old = bpy.data.collections.get(COLLECTION_NAME)
    if old:
        for obj in list(old.all_objects):
            if obj is not None:
                bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old)
    # palata_zero.blend currently stores the patient in the scene Collection,
    # not ASSET_violent_patient_v1. Drop every leftover violent_* object so
    # the new meshes do not come back as .001 and miss the bind map.
    for obj in list(bpy.data.objects):
        lowered = obj.name.lower()
        if (
            lowered.startswith("violent_")
            or obj.name in {ROOT_NAME, RIG_NAME}
            or obj.type == "ARMATURE" and "violent" in lowered
        ):
            bpy.data.objects.remove(obj, do_unlink=True)
    collection = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(collection)

    materials = {
        "gown": material("MAT_violent_patient_gown", (0.16, 0.29, 0.265), (0.025, 0.055, 0.045), 0.98),
        # Sick, desaturated skin reads as human under the green ward lighting;
        # the old brown ramp made the face look like a wooden puppet.
        "skin": material("MAT_violent_patient_skin", (0.62, 0.49, 0.40), (0.22, 0.12, 0.095), 0.94, noise_scale=16.0),
        "bruise": material("MAT_violent_patient_bruise", (0.095, 0.042, 0.048), (0.022, 0.008, 0.012), 0.98),
        "bandage": material("MAT_violent_patient_bandage", (0.58, 0.55, 0.40), (0.18, 0.14, 0.08), 0.99),
        "hair": material("MAT_violent_patient_hair", (0.035, 0.025, 0.015), (0.003, 0.002, 0.001), 0.98),
        # Keep the stare unsettling, but avoid the cheap glowing-red monster look.
        "eye": material("MAT_violent_patient_eye", (0.12, 0.075, 0.035), (0.012, 0.006, 0.003), 0.40),
        "shoe": material("MAT_violent_patient_shoe", (0.025, 0.028, 0.022), (0.002, 0.003, 0.002), 0.92),
        "metal": material("MAT_violent_patient_metal", (0.30, 0.31, 0.27), (0.06, 0.055, 0.04), 0.72, 0.52),
        "rust": material("MAT_violent_patient_rust", (0.34, 0.065, 0.012), (0.055, 0.006, 0.001), 1.0, 0.10),
    }

    root = bpy.data.objects.new(ROOT_NAME, None)
    collection.objects.link(root)
    root["asset_type"] = "rigged_violent_patient"
    root["version"] = 3

    rig = build_rig(collection, root)

    body = build_body(collection, materials["skin"])
    head = build_head(collection, materials["skin"])
    hair = build_hair(collection, materials["hair"])
    face = build_face_details(collection, materials)
    clothes = build_clothes(collection, materials["gown"])
    wraps = build_wraps_and_marks(collection, materials)
    hands = build_hands(collection, materials["skin"])
    shoes = build_shoes(collection, materials["shoe"])
    weapon = build_weapon(collection, materials)

    bind(body, rig, DEFORM_BONES)
    for obj in [head] + hair + face:
        bind_rigid(obj, rig, "head")
    for obj in clothes:
        if "pants" in obj.name:
            bind(obj, rig, ["hips", "thigh.L", "thigh.R", "shin.L", "shin.R"])
        elif "collar" in obj.name:
            bind(obj, rig, ["chest", "neck"])
        elif "belt" in obj.name:
            bind_rigid(obj, rig, "hips")
        else:
            bind(obj, rig, ["hips", "spine", "chest", "neck",
                            "upper_arm.L", "forearm.L", "upper_arm.R", "forearm.R"])

    rigid_map = {
        "violent_bandage_forearm_L": "forearm.L",
        "violent_bandage_hand_L": "hand.L",
        "violent_bandage_ankle_R": "shin.R",
        "violent_bruise_temple": "upper_arm.L",
        "violent_bruise_cheek": "shin.L",
        "violent_bruise_shoulder": "upper_arm.R",
        "violent_bruise_forearm": "forearm.R",
        "violent_shoe_L": "foot.L",
        "violent_shoe_R": "foot.R",
        "violent_bed_rail": "hand.R",
        "violent_rail_rust": "hand.R",
        "violent_hand_L_palm": "hand.L",
        "violent_hand_L_thumb": "hand.L",
        "violent_hand_R_palm": "hand.R",
        "violent_hand_R_thumb": "hand.R",
    }
    for obj in wraps + shoes + weapon + hands:
        bind_rigid(obj, rig, rigid_map[obj.name])

    meshes = [obj for obj in collection.all_objects if obj.type == "MESH"]
    for obj in meshes:
        add_uv(obj)
        obj.data.update()

    bpy.context.scene.frame_set(1)
    print("VIOLENT_REBUILD meshes=%d bones=%d faces=%d" % (
        len(meshes), len(rig.data.bones),
        sum(len(obj.data.polygons) for obj in meshes)))
    print("NAMES " + ",".join(sorted(obj.name for obj in meshes)))


run()
