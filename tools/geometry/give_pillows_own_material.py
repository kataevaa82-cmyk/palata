# -*- coding: utf-8 -*-
"""Give the pillows a material of their own.

MAT_faded_hospital_linen is the mattress material, and material_system.gd maps
every name containing "linen" to the same muted green - so the reshaped pillow
came out exactly the colour of the bed it lies on and vanished into it. This
gives the pillows their own material name; the matching rule in
_palette_color() paints it like laundered cotton instead.

The name still contains "linen" on purpose, so the fabric shader path in
material_system.gd keeps treating it as cloth.

Run: blender --background hospital_models_work.blend --python this_file.py
"""
import bpy

SOURCE = "MAT_faded_hospital_linen"
NAME = "MAT_pillow_linen"

source = bpy.data.materials.get(SOURCE)
if source is None:
    raise SystemExit("material %s not found" % SOURCE)

material = bpy.data.materials.get(NAME)
if material is None:
    material = source.copy()
    material.name = NAME
    print("CREATED", NAME, "from", SOURCE)

count = 0
for obj in bpy.data.objects:
    if obj.type != "MESH" or "pillow" not in obj.name.lower():
        continue
    if obj.name.startswith("interaction_"):
        continue          # the oxygen pillow is a prop, not bedding
    obj.data.materials.clear()
    obj.data.materials.append(material)
    count += 1
    print("   %s" % obj.name)

print("PILLOW_MATERIAL count=%d material=%s" % (count, NAME))
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print("PILLOW_MATERIAL_SAVED", bpy.data.filepath)
