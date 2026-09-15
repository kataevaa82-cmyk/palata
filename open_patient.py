import bpy

path = r"C:\palata\violent_patient_v1.glb"
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=path)

objs = [o for o in bpy.context.scene.objects if o.type in {'MESH', 'ARMATURE'}]
for o in bpy.context.selected_objects:
    o.select_set(False)
for o in objs:
    o.select_set(True)
if objs:
    bpy.context.view_layer.objects.active = objs[0]

bpy.ops.wm.save_as_mainfile(filepath=r"C:\palata\patient_work.blend")
