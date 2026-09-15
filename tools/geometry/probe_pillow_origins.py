import bpy
for name in ("ward_1_bed_1_pillow_left", "ward_1_bed_1_pillow_right", "ward_6_bed_2_pillow_left"):
    o = bpy.data.objects.get(name)
    if not o:
        print("MISSING", name); continue
    print("%-30s loc=%s scale=%s parent=%s mesh=%s users=%d verts_local_first=%s"
          % (name, tuple(round(v,3) for v in o.location), tuple(round(v,3) for v in o.scale),
             o.parent.name if o.parent else None, o.data.name, o.data.users,
             tuple(round(v,3) for v in o.data.vertices[0].co)))
    print("     matrix_world translation", tuple(round(v,3) for v in o.matrix_world.translation))
