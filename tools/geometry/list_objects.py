import bpy
print("OBJ_BEGIN")
for o in bpy.data.objects:
    print("OBJ", o.type, o.name, "parent=", o.parent.name if o.parent else "-")
print("MESHES", len(bpy.data.meshes), "MATS", len(bpy.data.materials))
print("OBJ_END")
