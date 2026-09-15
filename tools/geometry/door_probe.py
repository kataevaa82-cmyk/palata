import bpy
from mathutils import Vector
target = bpy.data.objects.get("hospital_door_N_1")
print("PROBE_BEGIN")
print("leaf dims", tuple(round(v,3) for v in target.dimensions), "loc", tuple(round(v,3) for v in target.location),
      "tris", sum(max(len(p.vertices)-2,1) for p in target.data.polygons))
c = target.matrix_world.translation
near = []
for o in bpy.data.objects:
    if o.type != "MESH" or o is target: continue
    if (o.matrix_world.translation - c).length < 1.6:
        near.append((round((o.matrix_world.translation-c).length,2), o.name,
                     tuple(round(v,3) for v in o.dimensions),
                     sum(max(len(p.vertices)-2,1) for p in o.data.polygons)))
for n in sorted(near)[:20]:
    print("near", n)
w = bpy.data.objects.get("window_frame_0")
print("window_frame_0 dims", tuple(round(v,3) for v in w.dimensions), "tris", sum(max(len(p.vertices)-2,1) for p in w.data.polygons))
cw = w.matrix_world.translation
for o in bpy.data.objects:
    if o.type != "MESH" or o is w: continue
    if (o.matrix_world.translation - cw).length < 1.4:
        print("win_near", round((o.matrix_world.translation-cw).length,2), o.name,
              tuple(round(v,3) for v in o.dimensions),
              sum(max(len(p.vertices)-2,1) for p in o.data.polygons))
print("PROBE_END")
