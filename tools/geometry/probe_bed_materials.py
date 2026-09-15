import bpy
for o in sorted([o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("ward_1_bed_2_")], key=lambda o: o.name):
    mats = [m.name for m in o.data.materials if m] if o.data.materials else []
    print("   %-40s %s" % (o.name.replace("ward_1_bed_2_", ""), mats))
