import bpy
import math
from mathutils import Vector


BLEND_PATH = "C:/palata/palata_zero.blend"
COLLECTION_NAME = "GAMEPLAY_CARE_PROPS_V2"


def make_material(name, base, roughness=0.9, metallic=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*base, 1.0)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    if shader:
        shader.inputs["Base Color"].default_value = (*base, 1.0)
        shader.inputs["Roughness"].default_value = roughness
        shader.inputs["Metallic"].default_value = metallic
    return mat


MAT_ENAMEL = make_material("MAT_care_old_enamel", (0.42, 0.46, 0.37), 0.92)
MAT_GLASS = make_material("MAT_care_cloudy_glass", (0.17, 0.24, 0.20), 0.38)
MAT_METAL = make_material("MAT_care_worn_metal", (0.25, 0.27, 0.23), 0.72, 0.42)
MAT_RUST = make_material("MAT_care_rust", (0.31, 0.065, 0.012), 0.98, 0.08)
MAT_PAPER = make_material("MAT_care_old_paper", (0.62, 0.56, 0.39), 0.98)
MAT_RED = make_material("MAT_care_red_label", (0.42, 0.025, 0.012), 0.9)
MAT_BLUE = make_material("MAT_care_blue_label", (0.035, 0.12, 0.19), 0.9)
MAT_AMBER = make_material("MAT_care_amber_glass", (0.28, 0.10, 0.025), 0.46)
MAT_LINEN = make_material("MAT_care_clean_linen", (0.52, 0.56, 0.44), 0.99)
MAT_DIRTY_LINEN = make_material("MAT_care_dirty_linen", (0.31, 0.30, 0.22), 0.99)
MAT_WATER = make_material("MAT_care_dirty_water", (0.055, 0.12, 0.11), 0.24)
MAT_SKIN = make_material("MAT_patient_skin_natural", (0.43, 0.30, 0.22), 0.94)
MAT_SKIN_PALE = make_material("MAT_patient_skin_pale", (0.36, 0.31, 0.25), 0.95)
MAT_HAIR = make_material("MAT_patient_hair", (0.025, 0.018, 0.011), 0.98)
MAT_GOWN = make_material("MAT_patient_gown_worn", (0.16, 0.27, 0.25), 0.99)
MAT_BLANKET = make_material("MAT_patient_blanket_blue", (0.20, 0.30, 0.32), 0.99)
MAT_BANDAGE = make_material("MAT_patient_bandage_old", (0.56, 0.52, 0.36), 0.99)
MAT_INK = make_material("MAT_patient_ink_dark", (0.025, 0.018, 0.012), 0.96)
MAT_CERAMIC = make_material("MAT_procedure_chipped_ceramic", (0.68, 0.70, 0.61), 0.82)
MAT_RUBBER = make_material("MAT_procedure_old_rubber", (0.045, 0.055, 0.045), 0.98)
MAT_CLOTH = make_material("MAT_procedure_canvas", (0.31, 0.34, 0.25), 0.99)
MAT_MERCURY = make_material("MAT_procedure_mercury", (0.12, 0.16, 0.14), 0.26, 0.55)
MAT_BOARD = make_material("MAT_assignment_board_green", (0.10, 0.18, 0.13), 0.97)
MAT_LIPS = make_material("MAT_patient_lips_natural", (0.24, 0.105, 0.085), 0.90)


def remove_tree(root):
    children = list(root.children_recursive)
    for child in reversed(children):
        bpy.data.objects.remove(child, do_unlink=True)


def link_to(obj, collection, parent=None):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    obj.parent = parent
    return obj


def add_empty(name, location, collection, parent=None):
    obj = bpy.data.objects.new(name, None)
    collection.objects.link(obj)
    obj.location = location
    obj.parent = parent
    return obj


