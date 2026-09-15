import bpy
print("BLEND", bpy.data.filepath)
print("OBJECTS", len(bpy.data.objects), "MESHES", sum(1 for o in bpy.data.objects if o.type=="MESH"))
print("COLLECTIONS", [c.name for c in bpy.data.collections])
for name in ("ward_4_bed_1_patient_v3","violent_patient_v1","orderly_anomaly_v5","violent_patient_rig","orderly_v6_rig"):
    o = bpy.data.objects.get(name)
    print("OBJ", name, "FOUND" if o else "MISSING", getattr(o, "type", ""))
print("MESH_SAMPLE", [o.name for o in list(bpy.data.objects)[:30] if o.type=="MESH"])
