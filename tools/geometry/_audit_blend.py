import bpy
print("BLEND", bpy.data.filepath)
print("OBJECTS", len(bpy.data.objects), "MESHES", sum(1 for o in bpy.data.objects if o.type=="MESH"))
print("COLLECTIONS", [c.name for c in bpy.data.collections])
for name in ("ward_4_bed_1_patient_v3","violent_patient_v1","orderly_anomaly_v5","violent_patient_rig","orderly_v6_rig"):
    o = bpy.data.objects.get(name)
    print("OBJ", name, "FOUND" if o else "MISSING", o.type if o else "")
patients = [o.name for o in bpy.data.objects if "patient_v3" in o.name and o.parent is None or (o.name.endswith("patient_v3"))]
print("PATIENT_ROOTS", [n for n in patients if n.endswith("patient_v3")])
