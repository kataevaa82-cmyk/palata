import bpy


BLEND_PATH = "C:/palata/palata_zero.blend"
GLB_PATH = "C:/palata/palata_zero.glb"
EXCLUDED_COLLECTIONS = {
    "ASSET_orderly_ghost_v5",
    "ASSET_violent_patient_v1",
    "MODULE_LIBRARY",
    "ANOMALY_VARIANTS",
}
EXPORT_TYPES = {"MESH", "CURVE", "FONT", "EMPTY", "LIGHT"}


scene = bpy.context.scene
top_collections = list(scene.collection.children)
collection_state = {
    collection.name: (collection.hide_viewport, collection.hide_render)
    for collection in top_collections
}
excluded_objects = {
    obj
    for collection in top_collections
    if collection.name in EXCLUDED_COLLECTIONS
    for obj in collection.all_objects
    if obj is not None
}
export_objects = []
seen = set()
for collection in top_collections:
    if collection.name in EXCLUDED_COLLECTIONS:
        continue
    collection.hide_viewport = False
    collection.hide_render = False
    for obj in list(collection.all_objects):
        if obj is None or obj in excluded_objects or obj in seen or obj.type not in EXPORT_TYPES:
            continue
        export_objects.append(obj)
        seen.add(obj)

object_state = {
    obj.name: (obj.hide_viewport, obj.hide_render, obj.hide_get())
    for obj in export_objects
}
for obj in bpy.context.view_layer.objects:
    obj.select_set(False)
for obj in export_objects:
    obj.hide_viewport = False
    obj.hide_render = False
    obj.hide_set(False)
    obj.select_set(True)

active = next((obj for obj in export_objects if obj.type == "MESH"), None)
if active is None:
    raise RuntimeError("No mesh objects were selected for the hospital export")
bpy.context.view_layer.objects.active = active
bpy.context.view_layer.update()
bpy.ops.export_scene.gltf(
    filepath=GLB_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_cameras=False,
    export_lights=True,
    export_animations=True,
)

for obj in export_objects:
    old = object_state.get(obj.name)
    if old:
        obj.hide_viewport, obj.hide_render = old[:2]
        obj.hide_set(old[2])
for collection in top_collections:
    old = collection_state.get(collection.name)
    if old:
        collection.hide_viewport, collection.hide_render = old

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print(
    "MAIN_SCENE_EXPORTED",
    "objects=", len(export_objects),
    "meshes=", sum(obj.type == "MESH" for obj in export_objects),
    "lights=", sum(obj.type == "LIGHT" for obj in export_objects),
    "excluded=", sorted(EXCLUDED_COLLECTIONS),
    "path=", GLB_PATH,
)
