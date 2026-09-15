import bpy
from mathutils import Vector
for name in bpy.data.objects.keys():
    if name.startswith("ward_1_bed_1_") and ("pillow" in name.lower() or "mattress" in name.lower()):
        o = bpy.data.objects[name]
        lo = Vector((1e9,)*3); hi = Vector((-1e9,)*3)
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(min(lo[i], w[i]) for i in range(3)); hi = Vector(max(hi[i], w[i]) for i in range(3))
        print("PILLOW %-34s x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f" % (name, lo.x,hi.x,lo.y,hi.y,lo.z,hi.z))
mats=set()
for o in bpy.data.objects:
    if o.name.startswith("ward_1_bed_1_patient_v3_patient_") and o.type=="MESH" and o.data.materials:
        mats.add((o.name.split("_patient_")[-1], o.data.materials[0].name))
for m in sorted(mats): print("MAT", m)
