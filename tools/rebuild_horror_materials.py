import bpy


BLEND_PATH = "C:/palata/palata_zero.blend"
GLB_PATH = "C:/palata/palata_zero.glb"
ASSET_COLLECTIONS = {"ASSET_orderly_ghost_v5", "ASSET_violent_patient_v1"}


def is_special(name):
    tokens = (
        "glass", "water", "screen", "emiss", "glow", "eye", "fluorescent",
        "warm_bulb", "night_outside", "monitor_trace", "mist",
        "patient_skin", "patient_lips", "patient_ink", "patient_hair",
        "assignment_board",
    )
    return any(token in name for token in tokens)


def category_for(name):
    if any(token in name for token in ("whitewash", "oil_paint_green", "repainted_mint", "wall_repair", "ceiling", "skirting")):
        return "wall"
    if any(token in name for token in ("linoleum", "worn_floor", "wheel_scuff", "marble", "stone")):
        return "floor"
    if any(token in name for token in ("painted_wood", "offwhite")):
        return "painted_wood"
    if any(token in name for token in ("veneer", "old_dsp", "tv_dark_wood", "wood")):
        return "wood"
    if any(token in name for token in ("linen", "blanket", "vinyl", "gown", "apron", "scarf", "bandage", "curtain", "towel", "robe", "cloth", "fabric", "uniform", "hood")):
        return "fabric"
    if any(token in name for token in ("metal", "chrome", "steel", "iron", "bucket", "pipe", "hinge", "rust", "enamel", "lamp_housing")):
        return "metal"
    if any(token in name for token in ("ceramic", "porcelain", "square_tile")):
        return "ceramic"
    if any(token in name for token in ("paper", "label", "coffee")):
        return "paper"
    return "generic"


def colors_for(name, category):
    if category == "wall":
        if "green" in name or "mint" in name or "repair" in name:
            return ((0.075, 0.17, 0.105, 1), (0.19, 0.31, 0.22, 1), (0.28, 0.39, 0.29, 1), (0.035, 0.055, 0.035, 1))
        if "skirting" in name:
            return ((0.025, 0.065, 0.04, 1), (0.075, 0.15, 0.095, 1), (0.13, 0.22, 0.15, 1), (0.018, 0.026, 0.018, 1))
        return ((0.12, 0.13, 0.095, 1), (0.43, 0.44, 0.35, 1), (0.64, 0.63, 0.51, 1), (0.055, 0.062, 0.042, 1))
    if category == "floor":
        return ((0.045, 0.052, 0.041, 1), (0.20, 0.23, 0.19, 1), (0.48, 0.48, 0.40, 1), (0.70, 0.68, 0.56, 1))
    if category == "painted_wood":
        return ((0.18, 0.075, 0.025, 1), (0.37, 0.36, 0.28, 1), (0.67, 0.65, 0.53, 1), (0.77, 0.74, 0.61, 1))
    if category == "wood":
        return ((0.055, 0.018, 0.006, 1), (0.15, 0.06, 0.018, 1), (0.31, 0.15, 0.045, 1), (0.43, 0.24, 0.08, 1))
    if category == "fabric":
        if "blue" in name:
            return ((0.025, 0.045, 0.06, 1), (0.08, 0.14, 0.17, 1), (0.18, 0.25, 0.26, 1), (0.28, 0.32, 0.29, 1))
        if "rose" in name or "red" in name:
            return ((0.07, 0.025, 0.02, 1), (0.18, 0.08, 0.065, 1), (0.33, 0.17, 0.14, 1), (0.39, 0.29, 0.21, 1))
        return ((0.03, 0.048, 0.035, 1), (0.10, 0.17, 0.12, 1), (0.23, 0.30, 0.23, 1), (0.36, 0.38, 0.29, 1))
    if category == "metal":
        if "red" in name or "warning" in name or "hot" in name:
            return ((0.07, 0.008, 0.004, 1), (0.31, 0.018, 0.009, 1), (0.49, 0.055, 0.025, 1), (0.18, 0.055, 0.015, 1))
        if "blue" in name or "bucket" in name or "cold" in name:
            return ((0.012, 0.035, 0.055, 1), (0.025, 0.11, 0.17, 1), (0.08, 0.22, 0.28, 1), (0.22, 0.07, 0.018, 1))
        return ((0.035, 0.045, 0.037, 1), (0.15, 0.18, 0.15, 1), (0.34, 0.36, 0.31, 1), (0.28, 0.075, 0.018, 1))
    if category == "ceramic":
        return ((0.15, 0.13, 0.075, 1), (0.48, 0.46, 0.35, 1), (0.72, 0.69, 0.55, 1), (0.31, 0.24, 0.10, 1))
    if category == "paper":
        return ((0.11, 0.075, 0.025, 1), (0.40, 0.31, 0.15, 1), (0.69, 0.60, 0.37, 1), (0.79, 0.72, 0.50, 1))
    if "skin" in name or "hands" in name:
        return ((0.08, 0.045, 0.03, 1), (0.31, 0.20, 0.14, 1), (0.52, 0.38, 0.27, 1), (0.62, 0.50, 0.37, 1))
    if "black" in name or "rubber" in name or "hair" in name or "ink" in name or "dark" in name:
        return ((0.004, 0.004, 0.003, 1), (0.015, 0.016, 0.013, 1), (0.045, 0.046, 0.038, 1), (0.08, 0.075, 0.058, 1))
    if "red" in name or "warning" in name:
        return ((0.055, 0.004, 0.002, 1), (0.24, 0.012, 0.006, 1), (0.47, 0.04, 0.018, 1), (0.18, 0.025, 0.008, 1))
    if "blue" in name:
        return ((0.01, 0.025, 0.04, 1), (0.025, 0.09, 0.15, 1), (0.09, 0.19, 0.25, 1), (0.19, 0.24, 0.23, 1))
    return ((0.025, 0.027, 0.021, 1), (0.13, 0.14, 0.105, 1), (0.30, 0.30, 0.23, 1), (0.42, 0.39, 0.27, 1))


