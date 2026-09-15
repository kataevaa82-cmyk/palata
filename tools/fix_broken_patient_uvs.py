import math

import bpy


fixed = []
for obj in list(bpy.data.objects):
    if obj.type != "MESH" or obj.data is None:
        continue
    broken = any(len(layer.uv) != len(obj.data.loops) for layer in obj.data.uv_layers)
    if not broken:
        continue
    for layer in list(obj.data.uv_layers):
        obj.data.uv_layers.remove(layer)
    for candidate in bpy.context.view_layer.objects:
        candidate.select_set(False)
    obj.hide_viewport = False
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    fixed.append((obj.name, len(obj.data.loops), len(obj.data.uv_layers.active.uv) if obj.data.uv_layers.active else 0))

bpy.ops.wm.save_as_mainfile(filepath="C:/palata/palata_zero.blend")
print("BROKEN_PATIENT_UVS_FIXED", len(fixed), fixed)
