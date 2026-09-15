import bpy


BLEND_PATH = "C:/palata/palata_zero.blend"
GLB_PATH = "C:/palata/palata_zero.glb"
ASSET_COLLECTIONS = {"ASSET_orderly_ghost_v5", "ASSET_violent_patient_v1"}


def reset_material(name, color, roughness):
    material = bpy.data.materials.get(name)
    if material is None:
        return False
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return True


fixed = 0
fixed += reset_material("MAT_patient_skin_natural", (0.43, 0.30, 0.22), 0.94)
fixed += reset_material("MAT_patient_skin_pale", (0.36, 0.31, 0.25), 0.95)
fixed += reset_material("MAT_patient_lips_natural", (0.24, 0.105, 0.085), 0.90)
fixed += reset_material("MAT_patient_ink_dark", (0.025, 0.018, 0.012), 0.96)
fixed += reset_material("MAT_patient_hair", (0.025, 0.018, 0.011), 0.98)
fixed += reset_material("MAT_assignment_board_green", (0.10, 0.18, 0.13), 0.97)

original_visibility = {collection.name: collection.hide_viewport for collection in bpy.context.scene.collection.children}
for collection in bpy.context.scene.collection.children:
    collection.hide_viewport = collection.name in ASSET_COLLECTIONS

for obj in bpy.context.view_layer.objects:
    obj.select_set(False)
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
print("PATIENT_MATERIALS_FIXED", fixed)
