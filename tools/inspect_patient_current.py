import bpy, json
from mathutils import Vector

out=[]
for obj in bpy.data.objects:
    if obj.type != 'MESH' or not ('violent_patient_human' in obj.name or 'ward_4_bed_1_patient_v3' in obj.name):
        continue
    mats=[]
    for i, mat in enumerate(obj.data.materials):
        vids={v for p in obj.data.polygons if p.material_index==i for v in p.vertices}
        coords=[obj.data.vertices[v].co for v in vids]
        mats.append({'name':mat.name,'verts':len(coords),'lo':[min(v[a] for v in coords) for a in range(3)] if coords else [],'hi':[max(v[a] for v in coords) for a in range(3)] if coords else []})
    out.append({'name':obj.name,'matrix':[list(row) for row in obj.matrix_world], 'parent':obj.parent.name if obj.parent else None,'materials':mats,'modifiers':[(m.name,m.type) for m in obj.modifiers]})
print('PATIENT_INSPECT',json.dumps(out))
