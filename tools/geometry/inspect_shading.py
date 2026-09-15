import bpy
names = ["level_fuse_panel_shell", "level_fuse_socket", "level_kettle_body", "level_bix_drum",
         "level_gurney_deck", "level_extinguisher_body", "level_zero_door_leaf"]
print("SHADING_BEGIN")
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    if not any(o.name.startswith(n) for n in names):
        continue
    me = o.data
    smooth = sum(1 for p in me.polygons if p.use_smooth)
    sharp = sum(1 for e in me.edges if e.use_edge_sharp)
    mods = [(m.type, getattr(m, "node_group", None) and m.node_group.name or m.name) for m in o.modifiers]
    print("MESH", o.name, "polys=", len(me.polygons), "smooth=", smooth, "sharp_edges=", sharp,
          "custom_normals=", me.has_custom_normals, "mods=", mods)
# global stats
tot = sm = 0
sharp_meshes = 0
angle_mod = 0
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    tot += len(o.data.polygons)
    sm += sum(1 for p in o.data.polygons if p.use_smooth)
    if any(e.use_edge_sharp for e in o.data.edges):
        sharp_meshes += 1
    if any(m.type == "NODES" for m in o.modifiers):
        angle_mod += 1
print("GLOBAL polys=", tot, "smooth=", sm, "meshes_with_sharp=", sharp_meshes, "meshes_with_node_mod=", angle_mod,
      "meshes=", sum(1 for o in bpy.data.objects if o.type == "MESH"))
print("SHADING_END")
