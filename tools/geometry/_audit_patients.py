import bpy
root = bpy.data.objects.get("ward_4_bed_1_patient_v3")
print("ROOT", root.name, root.location, root.rotation_mode, tuple(round(x,3) for x in root.rotation_euler), root.keys())
parts = []
for o in root.children_recursive:
    if o.type != "MESH":
        print("NONMESH", o.name, o.type)
        continue
    tris = sum(max(len(p.vertices)-2,1) for p in o.data.polygons)
    verts = len(o.data.vertices)
    mats = [m.name if m else None for m in o.data.materials]
    dims = tuple(round(d,3) for d in o.dimensions)
    parts.append((o.name, verts, tris, dims, mats))
    print("PART", o.name, "verts", verts, "tris", tris, "dims", dims, "mats", mats)
print("PART_COUNT", len(parts), "TRIS", sum(p[2] for p in parts))
# mattress
m = bpy.data.objects.get("ward_4_bed_1_mattress")
if m:
    zs = [(m.matrix_world @ v.co).z for v in m.data.vertices]
    print("MATTRESS_Z", round(min(zs),3), round(max(zs),3), "dims", tuple(round(d,3) for d in m.dimensions))
pillow = bpy.data.objects.get("ward_4_bed_1_pillow")
if pillow:
    zs = [(pillow.matrix_world @ v.co).z for v in pillow.data.vertices]
    print("PILLOW_Z", round(min(zs),3), round(max(zs),3))
# patient local bounds
from mathutils import Vector
lo = Vector((1e9,)*3); hi = Vector((-1e9,)*3)
for o in root.children_recursive:
    if o.type != "MESH":
        continue
    for v in o.data.vertices:
        p = o.matrix_local @ v.co
        lo = Vector(min(lo[i], p[i]) for i in range(3))
        hi = Vector(max(hi[i], p[i]) for i in range(3))
print("PATIENT_LOCAL_BOX", tuple(round(x,3) for x in lo), tuple(round(x,3) for x in hi))
