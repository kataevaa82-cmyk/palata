import bpy
from mathutils import Vector


def bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return tuple(round(value, 3) for axis in range(3) for value in (min(point[axis] for point in points), max(point[axis] for point in points)))


for obj in bpy.data.objects:
    lower = obj.name.lower()
    if obj.type not in {"MESH", "CURVE", "FONT"}:
        continue
    if any(token in lower for token in ("east_end", "west_end", "exit", "entrance", "elevator", "fire", "window")):
        print("END_WALL_ITEM", obj.name, obj.type, bounds(obj), "parent", obj.parent.name if obj.parent else "NONE")