def rebuild_nodes(material, category, palette):
    material.use_nodes = True
    material.diffuse_color = palette[2]
    tree = material.node_tree
    tree.nodes.clear()

    output = tree.nodes.new("ShaderNodeOutputMaterial")
    shader = tree.nodes.new("ShaderNodeBsdfPrincipled")
    texcoord = tree.nodes.new("ShaderNodeTexCoord")
    noise = tree.nodes.new("ShaderNodeTexNoise")
    ramp = tree.nodes.new("ShaderNodeValToRGB")
    bump = tree.nodes.new("ShaderNodeBump")

    output.location = (620, 0)
    shader.location = (350, 0)
    ramp.location = (80, 80)
    noise.location = (-180, 60)
    texcoord.location = (-410, 60)
    bump.location = (100, -180)

    settings = {
        "wall": (3.2, 5.0, 0.95, 0.18),
        "floor": (14.0, 2.4, 0.91, 0.24),
        "painted_wood": (5.0, 5.0, 0.86, 0.22),
        "wood": (6.5, 4.0, 0.78, 0.20),
        "fabric": (24.0, 2.0, 0.96, 0.12),
        "metal": (7.0, 4.5, 0.84, 0.27),
        "ceramic": (4.2, 3.0, 0.58, 0.09),
        "paper": (6.0, 3.5, 0.94, 0.10),
        "generic": (5.5, 3.5, 0.88, 0.16),
    }
    scale, detail, roughness, bump_strength = settings[category]
    noise.noise_dimensions = "3D"
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = detail
    noise.inputs["Roughness"].default_value = 0.72

    color_ramp = ramp.color_ramp
    color_ramp.elements.remove(color_ramp.elements[1])
    first = color_ramp.elements[0]
    first.position = 0.0
    first.color = palette[0]
    positions = (0.30, 0.58, 0.82)
    if category == "painted_wood":
        positions = (0.22, 0.28, 0.70)
    elif category == "floor":
        positions = (0.37, 0.58, 0.72)
    for position, color in zip(positions, palette[1:]):
        element = color_ramp.elements.new(position)
        element.color = color

    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = 0.18 if category == "metal" else 0.0
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.045 if category in ("wall", "floor", "painted_wood") else 0.022

    tree.links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    tree.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    tree.links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    tree.links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])


def assign_material(obj, material):
    obj.data.materials.clear()
    obj.data.materials.append(material)


def is_ward_door(name):
    return (
        name.startswith("hospital_door_")
        or name.startswith("doorframe_")
        or name.startswith("door_detail")
        or "anomaly_room_zero_door" in name
    )


def rebuild():
    door_material = bpy.data.materials.get("MAT_old_white_chipped_doors") or bpy.data.materials.new("MAT_old_white_chipped_doors")
    door_palette = (
        (0.15, 0.055, 0.015, 1),
        (0.39, 0.37, 0.27, 1),
        (0.67, 0.65, 0.53, 1),
        (0.78, 0.75, 0.62, 1),
    )
    rebuild_nodes(door_material, "painted_wood", door_palette)

    rebuilt = 0
    assigned_doors = 0
    missing = 0
    for material in list(bpy.data.materials):
        lower = material.name.lower()
        if material == door_material or is_special(lower) or "orderly_v5" in lower or "violent_patient" in lower:
            continue
        category = category_for(lower)
        rebuild_nodes(material, category, colors_for(lower, category))
        rebuilt += 1

    generic = bpy.data.materials.get("MAT_horror_generic")
    if not generic:
        generic = bpy.data.materials.new("MAT_horror_generic")
        rebuild_nodes(generic, "generic", colors_for("generic", "generic"))

    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        lower = obj.name.lower()
        if is_ward_door(lower):
            assign_material(obj, door_material)
            assigned_doors += 1
        elif len(obj.data.materials) == 0:
            assign_material(obj, generic)
            missing += 1

    original_visibility = {collection.name: collection.hide_viewport for collection in bpy.context.scene.collection.children}
    for collection in bpy.context.scene.collection.children:
        collection.hide_viewport = collection.name in ASSET_COLLECTIONS

    bpy.ops.object.select_all(action="DESELECT")
    for collection in bpy.context.scene.collection.children:
        if collection.name in ASSET_COLLECTIONS:
            continue
        for obj in collection.all_objects:
            if obj.type in {"MESH", "CURVE", "FONT", "EMPTY"}:
                obj.select_set(True)

    bpy.context.view_layer.objects.active = next((obj for obj in bpy.context.selected_objects if obj.type == "MESH"), None)
    bpy.ops.export_scene.gltf(
        filepath=GLB_PATH,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_cameras=False,
        export_lights=True,
    )

    for collection in bpy.context.scene.collection.children:
        collection.hide_viewport = original_visibility[collection.name]
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"HORROR_MATERIALS rebuilt={rebuilt} doors={assigned_doors} missing={missing}")


rebuild()
