# -*- coding: utf-8 -*-
"""Close-ups of two doorways from the corridor side.

The handle/hinge placement is derived per door from the leaf's own bounding box,
so a mirrored south-side door is the case that would show a handle sunk into the
leaf or hanging in the wall. Render one of each and look.
"""
import math, os, sys
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "C:/palata/build/family_review"
TAG = argv[1] if len(argv) > 1 else "after"
os.makedirs(OUT, exist_ok=True)
scene = bpy.context.scene
for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
    try:
        scene.render.engine = engine; break
    except TypeError: continue
scene.render.resolution_x = 700; scene.render.resolution_y = 900
scene.render.image_settings.file_format = "PNG"
world = bpy.data.worlds.new("DOORCU"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.09, 0.10, 0.10, 1.0)
scene.world = world
cam_data = bpy.data.cameras.new("DOORCU_cam"); cam_data.lens = 42
camera = bpy.data.objects.new("DOORCU_cam", cam_data)
scene.collection.objects.link(camera); scene.camera = camera
lights = []
for name, energy in (("k", 700.0), ("f", 260.0)):
    d = bpy.data.lights.new("DOORCU_" + name, "POINT"); d.energy = energy; d.shadow_soft_size = 1.2
    o = bpy.data.objects.new("DOORCU_" + name, d); scene.collection.objects.link(o); lights.append(o)
helpers = {camera.name} | {l.name for l in lights}
for o in scene.objects:
    if o.name not in helpers: o.hide_render = True

for tag in ("N_1", "S_2"):
    parts = [o for o in scene.objects if o.type == "MESH" and (
        o.name.startswith(("hospital_door_" + tag, "door_glass_" + tag,
                           "doorframe_" + tag, "doorframe_top_" + tag)) or
        (o.name.startswith("door_detail_") and o.name.endswith(tag)) or
        (o.name.startswith("door_detail_") and ("_" + tag + "_") in o.name))]
    if not parts:
        print("CLOSEUP_MISSING", tag); continue
    for o in parts: o.hide_render = False
    lo = Vector((1e9,)*3); hi = Vector((-1e9,)*3)
    for o in parts:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(min(lo[i], w[i]) for i in range(3)); hi = Vector(max(hi[i], w[i]) for i in range(3))
    centre = (lo + hi) * 0.5
    # Stand in the corridor: the corridor runs along x with its faces at y=+-1.55
    side = 1.0 if centre.y > 0 else -1.0
    camera.location = centre + Vector((0.55, side * 2.1, 0.15))
    camera.rotation_euler = (centre - camera.location).normalized().to_track_quat("-Z", "Y").to_euler()
    lights[0].location = centre + Vector((1.0, side * 2.0, 1.6))
    lights[1].location = centre + Vector((-1.4, side * 1.6, 0.6))
    scene.render.filepath = os.path.join(OUT, "doorcu_%s_%s.png" % (tag, TAG))
    bpy.ops.render.render(write_still=True)
    print("CLOSEUP", tag, "parts", len(parts))
    for o in parts: o.hide_render = True
print("CLOSEUP_DONE")
