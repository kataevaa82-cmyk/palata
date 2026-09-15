import bpy
import re
from mathutils import Vector


def world_bounds(obj):
    return [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]


def merged(objects):
    points = []
    for obj in objects:
        if obj.type in {"MESH", "CURVE", "FONT"}:
            points.extend(world_bounds(obj))
    if not points:
        return None
    minimum = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    maximum = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    center = (minimum + maximum) * 0.5
    return tuple(round(v, 3) for v in (*minimum, *maximum, *center))


def descendants(root):
    result = []
    queue = list(root.children)
    while queue:
        child = queue.pop()
        result.append(child)
        queue.extend(child.children)
    return result


print("CLOCKS")
for obj in bpy.data.objects:
    if "clock" in obj.name.lower() and obj.parent is None:
        print(obj.name, merged([obj] + descendants(obj)))

print("SIGNS")
for obj in bpy.data.objects:
    lower = obj.name.lower()
    if any(token in lower for token in ("sign", "label", "plaque", "room_number", "door_number", "ward_number")):
        print(obj.name, obj.type, merged([obj] + descendants(obj)) if obj.parent is None else merged([obj]))

print("PATIENTS")
for obj in bpy.data.objects:
    if re.fullmatch(r"ward_[1-6]_bed_[12]_patient_v3", obj.name.lower()):
        print(obj.name, merged(descendants(obj)))

print("INTERACTIONS")
for obj in bpy.data.objects:
    lower = obj.name.lower()
    if lower.startswith("interaction_") and obj.parent is None:
        print(obj.name, merged([obj] + descendants(obj)))

print("ROOM_ROOTS")
for obj in bpy.data.objects:
    lower = obj.name.lower()
    if obj.parent is None and any(token in lower for token in ("procedure", "nurse_station", "service_room", "sanitary")):
        print(obj.name, merged([obj] + descendants(obj)))
