import bpy
import math


def rebuild_orderly():
    for collection_name in (
        "ASSET_orderly_anomaly_v3",
        "ASSET_orderly_ghost_v4",
        "ASSET_orderly_ghost_v5",
    ):
        collection = bpy.data.collections.get(collection_name)
        if collection:
            for obj in list(collection.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(collection)

    collection = bpy.data.collections.new("ASSET_orderly_ghost_v5")
    bpy.context.scene.collection.children.link(collection)

    def material(name, base, dark, roughness=0.88, metallic=0.0, alpha=1.0):
        mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        mat.diffuse_color = (*base, alpha)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        output = nodes.new("ShaderNodeOutputMaterial")
        shader = nodes.new("ShaderNodeBsdfPrincipled")
        shader.inputs["Roughness"].default_value = roughness
        shader.inputs["Metallic"].default_value = metallic
        shader.inputs["Alpha"].default_value = alpha
        coords = nodes.new("ShaderNodeTexCoord")
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 7.0
        noise.inputs["Detail"].default_value = 4.5
        noise.inputs["Roughness"].default_value = 0.76
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.24
        ramp.color_ramp.elements[0].color = (*dark, 1.0)
        ramp.color_ramp.elements[1].position = 0.82
        ramp.color_ramp.elements[1].color = (*base, 1.0)
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.08
        bump.inputs["Distance"].default_value = 0.035
        links.new(coords.outputs["Generated"], noise.inputs["Vector"])
        links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], shader.inputs["Normal"])
        links.new(shader.outputs["BSDF"], output.inputs["Surface"])
        if alpha < 1.0:
            try:
                mat.surface_render_method = "DITHERED"
            except Exception:
                pass
        return mat

    uniform_mat = material(
        "MAT_orderly_v5_old_uniform", (0.20, 0.255, 0.235), (0.045, 0.060, 0.050), 0.95
    )
    apron_mat = material(
        "MAT_orderly_v5_old_apron", (0.41, 0.425, 0.38), (0.085, 0.090, 0.065), 0.97
    )
    hood_mat = material(
        "MAT_orderly_v5_grey_hood", (0.18, 0.205, 0.19), (0.025, 0.032, 0.027), 0.97
    )
    void_mat = material(
        "MAT_orderly_v5_face_void", (0.008, 0.010, 0.009), (0.001, 0.002, 0.001), 0.76
    )
    # The opening is a literal black void, not skin, a mask, or a hinted face.
    void_nodes = void_mat.node_tree.nodes
    void_ramp = next(node for node in void_nodes if node.bl_idname == "ShaderNodeValToRGB")
    for element in void_ramp.color_ramp.elements:
        element.color = (0.001, 0.001, 0.001, 1.0)
    void_shader = next(node for node in void_nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    void_shader.inputs["Roughness"].default_value = 1.0
    if void_shader.inputs.get("Specular IOR Level"):
        void_shader.inputs["Specular IOR Level"].default_value = 0.0
    for link in list(void_mat.node_tree.links):
        if link.to_node == void_shader and link.to_socket.name == "Normal":
            void_mat.node_tree.links.remove(link)
    eye_glow_mat = bpy.data.materials.get("MAT_orderly_v5_eye_glow") or bpy.data.materials.new(
        "MAT_orderly_v5_eye_glow"
    )
    eye_glow_mat.diffuse_color = (0.24, 0.012, 0.002, 1.0)
    eye_glow_mat.use_nodes = True
    eye_nodes = eye_glow_mat.node_tree.nodes
    eye_links = eye_glow_mat.node_tree.links
    eye_nodes.clear()
    eye_output = eye_nodes.new("ShaderNodeOutputMaterial")
    eye_emission = eye_nodes.new("ShaderNodeEmission")
    eye_emission.inputs["Color"].default_value = (0.42, 0.018, 0.002, 1.0)
    eye_emission.inputs["Strength"].default_value = 5.0
    eye_links.new(eye_emission.outputs["Emission"], eye_output.inputs["Surface"])
    hand_mat = material(
        "MAT_orderly_v5_grey_hands", (0.25, 0.275, 0.25), (0.070, 0.080, 0.068), 0.84
    )
    shoe_mat = material(
        "MAT_orderly_v5_black_shoes", (0.025, 0.029, 0.025), (0.004, 0.006, 0.004), 0.98
    )
    metal_mat = material(
        "MAT_orderly_v5_worn_metal", (0.18, 0.20, 0.19), (0.030, 0.038, 0.034), 0.50, 0.62
    )
    bucket_mat = material(
        "MAT_orderly_v5_blue_bucket", (0.014, 0.052, 0.135), (0.004, 0.010, 0.026), 0.52, 0.24
    )
    rust_mat = material(
        "MAT_orderly_v5_rust", (0.23, 0.052, 0.014), (0.050, 0.010, 0.003), 0.92
    )
    mist_mat = material(
        "MAT_orderly_v5_mist", (0.16, 0.21, 0.19), (0.030, 0.045, 0.035), 0.82, alpha=0.22
    )

    def move_to_collection(obj):
        for owner in list(obj.users_collection):
            owner.objects.unlink(obj)
        collection.objects.link(obj)

    def empty(name, location=(0.0, 0.0, 0.0), parent=None):
        obj = bpy.data.objects.new(name, None)
        collection.objects.link(obj)
        obj.parent = parent
        obj.location = location
        obj.empty_display_type = "PLAIN_AXES"
        obj.empty_display_size = 0.07
        return obj

    def finish(obj, name, parent, location, mat=None, rotation=(0.0, 0.0, 0.0), smooth=True, bevel=0.0):
        move_to_collection(obj)
        obj.name = name
        obj.parent = parent
        obj.location = location
        obj.rotation_euler = rotation
        if mat and hasattr(obj.data, "materials"):
            obj.data.materials.append(mat)
        if smooth and obj.type == "MESH":
            for polygon in obj.data.polygons:
                polygon.use_smooth = True
        if bevel:
            modifier = obj.modifiers.new("soft_edges", "BEVEL")
            modifier.width = bevel
            modifier.segments = 3
        return obj

    def sphere(name, location, scale, mat, parent, rotation=(0.0, 0.0, 0.0), segments=28):
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=segments, ring_count=max(14, segments // 2), location=(0.0, 0.0, 0.0)
        )
        obj = bpy.context.object
        obj.scale = scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        return finish(obj, name, parent, location, mat, rotation)

    def cylinder(name, location, radius, depth, mat, parent, rotation=(0.0, 0.0, 0.0), vertices=24):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=vertices, radius=radius, depth=depth, location=(0.0, 0.0, 0.0)
        )
        return finish(bpy.context.object, name, parent, location, mat, rotation, True, 0.005)

    def cone(name, location, radius_bottom, radius_top, depth, mat, parent, rotation=(0.0, 0.0, 0.0), vertices=24):
        bpy.ops.mesh.primitive_cone_add(
            vertices=vertices,
            radius1=radius_bottom,
            radius2=radius_top,
            depth=depth,
            location=(0.0, 0.0, 0.0),
        )
        return finish(bpy.context.object, name, parent, location, mat, rotation, True, 0.006)

    def cube(name, location, dimensions, mat, parent, rotation=(0.0, 0.0, 0.0), bevel=0.01):
        bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, 0.0))
        obj = bpy.context.object
        obj.scale = (dimensions[0] / 2.0, dimensions[1] / 2.0, dimensions[2] / 2.0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        return finish(obj, name, parent, location, mat, rotation, False, bevel)

    def pipe(name, points, radius, mat, parent):
        curve = bpy.data.curves.new(name + "_curve", "CURVE")
        curve.dimensions = "3D"
        curve.resolution_u = 3
        curve.bevel_depth = radius
        curve.bevel_resolution = 3
        spline = curve.splines.new("BEZIER")
        spline.bezier_points.add(len(points) - 1)
        for point, coordinate in zip(spline.bezier_points, points):
            point.co = coordinate
            point.handle_left_type = "AUTO"
            point.handle_right_type = "AUTO"
        curve.materials.append(mat)
        obj = bpy.data.objects.new(name, curve)
        collection.objects.link(obj)
        obj.parent = parent
        return obj

    def oval_pipe(name, center_x, radius_y, radius_z, tube_radius, mat, parent, points=32):
        curve = bpy.data.curves.new(name + "_curve", "CURVE")
        curve.dimensions = "3D"
        curve.resolution_u = 2
        curve.bevel_depth = tube_radius
        curve.bevel_resolution = 3
        spline = curve.splines.new("BEZIER")
        spline.bezier_points.add(points - 1)
        for index, point in enumerate(spline.bezier_points):
            angle = 2.0 * math.pi * index / points
            point.co = (center_x, radius_y * math.cos(angle), radius_z * math.sin(angle))
            point.handle_left_type = "AUTO"
            point.handle_right_type = "AUTO"
        spline.use_cyclic_u = True
        curve.materials.append(mat)
        obj = bpy.data.objects.new(name, curve)
        collection.objects.link(obj)
        obj.parent = parent
        return obj

    def tapered_limb(name, rings, mat, parent, segments=20):
        """Build an organic vertical limb from elliptical anatomical cross-sections."""
        vertices = []
        faces = []
        for center_x, center_y, center_z, radius_x, radius_y in rings:
            for index in range(segments):
                angle = 2.0 * math.pi * index / segments
                vertices.append(
                    (
                        center_x + radius_x * math.cos(angle),
                        center_y + radius_y * math.sin(angle),
                        center_z,
                    )
                )
        for ring_index in range(len(rings) - 1):
            start = ring_index * segments
            next_start = (ring_index + 1) * segments
            for index in range(segments):
                following = (index + 1) % segments
                faces.append((start + index, start + following, next_start + following, next_start + index))
        faces.append(tuple(reversed(range(segments))))
        last = (len(rings) - 1) * segments
        faces.append(tuple(last + index for index in range(segments)))
        mesh = bpy.data.meshes.new(name + "_mesh")
        mesh.from_pydata(vertices, [], faces)
        mesh.materials.append(mat)
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        obj.parent = parent
        return obj

    def torus(name, location, major_radius, minor_radius, mat, parent):
        bpy.ops.mesh.primitive_torus_add(
            major_radius=major_radius,
            minor_radius=minor_radius,
            major_segments=32,
            minor_segments=8,
            location=(0.0, 0.0, 0.0),
        )
        return finish(bpy.context.object, name, parent, location, mat)

    def ribbon(name, points, width, mat, parent):
        vertices = []
        faces = []
        for index, point in enumerate(points):
            vertices.extend(
                ((point[0], point[1] - width, point[2]), (point[0], point[1] + width, point[2]))
            )
            if index:
                start = (index - 1) * 2
                faces.append((start, start + 1, index * 2 + 1, index * 2))
        mesh = bpy.data.meshes.new(name + "_mesh")
        mesh.from_pydata(vertices, [], faces)
        mesh.materials.append(mat)
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        obj.parent = parent
        solidify = obj.modifiers.new("cloth_thickness", "SOLIDIFY")
        solidify.thickness = 0.004
        return obj

    def fitted_uniform(name, parent):
        levels = (
            (0.12, 0.15, 0.255),
            (0.28, 0.17, 0.285),
            (0.56, 0.17, 0.280),
            (0.84, 0.15, 0.225),
            (1.06, 0.15, 0.225),
            (1.24, 0.16, 0.270),
            (1.34, 0.145, 0.295),
            (1.40, 0.11, 0.175),
        )
        segments = 32
        vertices = []
        faces = []
        for ring, (height, depth, width) in enumerate(levels):
            for index in range(segments):
                angle = 2.0 * math.pi * index / segments
                hem = 0.045 * (0.5 + 0.5 * math.sin(angle * 5.0 + 0.7)) if ring == 0 else 0.0
                vertices.append(
                    (
                        depth * math.cos(angle) * (1.0 + 0.02 * math.sin(angle * 3.0 + ring)),
                        width * math.sin(angle),
                        height + hem,
                    )
                )
        for ring in range(len(levels) - 1):
            for index in range(segments):
                nxt = (index + 1) % segments
                faces.append(
                    (
                        ring * segments + index,
                        ring * segments + nxt,
                        (ring + 1) * segments + nxt,
                        (ring + 1) * segments + index,
                    )
                )
        faces.append(tuple((len(levels) - 1) * segments + index for index in range(segments)))
        mesh = bpy.data.meshes.new(name + "_mesh")
        mesh.from_pydata(vertices, [], faces)
        mesh.materials.append(uniform_mat)
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        obj.parent = parent
        modifier = obj.modifiers.new("uniform_cloth", "SOLIDIFY")
        modifier.thickness = 0.012
        return obj

    def apron(name, parent):
        rows = ((0.43, 0.23, 0.175), (0.66, 0.25, 0.188), (0.90, 0.22, 0.174), (1.18, 0.17, 0.17))
        columns = 11
        vertices = []
        faces = []
        for row, (height, half_width, front) in enumerate(rows):
            for index in range(columns):
                fraction = index / (columns - 1)
                y = -half_width + 2.0 * half_width * fraction
                x = front - 0.032 * (y / half_width) ** 2
                z = height + (0.018 * math.sin(fraction * math.pi * 5.0) if row == 0 else 0.0)
                vertices.append((x, y, z))
        for row in range(len(rows) - 1):
            for index in range(columns - 1):
                start = row * columns + index
                faces.append((start, start + 1, start + 1 + columns, start + columns))
        mesh = bpy.data.meshes.new(name + "_mesh")
        mesh.from_pydata(vertices, [], faces)
        mesh.materials.append(apron_mat)
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        obj.parent = parent
        modifier = obj.modifiers.new("apron_thickness", "SOLIDIFY")
        modifier.thickness = 0.008
        return obj

    def hood_shell(name, parent):
        latitude_count = 20
        longitude_count = 36
        vertices = []
        faces = []
        for latitude in range(latitude_count + 1):
            phi = -math.pi / 2.0 + math.pi * latitude / latitude_count
            for longitude in range(longitude_count):
                theta = 2.0 * math.pi * longitude / longitude_count
                z = 0.225 * math.sin(phi)
                vertical = (z + 0.225) / 0.45
                skull_width = 0.82 + 0.18 * math.sin(math.pi * vertical)
                vertices.append(
                    (
                        -0.018 + 0.158 * math.cos(phi) * math.cos(theta) - 0.012 * vertical,
                        0.148 * skull_width * math.cos(phi) * math.sin(theta),
                        z,
                    )
                )
        for latitude in range(latitude_count):
            for longitude in range(longitude_count):
                nxt = (longitude + 1) % longitude_count
                indices = (
                    latitude * longitude_count + longitude,
                    latitude * longitude_count + nxt,
                    (latitude + 1) * longitude_count + nxt,
                    (latitude + 1) * longitude_count + longitude,
                )
                center_x = sum(vertices[index][0] for index in indices) / 4.0
                center_y = sum(vertices[index][1] for index in indices) / 4.0
                center_z = sum(vertices[index][2] for index in indices) / 4.0
                opening = (center_y / 0.102) ** 2 + ((center_z + 0.006) / 0.154) ** 2
                if center_x > 0.018 and opening < 1.0:
                    continue
                faces.append(indices)
        mesh = bpy.data.meshes.new(name + "_mesh")
        mesh.from_pydata(vertices, [], faces)
        mesh.materials.append(hood_mat)
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        obj.parent = parent
        modifier = obj.modifiers.new("hood_cloth", "SOLIDIFY")
        modifier.thickness = 0.010
        return obj

    def hood_drape(name, parent):
        rows = (
            (-0.125, -0.115, 0.070),
            (-0.205, -0.145, 0.135),
            (-0.310, -0.165, 0.235),
            (-0.405, -0.145, 0.300),
        )
        columns = 13
        vertices = []
        faces = []
        for row_index, (z, x, half_width) in enumerate(rows):
            for column in range(columns):
                fraction = column / (columns - 1)
                y = -half_width + 2.0 * half_width * fraction
                fold = 0.010 * math.sin(fraction * math.pi * 4.0 + row_index * 0.7)
                vertices.append((x + fold, y, z + 0.008 * math.cos(fraction * math.pi * 3.0)))
        for row_index in range(len(rows) - 1):
            for column in range(columns - 1):
                start = row_index * columns + column
                faces.append((start, start + 1, start + 1 + columns, start + columns))
        mesh = bpy.data.meshes.new(name + "_mesh")
        mesh.from_pydata(vertices, [], faces)
        mesh.materials.append(hood_mat)
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        obj.parent = parent
        solidify = obj.modifiers.new("drape_cloth", "SOLIDIFY")
        solidify.thickness = 0.009
        return obj

    root = empty("orderly_anomaly_v5")
    root["asset_type"] = "walking_featureless_orderly"
    root["face"] = "black_void"
    root["version"] = 5
    body = empty("ghost_body_pivot", parent=root)
    body.rotation_euler.y = math.radians(-3.0)
    fitted_uniform("ghost_fitted_uniform", body)
    apron("ghost_old_apron", body)
    cube("ghost_apron_pocket", (0.18, 0.09, 0.76), (0.014, 0.17, 0.14), apron_mat, body)
    for index, height in enumerate((1.16, 1.05, 0.94)):
        sphere("ghost_small_button_%d" % index, (0.176, 0.0, height), (0.010, 0.013, 0.013), metal_mat, body)
    pipe("ghost_apron_neck_loop", ((0.15, -0.14, 1.18), (0.13, 0.0, 1.34), (0.15, 0.14, 1.18)), 0.008, apron_mat, body)
    # The old three rigid trail ribbons looked like rods growing from the hem.
    # Motion is conveyed by the walk cycle and fog instead.

    head = empty("ghost_head_pivot", (-0.005, 0.0, 1.585), body)
    head.rotation_euler.y = math.radians(-12.0)
    hood_shell("ghost_anatomical_hood", head)
    hood_drape("ghost_hood_shoulder_drape", head)
    sphere(
        "ghost_hood_neck_fold",
        (-0.040, 0.0, -0.205),
        (0.135, 0.175, 0.090),
        hood_mat,
        head,
        segments=28,
    )
    sphere(
        "ghost_featureless_face_void",
        (0.045, 0.0, -0.006),
        (0.010, 0.098, 0.149),
        void_mat,
        head,
        segments=36,
    )
    oval_pipe("ghost_hood_face_rim", 0.060, 0.106, 0.158, 0.011, hood_mat, head, 36)
    sphere(
        "ghost_glowing_eye_left",
        (0.057, 0.035, 0.032),
        (0.006, 0.012, 0.008),
        eye_glow_mat,
        head,
        (0.0, math.radians(-4.0), math.radians(5.0)),
        18,
    )
    sphere(
        "ghost_glowing_eye_right",
        (0.057, -0.034, 0.024),
        (0.006, 0.010, 0.007),
        eye_glow_mat,
        head,
        (0.0, math.radians(5.0), math.radians(-7.0)),
        18,
    )

    # A real shoulder line: a soft upper-torso mass plus two uneven shoulder caps.
    # The asymmetry and slight drop make the silhouette feel human and exhausted.
    sphere("ghost_upper_torso_shoulder_mass", (0.0, 0.0, 1.30), (0.110, 0.270, 0.130), uniform_mat, body)
    arm_pivots = {}
    for side, y, shoulder_z, lean, droop in (
        ("l", 0.255, 1.265, 0.018, -4.0),
        ("r", -0.270, 1.215, -0.012, 7.0),
    ):
        sphere(
            "ghost_%s_shoulder_cap" % side,
            (0.0, y, shoulder_z),
            (0.092, 0.105, 0.115),
            uniform_mat,
            body,
            (0.0, math.radians(droop), 0.0),
        )
        pivot = empty("ghost_%s_arm_pivot" % side, (0.0, y, shoulder_z), body)
        pivot.rotation_euler.x = math.radians(droop)
        arm_pivots[side] = pivot
        tapered_limb(
            "ghost_%s_anatomical_sleeve" % side,
            (
                (0.000, 0.0, -0.015, 0.085, 0.078),
                (lean * 0.35, 0.0, -0.105, 0.079, 0.071),
                (lean, 0.0, -0.235, 0.068, 0.060),
                (0.030 + lean, 0.0, -0.335, 0.060, 0.052),
            ),
            uniform_mat,
            pivot,
        )
        sphere(
            "ghost_%s_elbow" % side,
            (0.033 + lean, 0.0, -0.345),
            (0.057, 0.052, 0.061),
            hand_mat,
            pivot,
            segments=20,
        )
        tapered_limb(
            "ghost_%s_anatomical_forearm" % side,
            (
                (0.035 + lean, 0.0, -0.335, 0.050, 0.047),
                (0.053 + lean, 0.0, -0.425, 0.046, 0.042),
                (0.070 + lean, 0.0, -0.535, 0.037, 0.035),
                (0.073 + lean, 0.0, -0.595, 0.030, 0.029),
            ),
            hand_mat,
            pivot,
            18,
        )
        torus("ghost_%s_frayed_cuff" % side, (0.032 + lean, 0.0, -0.326), 0.058, 0.006, uniform_mat, pivot)
        sphere(
            "ghost_%s_wrist" % side,
            (0.076 + lean, 0.0, -0.610),
            (0.034, 0.031, 0.047),
            hand_mat,
            pivot,
            segments=20,
        )
        sphere(
            "ghost_%s_palm" % side,
            (0.086 + lean, 0.0, -0.682),
            (0.050, 0.046, 0.079),
            hand_mat,
            pivot,
            (0.0, math.radians(4.0), 0.0),
            24,
        )
        finger_lengths = (0.102, 0.121, 0.116, 0.095)
        for finger, length in enumerate(finger_lengths):
            finger_y = (finger - 1.5) * 0.022
            start_z = -0.733 - abs(finger - 1.5) * 0.004
            pipe(
                "ghost_%s_finger_%d" % (side, finger),
                (
                    (0.091 + lean, finger_y, start_z),
                    (0.104 + lean, finger_y, start_z - length * 0.42),
                    (0.112 + lean, finger_y, start_z - length * 0.76),
                    (0.108 + lean, finger_y, start_z - length),
                ),
                0.0073 - abs(finger - 1.5) * 0.0006,
                hand_mat,
                pivot,
            )
            sphere(
                "ghost_%s_fingertip_%d" % (side, finger),
                (0.108 + lean, finger_y, start_z - length),
                (0.0078, 0.0072, 0.0085),
                hand_mat,
                pivot,
                segments=12,
            )
        thumb_side = -1.0 if side == "l" else 1.0
        pipe(
            "ghost_%s_thumb" % side,
            (
                (0.095 + lean, thumb_side * 0.036, -0.662),
                (0.110 + lean, thumb_side * 0.054, -0.694),
                (0.118 + lean, thumb_side * 0.061, -0.731),
                (0.111 + lean, thumb_side * 0.057, -0.752),
            ),
            0.009,
            hand_mat,
            pivot,
        )
        sphere(
            "ghost_%s_thumb_tip" % side,
            (0.111 + lean, thumb_side * 0.057, -0.752),
            (0.0095, 0.0090, 0.0105),
            hand_mat,
            pivot,
            segments=12,
        )

    leg_pivots = {}
    for side, y in (("l", 0.11), ("r", -0.11)):
        pivot = empty("ghost_%s_leg_pivot" % side, (0.0, y, 0.48), root)
        leg_pivots[side] = pivot
        cone("ghost_%s_ankle" % side, (0.0, 0.0, -0.16), 0.040, 0.048, 0.32, hand_mat, pivot)
        sphere("ghost_%s_shoe" % side, (0.078, 0.0, -0.34), (0.15, 0.075, 0.047), shoe_mat, pivot, (0.0, 0.03, 0.0), 20)

    # Keep the bucket in the right hand.  The pivot is a child of the rigid
    # arm assembly so the grip stays locked to the palm throughout the walk.
    # A slightly outward offset keeps the bucket clear of the coat hem.
    bucket = empty("ghost_bucket_pivot", (0.074, -0.13, -1.257), arm_pivots["r"])
    cone("ghost_blue_bucket_body", (0.0, 0.0, 0.23), 0.16, 0.20, 0.34, bucket_mat, bucket, vertices=30)
    cylinder("ghost_blue_bucket_inner", (0.0, 0.0, 0.395), 0.176, 0.018, void_mat, bucket, vertices=30)
    torus("ghost_blue_bucket_rim", (0.0, 0.0, 0.402), 0.185, 0.011, metal_mat, bucket)
    pipe(
        "ghost_blue_bucket_handle",
        ((0.0, -0.185, 0.39), (0.0, -0.105, 0.55), (0.0, 0.13, 0.65), (0.0, 0.185, 0.55), (0.0, 0.185, 0.39)),
        0.009,
        metal_mat,
        bucket,
    )
    cylinder("ghost_blue_bucket_grip", (0.0, 0.13, 0.65), 0.018, 0.13, void_mat, bucket, (math.pi / 2.0, 0.0, 0.0), 18)
    sphere("ghost_bucket_rust", (0.162, -0.055, 0.21), (0.009, 0.036, 0.029), rust_mat, bucket, segments=18)

    for pivot, sequence in (
        (leg_pivots["l"], (-12.0, 12.0, -12.0)),
        (leg_pivots["r"], (12.0, -12.0, 12.0)),
        (arm_pivots["l"], (8.0, -8.0, 8.0)),
        (arm_pivots["r"], (-3.0, 4.0, -3.0)),
    ):
        for frame, angle in ((1, sequence[0]), (17, sequence[1]), (33, sequence[2])):
            pivot.rotation_euler.y = math.radians(angle)
            pivot.keyframe_insert("rotation_euler", index=1, frame=frame, group="Walk")
    for frame, height in ((1, 0.0), (9, 0.016), (17, 0.0), (25, 0.016), (33, 0.0)):
        body.location.z = height
        body.keyframe_insert("location", index=2, frame=frame, group="Walk")

    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 32
    scene.frame_set(8)
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    for obj in (root, *root.children_recursive):
        obj.hide_viewport = False
        obj.hide_render = False
        obj.hide_set(False)
        obj.select_set(True)
    bpy.context.view_layer.objects.active = root
    for child_collection in scene.collection.children:
        child_collection.hide_viewport = child_collection != collection
    collection.hide_viewport = False
    bpy.ops.wm.save_as_mainfile(filepath=r"C:\palata\palata_zero.blend")

    def focus_viewports():
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type != "VIEW_3D":
                    continue
                area.spaces.active.shading.type = "MATERIAL"
                region = next((item for item in area.regions if item.type == "WINDOW"), None)
                if region:
                    try:
                        with bpy.context.temp_override(window=window, area=area, region=region):
                            bpy.ops.view3d.view_selected(use_all_regions=False)
                    except Exception:
                        pass
        return None

    bpy.app.timers.register(focus_viewports, first_interval=0.7)


rebuild_orderly()
