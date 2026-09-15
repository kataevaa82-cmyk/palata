import bpy, sys
from mathutils import Vector
targets = sys.argv[sys.argv.index("--")+1:]
print("DUMP_BEGIN")
for name in targets:
    root = bpy.data.objects.get("interaction_" + name)
    if not root:
        print("MISSING", name); continue
    print("ROOT", name, "loc=", tuple(round(v,3) for v in root.location),
          "rotz=", round(root.rotation_euler.z, 3), "scale=", tuple(round(v,3) for v in root.scale))
    lo = Vector((1e9,)*3); hi = Vector((-1e9,)*3)
    for o in root.children_recursive:
        if o.type not in {"MESH","CURVE","FONT"}: continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(min(lo[i], w[i]) for i in range(3))
            hi = Vector(max(hi[i], w[i]) for i in range(3))
        d = o.dimensions
        print("   ", o.name, o.type, "loc=", tuple(round(v,3) for v in o.location),
              "dim=", tuple(round(v,3) for v in d), "mat=", o.data.materials[0].name if getattr(o.data,'materials',None) and o.data.materials else "-")
    print("   BBOX", tuple(round(v,3) for v in lo), tuple(round(v,3) for v in hi),
          "size=", tuple(round(hi[i]-lo[i],3) for i in range(3)))
print("DUMP_END")
