# -*- coding: utf-8 -*-
import bpy

for name in ("MAT_faded_hospital_linen", "MAT_care_clean_linen", "MAT_care_dirty_linen",
             "MAT_offwhite_painted_wood", "MAT_patient_blanket_blue", "MAT_faded_blue_blanket"):
    mat = bpy.data.materials.get(name)
    if mat is None:
        print("MISSING", name)
        continue
    base = None
    rough = None
    if mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                base = tuple(round(v, 3) for v in node.inputs["Base Color"].default_value)
                rough = round(node.inputs["Roughness"].default_value, 3)
                break
    users = sum(1 for o in bpy.data.objects
                if o.type == "MESH" and o.data.materials and mat.name in
                [m.name for m in o.data.materials if m])
    print("%-28s base=%s roughness=%s objects=%d" % (name, base, rough, users))
