import bpy
print("HIER_BEGIN")
for n in ["hospital_door_N_1","door_glass_N_1","doorframe_N_1","window_frame_0","window_detail_mesh_0"]:
    o = bpy.data.objects.get(n)
    if not o: print("missing", n); continue
    chain=[]; p=o.parent
    while p: chain.append(p.name+"("+p.type+")"); p=p.parent
    print(n, "parent_chain=", chain or "-", "rot=", tuple(round(v,3) for v in o.rotation_euler))
pivots=[o.name for o in bpy.data.objects if o.name.lower().startswith("pivot")]
print("pivots", len(pivots), sorted(pivots)[:8])
p0 = bpy.data.objects.get(sorted(pivots)[0]) if pivots else None
if p0:
    print("pivot0", p0.name, "type", p0.type, "children", [c.name for c in p0.children])
doors=[o.name for o in bpy.data.objects if o.name.startswith("hospital_door")]
print("doors", len(doors), sorted(doors))
wins=[o.name for o in bpy.data.objects if o.name.startswith("window_frame")]
print("window_frames", len(wins), sorted(wins))
print("HIER_END")
