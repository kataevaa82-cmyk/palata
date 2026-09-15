import bpy
from mathutils import Vector


def world_bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    low = Vector((min(point.x for point in points), min(point.y for point in points), min(point.z for point in points)))
    high = Vector((max(point.x for point in points), max(point.y for point in points), max(point.z for point in points)))
    return low, high


print("EAST_ROOM_OBJECTS")
for obj in bpy.data.objects:
    if obj.type not in {"MESH", "CURVE", "FONT"}:
        continue
    low, high = world_bounds(obj)
    if high.x < 14.8 or low.x > 20.8 or high.y < 1.25 or low.y > 6.2:
        continue
    root = obj
    while root.parent:
        root = root.parent
    print(
        obj.name,
        "root=", root.name,
        "collection=", obj.users_collection[0].name if obj.users_collection else "NONE",
        "bounds=", tuple(round(value, 3) for value in (*low, *high)),
    )