def cube(name, location, size, material, collection, parent=None, rotation=(0, 0, 0), bevel=0.025):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.scale = tuple(v * 0.5 for v in size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.name = name
    link_to(obj, collection, parent)
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("soft_worn_edges", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
    return obj


def sphere(name, location, scale, material, collection, parent=None, segments=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=16, location=location)
    obj = bpy.context.object
    obj.scale = scale
    obj.name = name
    link_to(obj, collection, parent)
    obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def cylinder(name, location, radius, depth, material, collection, parent=None, rotation=(0, 0, 0), vertices=20):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    link_to(obj, collection, parent)
    obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def cylinder_between(name, start, end, radius, material, collection, parent=None, vertices=20):
    start_v, end_v = Vector(start), Vector(end)
    direction = end_v - start_v
    obj = cylinder(name, (start_v + end_v) * 0.5, radius, direction.length, material, collection, parent, vertices=vertices)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    obj.rotation_mode = "XYZ"
    return obj


def torus(name, location, major_radius, minor_radius, material, collection, parent=None, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_radius, minor_radius=minor_radius, major_segments=24, minor_segments=8, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    link_to(obj, collection, parent)
    obj.data.materials.append(material)
    return obj


def curve(name, points, bevel_depth, material, collection, parent=None, cyclic=False):
    data = bpy.data.curves.new(name + "_curve", "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = bevel_depth
    data.bevel_resolution = 2
    spline = data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, co in zip(spline.bezier_points, points):
        point.co = co
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(material)
    return obj


def text_mesh(name, body, location, size, material, collection, parent=None, rotation=(math.radians(90), 0, 0)):
    bpy.ops.object.text_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = 0.0015
    obj.data.bevel_depth = 0.0008
    link_to(obj, collection, parent)
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    obj.name = name
    return obj


def _ring_frame(direction):
    d = Vector(direction).normalized()
    up = Vector((0.0, 0.0, 1.0))
    if abs(d.dot(up)) > 0.94:
        up = Vector((0.0, 1.0, 0.0))
    side = d.cross(up).normalized()
    return side, side.cross(d).normalized()


def tube_mesh(name, points, radii, material, collection, parent, segments=14, squash=None):
    """A swept tube through a polyline - used for ears, which a sphere reads as a lump.

    Frames are parallel-transported from the first segment rather than
    recomputed independently at each point: an independent frame_for() per
    point can flip its "up" basis vector between neighbouring points with a
    similar direction, twisting the ring and producing spiky, self-crossing
    geometry - exactly what a low point-count ear curve triggers.
    """
    pts = [Vector(p) for p in points]
    directions = []
    for i in range(len(pts)):
        if i == 0:
            d = pts[1] - pts[0]
        elif i == len(pts) - 1:
            d = pts[-1] - pts[-2]
        else:
            d = pts[i + 1] - pts[i - 1]
        directions.append(d.normalized())
    side, up = _ring_frame(directions[0])
    rings = []
    for i, p in enumerate(pts):
        d = directions[i]
        side = (side - d * side.dot(d))
        if side.length < 1e-6:
            side = _ring_frame(d)[0]
        side = side.normalized()
        up = d.cross(side).normalized()
        r = radii[i]
        sq = 1.0 if squash is None else squash[i]
        rings.append([p + side * (math.cos(a) * r) + up * (math.sin(a) * r * sq)
                      for a in (math.tau * k / segments for k in range(segments))])
    verts = []
    faces = []
    n = segments
    for ring in rings:
        verts.extend(ring)
    for i in range(len(rings) - 1):
        a, b = i * n, (i + 1) * n
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((a + j, a + j2, b + j2, b + j))
    faces.append(tuple(range(n - 1, -1, -1)))
    faces.append(tuple(range((len(rings) - 1) * n, len(rings) * n)))
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata([tuple(v) for v in verts], [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return obj


def draped_blanket(name, material, collection, parent):
    """Low-poly cloth surface shaped around legs, hips and chest without a boxy slab."""
    x_steps = (-1.0, -0.52, 0.0, 0.52, 1.0)
    rows = (
        (-0.93, 0.27, 0.920, 0.010),
        (-0.67, 0.30, 0.945, 0.030),
        (-0.31, 0.34, 0.965, 0.050),
        (0.02, 0.37, 0.975, 0.065),
        (0.26, 0.35, 0.968, 0.035),
    )
    vertices = []
    for y, half_width, base_z, hump in rows:
        for normalized_x in x_steps:
            edge_drop = 0.030 * (abs(normalized_x) ** 1.7)
            body_hump = hump * (1.0 - abs(normalized_x) ** 1.55)
            vertices.append((half_width * normalized_x, y, base_z + body_hump - edge_drop))
    faces = []
    columns = len(x_steps)
    for row_index in range(len(rows) - 1):
        for column_index in range(columns - 1):
            a = row_index * columns + column_index
            faces.append((a, a + 1, a + columns + 1, a + columns))
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    solidify = obj.modifiers.new("cloth_thickness", "SOLIDIFY")
    solidify.thickness = 0.024
    solidify.offset = -0.4
    bevel = obj.modifiers.new("soft_blanket_edges", "BEVEL")
    bevel.width = 0.015
    bevel.segments = 2
    return obj


# --------------------------------------------------------------------------
# Sculpted patient head. A resting adult head, not a symmetric egg: the old
# version used a single circular cross-section (same radius toward the face
# as toward the back of the skull), which is why a nose bolted onto the front
# read as a golf-ball stuck to a sphere. This builds an asymmetric skull
# profile (face side vs. skull side) and folds nose/brow/cheek/chin/jaw into
# the same continuous surface, the technique proven on the violent-patient
# rebuild (tools/rebuild_violent_patient_human.py).
# --------------------------------------------------------------------------

HEAD_Y = 0.600            # sagittal axis the whole skull is built around
HEAD_CHIN_Z = 0.955        # bottom ring, where the neck cylinder meets the jaw
HEAD_APEX_Z = 1.325

# z, half-width, front depth (toward +Y / the face), back depth (toward -Y /
# the skull), squareness (<1 = boxier cross-section, 1 = round)
HEAD_PROFILE = [
    (0.955, 0.050, 0.076, 0.058, 0.82),
    (0.985, 0.082, 0.112, 0.070, 0.72),
    (1.015, 0.108, 0.128, 0.082, 0.70),
    (1.050, 0.130, 0.134, 0.094, 0.70),
    (1.090, 0.146, 0.132, 0.104, 0.74),
    (1.130, 0.155, 0.126, 0.112, 0.80),
    (1.170, 0.150, 0.116, 0.114, 0.86),
    (1.210, 0.136, 0.106, 0.112, 0.92),
    (1.250, 0.113, 0.094, 0.102, 0.97),
    (1.290, 0.079, 0.074, 0.080, 1.00),
    (1.315, 0.040, 0.040, 0.043, 1.00),
    (1.325, 0.010, 0.012, 0.013, 1.00),
]

# Anchor z-levels, matched to the original bolt-on feature positions so the
# patient keeps the same read (nose tip ~1.08, brows ~1.20, mouth ~1.01-1.02).
NOSE_TOP_Z, NOSE_BASE_Z = 1.145, 1.028
NOSE_PROFILE = [
    (0.00, 0.004), (0.22, 0.016), (0.44, 0.032),
    (0.66, 0.048), (0.82, 0.057), (0.93, 0.046), (1.00, 0.007),
]
BROW_Z, EYE_Z, CHEEK_HIGH_Z, CHEEK_LOW_Z = 1.198, 1.150, 1.112, 1.055
MOUTH_UPPER_Z, MOUTH_LOWER_Z, MOUTH_CREASE_Z = 1.019, 1.008, 1.0135
CHIN_Z, JAW_CORNER_Z, TEMPLE_Z = 0.978, 1.030, 1.222


def _lerp(a, b, t):
    return a + (b - a) * t


def _sample(table, key):
    if key <= table[0][0]:
        return table[0][1:]
    if key >= table[-1][0]:
        return table[-1][1:]
    for i in range(len(table) - 1):
        k0, k1 = table[i][0], table[i + 1][0]
        if k0 <= key <= k1:
            f = (key - k0) / (k1 - k0)
            return tuple(_lerp(a, b, f) for a, b in zip(table[i][1:], table[i + 1][1:]))
    return table[-1][1:]


def nose_push(x, z):
    if z > NOSE_TOP_Z or z < NOSE_BASE_Z:
        return 0.0
    t = (NOSE_TOP_Z - z) / (NOSE_TOP_Z - NOSE_BASE_Z)
    amount = _sample(NOSE_PROFILE, t)[0]
    half = 0.014 + 0.032 * (t ** 1.7)
    span = half * 1.85
    if abs(x) > span:
        return 0.0
    return amount * (1.0 - (abs(x) / span) ** 2) ** 1.1


def brow_push(x, z):
    dz = (z - BROW_Z) / 0.030
    ax = abs(x)
    if abs(dz) >= 1.0 or ax > 0.122:
        return 0.0
    across = 1.0 if ax < 0.080 else max(0.0, 1.0 - (ax - 0.080) / 0.042)
    glabella = 0.55 + 0.45 * min(1.0, ax / 0.018)
    return 0.020 * (1.0 - dz * dz) * across * glabella


def socket_pull(x, z):
    # Shallow - a sleeping patient's closed lids should read as a soft crease,
    # not a hollow skull socket. 0.024 (the first pass) carved a pit deep
    # enough to hard-shadow into a dark hole even under flat lighting.
    total = 0.0
    for cx in (0.060, -0.060):
        dx = (x - cx) / 0.058
        dz = (z - EYE_Z) / 0.030
        d = dx * dx + dz * dz
        if d < 1.0:
            total += 0.009 * (1.0 - d) ** 1.4
    return total


def cheek_shape(x, z):
    total = 0.0
    for cx in (0.100, -0.100):
        dx = (x - cx) / 0.062
        dz = (z - CHEEK_HIGH_Z) / 0.044
        d = dx * dx + dz * dz
        if d < 1.0:
            total += 0.014 * (1.0 - d)
    for cx in (0.092, -0.092):
        dx = (x - cx) / 0.058
        dz = (z - CHEEK_LOW_Z) / 0.044
        d = dx * dx + dz * dz
        if d < 1.0:
            total -= 0.012 * (1.0 - d)
    return total


def mouth_shape(x, z):
    if abs(x) > 0.062:
        return 0.0
    across = 1.0 - (abs(x) / 0.062) ** 2
    total = 0.0
    dz = (z - MOUTH_CREASE_Z) / 0.012
    if abs(dz) < 1.0:
        total -= 0.013 * (1.0 - dz * dz) * across
    dz = (z - MOUTH_UPPER_Z) / 0.015
    if abs(dz) < 1.0:
        total += 0.010 * (1.0 - dz * dz) * across
    dz = (z - MOUTH_LOWER_Z) / 0.015
    if abs(dz) < 1.0:
        total += 0.008 * (1.0 - dz * dz) * across
    if abs(x) < 0.017 and NOSE_BASE_Z - 0.024 < z < NOSE_BASE_Z:
        total -= 0.007 * (1.0 - (abs(x) / 0.017) ** 2)
    return total


def chin_push(x, z):
    dz = (z - CHIN_Z) / 0.038
    ax = abs(x)
    if abs(dz) >= 1.0 or ax > 0.056:
        return 0.0
    return 0.023 * (1.0 - dz * dz) * (1.0 - (ax / 0.056) ** 2)


def lateral_shift(x, z):
    total = 0.0
    dz = (z - JAW_CORNER_Z) / 0.044
    if abs(dz) < 1.0:
        total += 0.013 * (1.0 - dz * dz)
    dz = (z - TEMPLE_Z) / 0.048
    if abs(dz) < 1.0:
        total -= 0.016 * (1.0 - dz * dz)
    if NOSE_BASE_Z + 0.026 < z < NOSE_BASE_Z + 0.058 and 0.018 < abs(x) < 0.056:
        total += 0.010
    return total


def face_surface_y(x, z):
    """Front surface of the finished head at (x, z) - seats brows/lips/marks on it."""
    w, f, b, k = _sample(HEAD_PROFILE, z)
    sn = min(1.0, (min(abs(x), w * 0.999) / w) ** (1.0 / k))
    cn = math.sqrt(max(0.0, 1.0 - sn * sn))
    y = HEAD_Y + f * (cn ** k)
    forward = (nose_push(x, z) + brow_push(x, z) + chin_push(x, z)
               + cheek_shape(x, z) + mouth_shape(x, z) - socket_pull(x, z))
    return y + forward * (cn ** 1.35)


def head_ring(z, segments):
    w, f, b, k = _sample(HEAD_PROFILE, z)
    points = []
    for j in range(segments):
        theta = math.tau * j / segments        # theta=0 faces +Y (the face)
        s, c = math.sin(theta), math.cos(theta)
        sx = math.copysign(abs(s) ** k, s) if s else 0.0
        cx = math.copysign(abs(c) ** k, c) if c else 0.0
        x = w * sx
        y = HEAD_Y + (f if c > 0 else -b) * cx
        front = max(0.0, c) ** 1.35
        side = abs(s) ** 1.3

        forward = (nose_push(x, z) + brow_push(x, z) + chin_push(x, z)
                   + cheek_shape(x, z) + mouth_shape(x, z) - socket_pull(x, z))
        y += forward * front
        if x:
            x += math.copysign(lateral_shift(x, z), x) * side
        points.append((x, y, z))
    return points


def _mesh_from_rings_capped(rings, bottom_point=None, top_point=None):
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
        verts.append(bottom_point)
        for j in range(n):
            faces.append((index, j, (j + 1) % n))
    if top_point is not None:
        index = len(verts)
        verts.append(top_point)
        base = (len(rings) - 1) * n
        for j in range(n):
            faces.append((index, base + (j + 1) % n, base + j))
    return verts, faces


def patient_head_mesh(name, material, collection, parent):
    segments = 36
    levels = 26
    rings = []
    for i in range(levels):
        t = i / (levels - 1)
        eased = t * t * (3.0 - 2.0 * t) * 0.5 + t * 0.5
        z = _lerp(HEAD_CHIN_Z, HEAD_APEX_Z - 0.006, eased)
        rings.append(head_ring(z, segments))
    verts, faces = _mesh_from_rings_capped(
        rings,
        bottom_point=(0.0, HEAD_Y + 0.050, HEAD_CHIN_Z - 0.014),
        top_point=(0.0, HEAD_Y + 0.006, HEAD_APEX_Z),
    )
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.validate(clean_customdata=False)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    modifier = obj.modifiers.new("smooth_subdiv", "SUBSURF")
    modifier.levels = 1
    modifier.render_levels = 1
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.select_set(False)
    return obj


def build_patient(root, patient_id, display_name, variant):
    root_name = root.name
    collection = root.users_collection[0]
    bed_root = root.parent or bpy.data.objects.get(root_name.removesuffix("_patient_v3"))
    remove_tree(root)
    # The old bed roots contain baked transforms whose evaluated matrices are
    # unreliable inside Blender. Keep the patient as a world-positioned sibling
    # of the bed: this is visually identical in-game and makes Blender previews,
    # selection and export deterministic.
    if bed_root:
        obsolete_bedding = {
            f"{bed_root.name}_blanket",
            f"{bed_root.name}_blanket_knee_ridge",
        }
        for child in list(bed_root.children):
            if child.name in obsolete_bedding:
                bpy.data.objects.remove(child, do_unlink=True)
    # Recreate the legacy empty instead of reusing it: several original bed
    # containers have a stale identity matrix that survives ordinary edits.
    bpy.data.objects.remove(root, do_unlink=True)
    root = add_empty(root_name, bed_root.location.copy() if bed_root else (0, 0, 0), collection)
    if bed_root:
        root.rotation_mode = bed_root.rotation_mode
        root.rotation_euler = bed_root.rotation_euler.copy()
        root.scale = bed_root.scale.copy()
    root["patient_id"] = patient_id
    root["display_name"] = display_name
    skin = MAT_SKIN_PALE if variant % 3 == 1 else MAT_SKIN
    blanket = MAT_BLANKET if variant % 2 == 0 else MAT_LINEN

    # One continuous adult head. The face points toward +Y and no longer uses
    # stacked spheres for cheeks and jaw.
    patient_head_mesh(f"{root.name}_patient_head", skin, collection, root)
    cylinder(f"{root.name}_patient_neck", (0.0, 0.43, 1.035), 0.072, 0.19, skin, collection, root, rotation=(math.radians(90), 0, 0), vertices=24)
    sphere(f"{root.name}_patient_torso", (0.0, 0.16, 0.90), (0.285, 0.42, 0.105), MAT_GOWN, collection, root, 32)
    sphere(f"{root.name}_patient_hips", (0.0, -0.20, 0.855), (0.255, 0.28, 0.085), MAT_GOWN, collection, root, 28)

    # Arms lie naturally along or across the torso, with elbows and wrists joined.
    left_shoulder = (-0.23, 0.29, 0.98)
    right_shoulder = (0.23, 0.29, 0.98)
    left_elbow = (-0.31, 0.02, 0.94)
    right_elbow = (0.31, 0.04, 0.95)
    left_wrist = (-0.16, -0.16, 1.00)
    right_wrist = (0.14, -0.12, 1.015)
    cylinder_between(f"{root.name}_patient_upper_arm_L", left_shoulder, left_elbow, 0.052, MAT_GOWN, collection, root)
    cylinder_between(f"{root.name}_patient_forearm_L", left_elbow, left_wrist, 0.044, skin, collection, root)
    cylinder_between(f"{root.name}_patient_upper_arm_R", right_shoulder, right_elbow, 0.052, MAT_GOWN, collection, root)
    cylinder_between(f"{root.name}_patient_forearm_R", right_elbow, right_wrist, 0.044, skin, collection, root)
    for suffix, elbow in (("L", left_elbow), ("R", right_elbow)):
        sphere(f"{root.name}_patient_elbow_{suffix}", elbow, (0.057, 0.057, 0.052), skin, collection, root, 18)
    sphere(f"{root.name}_patient_hand_L", left_wrist, (0.055, 0.082, 0.035), skin, collection, root, 20)
    sphere(f"{root.name}_patient_hand_R", right_wrist, (0.055, 0.082, 0.035), skin, collection, root, 20)

    # Cloth follows the actual body profile and tapers around legs and shoulders.
    draped_blanket(f"{root.name}_patient_blanket", blanket, collection, root)
    cube(f"{root.name}_patient_blanket_top_fold", (0.0, 0.235, 0.995), (0.70, 0.075, 0.032), MAT_LINEN, collection, root, bevel=0.014)

    # Restrained facial features suitable for a sleeping or sedated adult. Nose
    # is now sculpted into the head mesh itself; brows/eye-creases/lips sit
    # flush on face_surface_y() instead of floating a fixed offset in front of
    # a flat sphere, so nothing reads as a bolted-on tube.
    for suffix, side in (("L", -1.0), ("R", 1.0)):
        # Monotonic in z (top to bottom of the ear) so segment direction never
        # reverses - a path that curves back on itself (the earlier version
        # bulged out in x then back in) makes even a parallel-transported tube
        # frame twist between rings.
        points = [
            (side * 0.148, HEAD_Y + 0.006, 1.140),
            (side * 0.168, HEAD_Y + 0.000, 1.126),
            (side * 0.174, HEAD_Y - 0.004, 1.108),
            (side * 0.164, HEAD_Y - 0.006, 1.090),
            (side * 0.148, HEAD_Y - 0.006, 1.076),
        ]
        radii = [0.017, 0.030, 0.033, 0.026, 0.014]
        squash = [0.40, 0.34, 0.32, 0.36, 0.42]
        tube_mesh(f"{root.name}_patient_ear_{suffix}", points, radii, skin, collection, root,
                  segments=14, squash=squash)

    for suffix, side in (("L", -1.0), ("R", 1.0)):
        x0 = side * 0.020
        points = [(x0 + side * 0.058 * t, face_surface_y(x0 + side * 0.058 * t, BROW_Z) - 0.002,
                   BROW_Z + 0.006 * math.sin(math.pi * t) - 0.010 * t * t) for t in (0.0, 0.16, 0.33, 0.5, 0.66, 0.83, 1.0)]
        radii = [0.0092 - 0.0034 * t for t in (0.0, 0.16, 0.33, 0.5, 0.66, 0.83, 1.0)]
        tube_mesh(f"{root.name}_patient_brow_{suffix}", points, radii, MAT_HAIR, collection, root,
                  segments=8, squash=[0.5] * 7)

        # A closed eye reads as a shallow crease, not a floating dark line
        # standing off the face - the eyelid follows the socket curvature.
        ex = side * 0.060
        points = [(ex - side * 0.036 * (1 - t) + side * 0.036 * t,
                   face_surface_y(ex - side * 0.036 * (1 - t) + side * 0.036 * t, EYE_Z) + 0.0006,
                   EYE_Z + 0.006 * math.sin(math.pi * t)) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
        radii = [0.0009, 0.0016, 0.0019, 0.0016, 0.0009]
        tube_mesh(f"{root.name}_patient_closed_eye_{suffix}", points, radii, MAT_INK, collection, root,
                  segments=6, squash=[0.4] * 5)

    for x in (-0.017, 0.017):
        z = NOSE_BASE_Z - 0.006
        sphere(f"{root.name}_patient_nostril", (x, face_surface_y(x, z) - 0.006, z),
               (0.0068, 0.0048, 0.0048), MAT_LIPS, collection, root, 12)

    for name, z, depth, width in (("upper_lip", MOUTH_UPPER_Z, 0.0032, 0.058),
                                   ("lower_lip", MOUTH_LOWER_Z, 0.0026, 0.050)):
        points = [(width * t, face_surface_y(width * t, z) - 0.0010, z)
                  for t in (-1.0, -0.5, 0.0, 0.5, 1.0)]
        radii = [depth * f for f in (0.35, 0.85, 1.0, 0.85, 0.35)]
        tube_mesh(f"{root.name}_patient_{name}", points, radii, MAT_LIPS, collection, root,
                  segments=8, squash=[0.55] * 5)

    # Thin, close-cropped scalp hair rather than a solid black beret.
    hair_top = HEAD_APEX_Z - 0.006
    hair_low = 1.225  # well above BROW_Z=1.198, or the fringe covers the eyes
    hair_rings = []
    for i in range(8):
        t = i / 7.0
        z = _lerp(hair_low, hair_top, t)
        w, f, b, k = _sample(HEAD_PROFILE, z)
        clump = 0.008 * (1.0 - t * 0.4)
        ring = []
        for j in range(24):
            theta = math.tau * j / 24
            s, c = math.sin(theta), math.cos(theta)
            sx = math.copysign(abs(s) ** k, s) if s else 0.0
            cx = math.copysign(abs(c) ** k, c) if c else 0.0
            ring.append(((w + clump) * sx, HEAD_Y + ((f if c > 0 else -b) + clump * (0.4 if c > 0 else 1.0)) * cx, z))
        hair_rings.append(ring)
    hair_verts = []
    hair_faces = []
    n = 24
    for ring in hair_rings:
        hair_verts.extend(ring)
    for i in range(len(hair_rings) - 1):
        a, b = i * n, (i + 1) * n
        for j in range(n):
            j2 = (j + 1) % n
            hair_faces.append((a + j, a + j2, b + j2, b + j))
    apex_index = len(hair_verts)
    hair_verts.append((0.0, HEAD_Y + 0.006, hair_top + 0.004))
    base = (len(hair_rings) - 1) * n
    for j in range(n):
        hair_faces.append((apex_index, base + (j + 1) % n, base + j))
    hair_mesh = bpy.data.meshes.new(f"{root.name}_patient_hair_cap_mesh")
    hair_mesh.from_pydata(hair_verts, [], hair_faces)
    hair_mesh.update()
    hair_obj = bpy.data.objects.new(f"{root.name}_patient_hair_cap", hair_mesh)
    collection.objects.link(hair_obj)
    hair_obj.parent = root
    hair_mesh.materials.append(MAT_HAIR)
    solidify = hair_obj.modifiers.new("thin_shell", "SOLIDIFY")
    solidify.thickness = 0.006
    solidify.offset = 1.0
    bpy.context.view_layer.objects.active = hair_obj
    hair_obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=solidify.name)
    hair_obj.select_set(False)
    for polygon in hair_mesh.polygons:
        polygon.use_smooth = True

    if variant in (1, 4):
        bz = 1.205
        cube(f"{root.name}_patient_forehead_bandage", (0.0, face_surface_y(0.0, bz) + 0.006, bz),
             (0.26, 0.020, 0.062), MAT_BANDAGE, collection, root, bevel=0.010)
    if variant in (2, 5):
        oz = EYE_Z
        curve(f"{root.name}_patient_oxygen_line",
              [(-0.13, face_surface_y(-0.13, oz) + 0.01, oz),
               (0.0, face_surface_y(0.0, NOSE_BASE_Z) + 0.014, NOSE_BASE_Z),
               (0.15, face_surface_y(0.15, oz) + 0.01, oz),
               (0.35, 0.25, 1.05)],
              0.007, MAT_BLUE, collection, root)

    # Identification band and bedside treatment card make patients distinguishable.
    torus(f"{root.name}_patient_id_wristband", left_wrist, 0.050, 0.009, MAT_PAPER, collection, root, rotation=(math.radians(90), 0, 0))
    card = cube(f"{root.name}_patient_chart_card", (0.43, 0.48, 1.16), (0.28, 0.025, 0.19), MAT_PAPER, collection, root, rotation=(math.radians(8), 0, 0), bevel=0.008)
    card["patient_id"] = patient_id
    cube(f"{root.name}_patient_chart_red_stripe", (0.43, 0.463, 1.205), (0.24, 0.008, 0.018), MAT_RED, collection, root, rotation=(math.radians(8), 0, 0), bevel=0.002)


def medicine_package(root_name, location, color, kind, collection):
    root = add_empty(root_name, location, collection)
    root["care_item"] = kind
    cube(root_name + "_box", (0, 0, 0), (0.26, 0.08, 0.16), MAT_PAPER, collection, root, bevel=0.012)
    cube(root_name + "_label", (0, -0.043, 0.0), (0.20, 0.008, 0.09), color, collection, root, bevel=0.003)
    for x in (-0.065, 0.0, 0.065):
        cube(root_name + "_print_line", (x, -0.049, -0.01), (0.010, 0.003, 0.065), MAT_INK, collection, root, bevel=0.001)
    return root


def build_props(collection):
    # Deep inside the procedure room, leaving its doorway fully clear.
    cabinet = add_empty("care_medicine_cabinet", (-4.15, 5.30, 0.0), collection)
    cube("care_cabinet_body", (0, 0, 0.95), (1.35, 0.42, 1.90), MAT_ENAMEL, collection, cabinet, bevel=0.035)
    cube("care_cabinet_inner", (0, -0.225, 1.02), (1.18, 0.08, 1.62), MAT_INK, collection, cabinet, bevel=0.015)
    for z in (0.48, 0.95, 1.42):
        cube("care_cabinet_shelf", (0, -0.31, z), (1.18, 0.32, 0.045), MAT_METAL, collection, cabinet, bevel=0.008)
    for x in (-0.31, 0.31):
        cube("care_cabinet_glass_door", (x, -0.245, 1.10), (0.56, 0.035, 1.42), MAT_GLASS, collection, cabinet, bevel=0.018)
        cylinder("care_cabinet_handle", (x + (-0.19 if x > 0 else 0.19), -0.285, 1.10), 0.014, 0.28, MAT_METAL, collection, cabinet)
    medicine_package("interaction_med_aminazine", (-4.52, 5.02, 1.43), MAT_RED, "aminazine", collection)
    medicine_package("interaction_med_cordiamin", (-4.16, 5.02, 1.43), MAT_BLUE, "cordiamin", collection)
    medicine_package("interaction_med_bandage", (-3.80, 5.02, 1.43), MAT_LINEN, "bandage", collection)

    saline = add_empty("interaction_med_saline", (-4.46, 5.00, 0.91), collection)
    saline["care_item"] = "saline"
    cube("care_saline_bag", (0, 0, 0), (0.22, 0.055, 0.32), MAT_LINEN, collection, saline, bevel=0.035)
    cube("care_saline_blue_label", (0, -0.032, -0.02), (0.15, 0.008, 0.09), MAT_BLUE, collection, saline, bevel=0.004)
    curve("care_saline_tube", [(0.0, 0.0, -0.16), (0.05, -0.02, -0.28), (0.10, 0.0, -0.38)], 0.008, MAT_GLASS, collection, saline)

    # Dedicated trolley along the west wall. Nothing is placed on the examination
    # couch anymore, and the central route from the door to the sink stays open.
    cart = add_empty("interaction_medical_cart", (-4.38, 3.25, 0.0), collection)
    cart["care_item"] = "medical_cart"
    cube("care_cart_top", (0, 0, 0.90), (0.92, 1.16, 0.09), MAT_ENAMEL, collection, cart, bevel=0.035)
    cube("care_cart_lower_shelf", (0, 0, 0.40), (0.82, 1.04, 0.055), MAT_METAL, collection, cart, bevel=0.022)
    for x in (-0.35, 0.35):
        for y in (-0.47, 0.47):
            cylinder("care_cart_post", (x, y, 0.63), 0.018, 0.50, MAT_METAL, collection, cart, vertices=14)
            torus("care_cart_wheel", (x, y, 0.12), 0.070, 0.018, MAT_RUBBER, collection, cart, rotation=(math.radians(90), 0, 0))
    cube("care_cart_drawer", (0.47, 0, 0.76), (0.06, 0.82, 0.18), MAT_ENAMEL, collection, cart, bevel=0.022)
    cylinder_between("care_cart_drawer_handle", (0.505, -0.22, 0.76), (0.505, 0.22, 0.76), 0.012, MAT_METAL, collection, cart, 12)
    cylinder_between("care_cart_handle_left", (-0.34, 0.59, 0.88), (-0.34, 0.59, 1.08), 0.015, MAT_METAL, collection, cart, 12)
    cylinder_between("care_cart_handle_right", (0.34, 0.59, 0.88), (0.34, 0.59, 1.08), 0.015, MAT_METAL, collection, cart, 12)
    cylinder_between("care_cart_handle_grip", (-0.34, 0.59, 1.08), (0.34, 0.59, 1.08), 0.017, MAT_RUBBER, collection, cart, 12)

    tray = add_empty("care_instrument_tray", (-4.38, 3.25, 0.98), collection)
    cube("care_instrument_tray_pan", (0, 0, 0), (0.78, 1.02, 0.055), MAT_METAL, collection, tray, bevel=0.045)
    stethoscope = add_empty("interaction_med_stethoscope", (-4.57, 2.82, 1.02), collection)
    stethoscope["care_item"] = "stethoscope"
    curve("care_stethoscope_tube", [(-0.13, 0.0, 0.0), (-0.12, -0.10, 0.0), (0.0, -0.16, 0.0), (0.12, -0.10, 0.0), (0.13, 0.0, 0.0)], 0.012, MAT_INK, collection, stethoscope)
    cylinder("care_stethoscope_chest_piece", (0, -0.17, 0), 0.045, 0.018, MAT_METAL, collection, stethoscope, rotation=(math.radians(90), 0, 0))
    thermometer = add_empty("interaction_med_thermometer", (-4.15, 2.84, 1.02), collection)
    thermometer.rotation_euler.z = math.radians(90.0)
    thermometer["care_item"] = "thermometer"
    cylinder("care_thermometer_glass", (0, 0, 0), 0.014, 0.30, MAT_GLASS, collection, thermometer, rotation=(0, math.radians(90), 0), vertices=16)
    cylinder("care_thermometer_tip", (-0.15, 0, 0), 0.019, 0.035, MAT_METAL, collection, thermometer, rotation=(0, math.radians(90), 0), vertices=16)

    # Detailed instruments arranged on the tray. They are separate modeled props,
    # not flat texture cards, so they read correctly from every camera angle.
    syringe = add_empty("procedure_syringe", (-4.58, 3.48, 1.02), collection)
    syringe.rotation_euler.z = math.radians(90.0)
    cylinder("procedure_syringe_barrel", (0, 0, 0), 0.026, 0.24, MAT_GLASS, collection, syringe, rotation=(0, math.radians(90), math.radians(-8)), vertices=20)
    cylinder("procedure_syringe_plunger", (-0.145, 0.020, 0), 0.011, 0.12, MAT_METAL, collection, syringe, rotation=(0, math.radians(90), math.radians(-8)), vertices=16)
    cube("procedure_syringe_thumb_rest", (-0.205, 0.028, 0), (0.025, 0.11, 0.012), MAT_METAL, collection, syringe, rotation=(0, 0, math.radians(-8)), bevel=0.004)
    cylinder("procedure_syringe_needle_hub", (0.145, -0.020, 0), 0.017, 0.055, MAT_BLUE, collection, syringe, rotation=(0, math.radians(90), math.radians(-8)), vertices=16)
    cylinder("procedure_syringe_needle", (0.255, -0.035, 0), 0.0035, 0.19, MAT_METAL, collection, syringe, rotation=(0, math.radians(90), math.radians(-8)), vertices=10)

    scissors = add_empty("procedure_surgical_scissors", (-4.18, 3.48, 1.02), collection)
    scissors.rotation_euler.z = math.radians(5)
    for x in (-0.060, 0.060):
        torus("procedure_scissors_handle", (x, -0.115, 0), 0.052, 0.010, MAT_METAL, collection, scissors)
    sphere("procedure_scissors_joint", (0, -0.015, 0.004), (0.022, 0.022, 0.010), MAT_RUST, collection, scissors, 14)
    cylinder_between("procedure_scissors_blade_L", (-0.040, -0.070, 0), (-0.018, 0.180, 0), 0.010, MAT_METAL, collection, scissors, 12)
    cylinder_between("procedure_scissors_blade_R", (0.040, -0.070, 0), (0.060, 0.180, 0), 0.010, MAT_METAL, collection, scissors, 12)

    clamp = add_empty("procedure_hemostatic_clamp", (-4.18, 3.12, 1.022), collection)
    clamp.rotation_euler.z = math.radians(-5)
    for x in (-0.044, 0.044):
        torus("procedure_clamp_handle", (x, -0.115, 0), 0.040, 0.008, MAT_METAL, collection, clamp)
    sphere("procedure_clamp_joint", (0, -0.035, 0.003), (0.018, 0.018, 0.009), MAT_RUST, collection, clamp, 12)
    cylinder_between("procedure_clamp_jaw_L", (-0.025, -0.045, 0), (-0.018, 0.180, 0), 0.007, MAT_METAL, collection, clamp, 10)
    cylinder_between("procedure_clamp_jaw_R", (0.025, -0.045, 0), (0.018, 0.180, 0), 0.007, MAT_METAL, collection, clamp, 10)

    scalpel = add_empty("procedure_scalpel", (-4.56, 3.08, 1.022), collection)
    scalpel.rotation_euler.z = math.radians(88)
    cube("procedure_scalpel_handle", (-0.055, 0, 0), (0.22, 0.032, 0.018), MAT_METAL, collection, scalpel, bevel=0.008)
    cube("procedure_scalpel_grip", (-0.070, 0, 0.004), (0.11, 0.038, 0.009), MAT_RUBBER, collection, scalpel, bevel=0.005)
    cube("procedure_scalpel_blade", (0.105, 0, 0), (0.10, 0.026, 0.010), MAT_MERCURY, collection, scalpel, rotation=(0, 0, math.radians(-5)), bevel=0.003)

    # A kidney dish and enamel bowl are stored on the lower trolley shelf.
    kidney = add_empty("procedure_kidney_dish", (-4.52, 3.43, 0.47), collection)
    rim = torus("procedure_kidney_dish_rim", (0, 0, 0.035), 0.19, 0.018, MAT_METAL, collection, kidney)
    rim.scale.y = 0.58
    basin = sphere("procedure_kidney_dish_basin", (0, 0, 0), (0.18, 0.10, 0.032), MAT_MERCURY, collection, kidney, 28)
    basin.scale.x *= 1.10
    sphere("procedure_kidney_dish_indent", (0.15, 0, 0.025), (0.085, 0.065, 0.020), MAT_INK, collection, kidney, 20)
    bowl = add_empty("procedure_enamel_bowl", (-4.22, 3.08, 0.47), collection)
    cylinder("procedure_enamel_bowl_body", (0, 0, 0.035), 0.135, 0.070, MAT_CERAMIC, collection, bowl, vertices=32)
    torus("procedure_enamel_bowl_rim", (0, 0, 0.075), 0.135, 0.012, MAT_METAL, collection, bowl)
    sphere("procedure_enamel_bowl_inside", (0, 0, 0.071), (0.11, 0.11, 0.022), MAT_INK, collection, bowl, 24)

    # Wooden ampoule rack on the middle cabinet shelf.
    ampoule_rack = add_empty("procedure_ampoule_rack", (-3.95, 4.98, 0.98), collection)
    cube("procedure_ampoule_rack_base", (0, 0, 0), (0.54, 0.18, 0.045), MAT_PAPER, collection, ampoule_rack, bevel=0.012)
    cube("procedure_ampoule_rack_back", (0, 0.075, 0.12), (0.54, 0.035, 0.26), MAT_PAPER, collection, ampoule_rack, bevel=0.012)
    for index in range(6):
        x = -0.205 + index * 0.082
        cylinder("procedure_ampoule_glass", (x, -0.015, 0.105), 0.020, 0.19, MAT_AMBER, collection, ampoule_rack, vertices=16)
        cylinder("procedure_ampoule_neck", (x, -0.015, 0.215), 0.010, 0.045, MAT_AMBER, collection, ampoule_rack, vertices=12)
        sphere("procedure_ampoule_tip", (x, -0.015, 0.245), (0.012, 0.012, 0.018), MAT_AMBER, collection, ampoule_rack, 12)
        cube("procedure_ampoule_label", (x, -0.038, 0.10), (0.035, 0.006, 0.045), MAT_PAPER, collection, ampoule_rack, bevel=0.002)

    # Gauze/cotton jars use geometry inside cloudy glass instead of image labels.
    for index, (x, contents) in enumerate(((-4.38, MAT_LINEN), (-4.05, MAT_BANDAGE))):
        jar = add_empty(f"procedure_gauze_jar_{index}", (x, 4.98, 0.49), collection)
        cylinder(f"procedure_gauze_jar_glass_{index}", (0, 0, 0.13), 0.115, 0.26, MAT_GLASS, collection, jar, vertices=28)
        torus(f"procedure_gauze_jar_lip_{index}", (0, 0, 0.27), 0.112, 0.010, MAT_METAL, collection, jar)
        cylinder(f"procedure_gauze_jar_lid_{index}", (0, 0, 0.295), 0.122, 0.035, MAT_METAL, collection, jar, vertices=28)
        for ball_index in range(5):
            angle = math.tau * ball_index / 5.0
            sphere(f"procedure_gauze_piece_{index}", (math.cos(angle) * 0.045, math.sin(angle) * 0.045, 0.09 + 0.035 * (ball_index % 2)), (0.045, 0.040, 0.038), contents, collection, jar, 14)
        cube(f"procedure_gauze_jar_label_{index}", (0, -0.119, 0.15), (0.13, 0.008, 0.075), MAT_PAPER, collection, jar, bevel=0.004)

    # Wall sphygmomanometer with fabric cuff, mercury column and rubber tubing.
    # It is mounted on the east wall, away from the sink.
    pressure = add_empty("procedure_wall_sphygmomanometer", (-0.12, 4.28, 1.72), collection)
    pressure.rotation_euler.z = math.radians(90.0)
    cube("procedure_pressure_case", (0, 0, 0), (0.48, 0.11, 0.72), MAT_ENAMEL, collection, pressure, bevel=0.035)
    cube("procedure_pressure_scale", (0, -0.065, 0.05), (0.25, 0.025, 0.52), MAT_PAPER, collection, pressure, bevel=0.012)
    cylinder("procedure_pressure_mercury", (0, -0.084, 0.015), 0.012, 0.38, MAT_MERCURY, collection, pressure, vertices=12)
    for z in (-0.18, -0.09, 0.0, 0.09, 0.18, 0.27):
        cube("procedure_pressure_tick", (0.065, -0.087, z), (0.075, 0.005, 0.009), MAT_INK, collection, pressure, bevel=0.001)
    cuff = add_empty("procedure_pressure_cuff", (-0.58, -0.02, -0.12), collection, pressure)
    cube("procedure_pressure_cuff_fabric", (0, 0, 0), (0.42, 0.12, 0.25), MAT_CLOTH, collection, cuff, rotation=(0, 0, math.radians(-10)), bevel=0.035)
    cube("procedure_pressure_cuff_strap", (0.20, -0.075, 0), (0.25, 0.045, 0.10), MAT_RUBBER, collection, cuff, rotation=(0, 0, math.radians(-10)), bevel=0.018)
    curve("procedure_pressure_tube", [(-0.15, -0.08, -0.26), (-0.24, -0.12, -0.48), (-0.02, -0.14, -0.62), (0.18, -0.10, -0.42)], 0.012, MAT_RUBBER, collection, pressure)
    sphere("procedure_pressure_bulb", (0.21, -0.10, -0.44), (0.055, 0.045, 0.11), MAT_RUBBER, collection, pressure, 20)

    # Floor sterilizer drum stands against the east wall, outside the door line.
    sterilizer = add_empty("procedure_sterilizer_drum", (-0.43, 2.58, 0.0), collection)
    cylinder("procedure_sterilizer_body", (0, 0, 0.39), 0.27, 0.70, MAT_METAL, collection, sterilizer, vertices=32)
    torus("procedure_sterilizer_bottom_ring", (0, 0, 0.05), 0.27, 0.018, MAT_RUST, collection, sterilizer)
    torus("procedure_sterilizer_top_ring", (0, 0, 0.74), 0.27, 0.018, MAT_METAL, collection, sterilizer)
    cylinder("procedure_sterilizer_lid", (0, 0, 0.77), 0.29, 0.06, MAT_ENAMEL, collection, sterilizer, vertices=32)
    cylinder_between("procedure_sterilizer_handle_L", (-0.13, 0, 0.80), (-0.13, 0, 0.92), 0.012, MAT_METAL, collection, sterilizer, 12)
    cylinder_between("procedure_sterilizer_handle_R", (0.13, 0, 0.80), (0.13, 0, 0.92), 0.012, MAT_METAL, collection, sterilizer, 12)
    cylinder_between("procedure_sterilizer_handle_grip", (-0.13, 0, 0.92), (0.13, 0, 0.92), 0.014, MAT_RUBBER, collection, sterilizer, 12)
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        sphere("procedure_sterilizer_vent", (math.cos(rad) * 0.272, math.sin(rad) * 0.272, 0.45), (0.022, 0.012, 0.022), MAT_INK, collection, sterilizer, 10)

    # Compact assignment board, level and flush with the corridor wall.
    board = add_empty("interaction_assignment_board", (4.50, 1.505, 1.84), collection)
    board.scale = (0.72, 1.0, 0.78)
    board["care_item"] = "assignment_board"
    cube("care_assignment_board_back", (0, 0, 0), (1.30, 0.07, 0.80), MAT_ENAMEL, collection, board, bevel=0.020)
    cube("care_assignment_board_inner", (0, -0.043, 0), (1.16, 0.025, 0.66), MAT_BOARD, collection, board, bevel=0.012)
    cube("care_assignment_schedule", (0, -0.061, -0.015), (0.98, 0.012, 0.55), MAT_PAPER, collection, board, bevel=0.006)
    for z in (-0.225, -0.125, -0.025, 0.075):
        cube("care_assignment_separator", (0, -0.071, z), (0.88, 0.004, 0.007), MAT_INK, collection, board, bevel=0.001)
    text_mesh("care_assignment_title", "НАЗНАЧЕНИЯ", (0, -0.077, 0.245), 0.060, MAT_INK, collection, board)
    assignments = (
        ("ПАЛАТА 4   САВЕЛЬЕВ", 0.125),
        ("ПАЛАТА 2   ЛЕВЧЕНКО", 0.025),
        ("ПАЛАТА 1   МОРОЗОВ", -0.075),
        ("ПРОЦЕДУРНАЯ   НОЧЬ", -0.175),
    )
    for index, (body, z) in enumerate(assignments):
        text_mesh(f"care_assignment_row_{index}", body, (0, -0.078, z), 0.043, MAT_INK, collection, board)
    for x in (-0.53, 0.53):
        sphere("care_assignment_screw", (x, -0.078, 0.315), (0.020, 0.010, 0.020), MAT_METAL, collection, board, 12)

    linen = add_empty("interaction_clean_linen", (8.28, -5.18, 0.88), collection)
    linen["care_item"] = "clean_linen"
    for index, (z, mat) in enumerate(((0.0, MAT_LINEN), (0.13, MAT_BLANKET), (0.26, MAT_LINEN))):
        cube(f"care_clean_linen_fold_{index}", (0, 0, z), (0.72, 0.44, 0.12), mat, collection, linen, bevel=0.035)
        curve(f"care_linen_seam_{index}", [(-0.29, -0.23, z + 0.06), (0, -0.235, z + 0.07), (0.29, -0.23, z + 0.06)], 0.006, MAT_DIRTY_LINEN, collection, linen)

    # Keep the dirty-linen basket inside the sanitary room.  Its old X=10.15
    # centre straddled partition_S_10 (the basket is 0.73 m wide), leaving half
    # of it visibly embedded in the wall.  This position also clears the rack.
    basket = add_empty("interaction_laundry_basket", (9.30, -4.65, 0.0), collection)
    basket["care_item"] = "laundry_basket"
    cylinder("care_laundry_basket_body", (0, 0, 0.38), 0.34, 0.72, MAT_ENAMEL, collection, basket, vertices=28)
    torus("care_laundry_basket_rim", (0, 0, 0.75), 0.34, 0.025, MAT_METAL, collection, basket)
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        cube("care_laundry_vent", (math.cos(rad) * 0.335, math.sin(rad) * 0.335, 0.42), (0.05, 0.018, 0.26), MAT_INK, collection, basket, rotation=(0, 0, rad), bevel=0.005)
    sphere("care_dirty_linen_top", (0, 0, 0.67), (0.28, 0.25, 0.12), MAT_DIRTY_LINEN, collection, basket, 20)

    # Irregular shallow puddle in the shower; hidden until the violent patient causes the incident.
    puddle = add_empty("interaction_water_spill", (2.5, -4.72, 0.018), collection)
    puddle["care_item"] = "water_spill"
    verts = [(0, 0, 0.0)]
    ring = []
    for index, radius in enumerate((1.05, 0.86, 1.18, 0.92, 1.12, 0.80, 1.17, 0.91, 1.08, 0.84, 1.16, 0.88)):
        angle = math.tau * index / 12.0
        ring.append((math.cos(angle) * radius, math.sin(angle) * radius * 0.62, 0.0))
    verts.extend(ring)
    faces = [(0, index + 1, ((index + 1) % 12) + 1) for index in range(12)]
    mesh = bpy.data.meshes.new("care_water_spill_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    surface = bpy.data.objects.new("care_water_spill_surface", mesh)
    collection.objects.link(surface)
    surface.parent = puddle
    surface.data.materials.append(MAT_WATER)
    for x, y, scale in ((0.35, 0.12, 0.34), (-0.45, -0.18, 0.26), (0.66, -0.25, 0.20)):
        sphere("care_water_spill_glint", (x, y, 0.01), (scale, scale * 0.45, 0.008), MAT_GLASS, collection, puddle, 18)

    # Mounted on the inside face of the east stair wall, facing back into the corridor.
    seal = add_empty("interaction_fire_exit_seal", (20.365, 1.10, 1.35), collection)
    seal.rotation_euler.z = math.radians(-90.0)
    seal["care_item"] = "fire_exit_seal"
    cube("care_fire_seal_plate", (0, 0, 0), (0.30, 0.045, 0.42), MAT_ENAMEL, collection, seal, bevel=0.018)
    cylinder("care_fire_seal_wire", (0, -0.04, 0), 0.012, 0.34, MAT_METAL, collection, seal, rotation=(0, 0, math.radians(20)), vertices=12)
    sphere("care_fire_seal_wax", (0.05, -0.065, -0.05), (0.055, 0.018, 0.055), MAT_RED, collection, seal, 16)

    indicator = add_empty("interaction_elevator_inspection", (12.50, -1.405, 1.92), collection)
    indicator.rotation_euler.z = math.pi
    indicator["care_item"] = "elevator_inspection"
    cube("care_elevator_indicator_frame", (0, 0, 0), (0.42, 0.05, 0.24), MAT_METAL, collection, indicator, bevel=0.018)
    cube("care_elevator_indicator_screen", (0, -0.032, 0), (0.30, 0.012, 0.13), MAT_INK, collection, indicator, bevel=0.008)
    sphere("care_elevator_indicator_lamp", (0.0, -0.045, 0.0), (0.035, 0.012, 0.035), MAT_RED, collection, indicator, 16)

    # Open wall cabinet in the medical equipment storage room with reusable canvas restraints.
    restraint_cabinet = add_empty("care_emergency_restraint_cabinet", (20.30, 4.72, 1.48), collection)
    restraint_cabinet.rotation_euler.z = math.radians(-90.0)
    cube("care_restraint_cabinet_back", (0, 0.10, 0), (0.92, 0.12, 0.92), MAT_ENAMEL, collection, restraint_cabinet, bevel=0.025)
    cube("care_restraint_cabinet_top", (0, -0.04, 0.46), (0.98, 0.34, 0.08), MAT_METAL, collection, restraint_cabinet, bevel=0.018)
    cube("care_restraint_cabinet_bottom", (0, -0.04, -0.46), (0.98, 0.34, 0.08), MAT_METAL, collection, restraint_cabinet, bevel=0.018)
    for x in (-0.46, 0.46):
        cube("care_restraint_cabinet_side", (x, -0.04, 0), (0.08, 0.34, 0.92), MAT_METAL, collection, restraint_cabinet, bevel=0.018)
    cube("care_restraint_cabinet_shelf", (0, -0.08, -0.05), (0.88, 0.28, 0.055), MAT_METAL, collection, restraint_cabinet, bevel=0.010)

    restraints = add_empty("interaction_patient_restraints", (20.00, 4.72, 1.43), collection)
    restraints.rotation_euler.z = math.radians(-90.0)
    restraints["care_item"] = "patient_restraints"
    for x in (-0.16, 0.16):
        torus("care_restraint_coil", (x, 0, 0), 0.12, 0.026, MAT_DIRTY_LINEN, collection, restraints, rotation=(math.radians(90), 0, 0))
        cube("care_restraint_buckle", (x, -0.035, 0), (0.10, 0.035, 0.075), MAT_METAL, collection, restraints, bevel=0.012)
    cube("care_restraint_label", (0, -0.045, -0.19), (0.42, 0.025, 0.12), MAT_PAPER, collection, restraints, bevel=0.010)

    # A bulky late-Soviet computer on the doctors' desk; resting here restores sanity.
    computer = add_empty("interaction_doctors_computer", (7.50, 4.28, 0.84), collection)
    computer["care_item"] = "doctors_computer"
    cube("care_computer_case", (0, 0, 0.34), (0.76, 0.48, 0.62), MAT_ENAMEL, collection, computer, bevel=0.055)
    cube("care_computer_bezel", (0, -0.255, 0.36), (0.62, 0.06, 0.45), MAT_INK, collection, computer, bevel=0.035)
    cube("care_computer_screen", (0, -0.292, 0.37), (0.49, 0.018, 0.32), MAT_GLASS, collection, computer, bevel=0.045)
    sphere("care_computer_power_lamp", (0.27, -0.303, 0.13), (0.022, 0.010, 0.022), MAT_RED, collection, computer, 12)
    cube("care_computer_keyboard", (0, -0.48, 0.035), (0.82, 0.34, 0.07), MAT_ENAMEL, collection, computer, rotation=(math.radians(4), 0, 0), bevel=0.025)
    for row in range(3):
        for column in range(9):
            cube("care_computer_key", (-0.30 + column * 0.075, -0.54 + row * 0.075, 0.088), (0.052, 0.050, 0.018), MAT_INK, collection, computer, bevel=0.005)
    curve("care_computer_power_cable", [(0.34, 0.20, 0.15), (0.55, 0.32, 0.02), (0.70, 0.32, -0.42)], 0.012, MAT_INK, collection, computer)


def run():
    old_clock = bpy.data.objects.get("interaction_old_wall_clock")
    if old_clock:
        remove_tree(old_clock)
        bpy.data.objects.remove(old_clock, do_unlink=True)

    # Rules and their decorative clipboard were removed from the game design.
    for obsolete_name in ("night_rules_sheet", "interaction_night_clipboard"):
        obsolete = bpy.data.objects.get(obsolete_name)
        if obsolete:
            remove_tree(obsolete)
            bpy.data.objects.remove(obsolete, do_unlink=True)

    emergency_button = bpy.data.objects.get("interaction_emergency_button")
    if emergency_button:
        emergency_button.location = (-1.0, 1.405, 1.34)
        emergency_button.rotation_euler = (0.0, 0.0, 0.0)

    # Replace the old baked cart completely; moving its offset origin caused it
    # to drift into the couch and doorway.
    old_cart = bpy.data.objects.get("interaction_medical_cart")
    if old_cart:
        remove_tree(old_cart)
        bpy.data.objects.remove(old_cart, do_unlink=True)

    old_collection = bpy.data.collections.get(COLLECTION_NAME)
    if old_collection:
        for obj in list(old_collection.all_objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old_collection)
    collection = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(collection)

    rebuilt = rebuild_patients()

    build_props(collection)
    bpy.context.scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"CARE_GAMEPLAY_V2 patients={rebuilt} props={len(collection.all_objects)} clock_removed={old_clock is not None} cart_rebuilt=True")


PATIENTS = (
    ("ward_1_bed_1_patient_v3", "morozov", "Морозов И. П.", 0),
    ("ward_2_bed_1_patient_v3", "levchenko", "Левченко А. Н.", 1),
    ("ward_3_bed_1_patient_v3", "orlova", "Орлова Н. Д.", 2),
    ("ward_4_bed_1_patient_v3", "saveliev", "Савельев П. М.", 3),
    ("ward_5_bed_1_patient_v3", "demina", "Демина В. Р.", 4),
    ("ward_6_bed_1_patient_v3", "yudin", "Юдин С. К.", 5),
    ("ward_6_bed_2_patient_v3", "klimova", "Климова Т. С.", 6),
)


def rebuild_patients():
    """Rebuild only the 7 bedridden patients - not props, cart or signage.

    Kept separate from run() so a face-only pass (see
    tools/rebuild_ward_patient_faces.py) never touches interaction_medical_cart,
    the clock, or the 15 build_props() objects that main.gd binds by name.
    """
    rebuilt = 0
    for object_name, patient_id, display_name, variant in PATIENTS:
        root = bpy.data.objects.get(object_name)
        if root:
            build_patient(root, patient_id, display_name, variant)
            rebuilt += 1
    return rebuilt


# The Blender MCP addon execs scripts with a bare globals dict (`{"bpy": bpy}`),
# so `__name__` resolves to "builtins", not "__main__". An `if __name__ ==
# "__main__"` guard here would never fire and running this file the documented
# way would silently do nothing. Drivers that want only the builder functions
# set CARE_GAMEPLAY_LIBRARY_ONLY in the exec globals instead.
if not globals().get("CARE_GAMEPLAY_LIBRARY_ONLY"):
    run()
