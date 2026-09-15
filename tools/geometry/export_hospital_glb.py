"""Export the hospital GLB from whichever blend is open, and save that same
blend back.

Deliberately not tools/export_main_scene_current.py: that one ends with
save_as_mainfile("C:/palata/palata_zero.blend") - a hardcoded path that is no
longer the file the hospital lives in. Running it from
hospital_models_work.blend would write the edits into the wrong file and leave
the working blend stale, which is how palata_zero.blend ended up holding 22
objects instead of the ward.
"""
import bpy

GLB_PATH = "C:/palata/palata_zero.glb"
EXPORT_TYPES = {"MESH", "CURVE", "FONT", "EMPTY", "LIGHT"}

scene = bpy.context.scene
skipped = bpy.data.collections.get("glTF_not_exported")
skipped_objects = set(skipped.all_objects) if skipped else set()

export_objects = [obj for obj in scene.objects
                  if obj.type in EXPORT_TYPES and obj not in skipped_objects]

for obj in bpy.context.view_layer.objects:
    obj.select_set(False)
for obj in export_objects:
    obj.hide_viewport = False
    obj.hide_render = False
    obj.hide_set(False)
    obj.select_set(True)
bpy.context.view_layer.objects.active = next(obj for obj in export_objects if obj.type == "MESH")
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

bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print("HOSPITAL_GLB_EXPORTED objects=", len(export_objects),
      "meshes=", sum(obj.type == "MESH" for obj in export_objects),
      "lights=", sum(obj.type == "LIGHT" for obj in export_objects),
      "blend=", bpy.data.filepath, "glb=", GLB_PATH)
