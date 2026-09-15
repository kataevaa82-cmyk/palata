import bpy
print("COLLECTIONS_BEGIN")
for c in bpy.data.collections:
    print("COL", c.name, len(c.objects), len(c.all_objects))
roots=[o.name for o in bpy.data.objects if o.name.startswith("interaction_")]
print("ROOTS", len(roots))
print("ROOTLIST", sorted(roots))
print("COLLECTIONS_END")
