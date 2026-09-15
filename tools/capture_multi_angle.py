"""Render a subject from several angles in one pass.

A single camera angle hides exactly the kind of fault we keep finding (a part
floating off the back, a stand not reaching the floor), so every placement fix
gets checked from four sides plus a top-down.
"""

import math
import os

import bpy
from mathutils import Vector

OUT_ROOT = "C:/palata/build/angles"

SUBJECTS = {
    "bucket": {"centre": (7.20, -4.70, 0.42), "radius": 0.75},
    "monitor_ward3": {"centre": (-7.50, 4.04, 0.60), "radius": 1.15},
    "monitor_ward3_wide": {"centre": (-7.50, 3.90, 0.75), "radius": 2.60},
}

ANGLES = (
    ("front", 270, 12),
    ("left", 180, 14),
    ("right", 0, 14),
    ("back", 90, 12),
    ("high", 300, 48),
)


def render_subject(name, centre, radius):
    scene = bpy.context.scene
    out_dir = "%s/%s" % (OUT_ROOT, name)
    os.makedirs(out_dir, exist_ok=True)
    target = Vector(centre)

    for helper in ("MA_cam", "MA_key", "MA_fill"):
        old = bpy.data.objects.get(helper)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)

    camera_data = bpy.data.cameras.new("MA_cam")
    camera_data.lens = 42
    camera = bpy.data.objects.new("MA_cam", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera

    lights = []
    for light_name, energy in (("MA_key", 420.0), ("MA_fill", 160.0)):
        data = bpy.data.lights.new(light_name, "POINT")
        data.energy = energy
        data.shadow_soft_size = 0.7
        obj = bpy.data.objects.new(light_name, data)
        scene.collection.objects.link(obj)
        lights.append(obj)

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 760
    scene.render.resolution_y = 640

    for angle_name, swing, elevation in ANGLES:
        a, e = math.radians(swing), math.radians(elevation)
        offset = Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))
        distance = radius * 3.1
        camera.location = target + offset * distance
        camera.rotation_mode = "QUATERNION"
        camera.rotation_quaternion = (target - camera.location).to_track_quat("-Z", "Y")
        lights[0].location = target + offset * distance * 0.6 + Vector((0.0, 0.0, distance * 0.5))
        lights[1].location = target - offset * distance * 0.5 + Vector((0.0, 0.0, distance * 0.35))
        scene.render.filepath = "%s/%s.png" % (out_dir, angle_name)
        bpy.ops.render.render(write_still=True)

    bpy.data.objects.remove(camera, do_unlink=True)
    for obj in lights:
        bpy.data.objects.remove(obj, do_unlink=True)


def run(only=None):
    for name, spec in SUBJECTS.items():
        if only and name not in only:
            continue
        render_subject(name, spec["centre"], spec["radius"])
        print("ANGLES_RENDERED", name)


run()
