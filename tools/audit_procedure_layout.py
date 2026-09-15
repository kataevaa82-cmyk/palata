import bpy
from mathutils import Vector


ROOM_MIN = Vector((-5.05, 1.42, -0.2))
ROOM_MAX = Vector((0.05, 5.95, 3.3))
bpy.context.view_layer.update()


def descendants(root):
    result = []
    queue = [root]
    while queue:
        node = queue.pop()
        result.append(node)
        queue.extend(node.children)
    return result


def visible_in_render(obj):
    if obj.hide_render:
        return False
    for collection in obj.users_collection:
        if collection.hide_render:
            return False
    return True


def bounds(root):
    points = []
    for obj in descendants(root):
        if obj.type not in {"MESH", "CURVE", "FONT"} or not visible_in_render(obj):
            continue
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not points:
        return None
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return low, high


def intersects_room(low, high):
    return low.x <= ROOM_MAX.x and high.x >= ROOM_MIN.x and low.y <= ROOM_MAX.y and high.y >= ROOM_MIN.y


print("PROCEDURE_ROOT_BOUNDS")
for root in sorted((obj for obj in bpy.data.objects if obj.parent is None), key=lambda obj: obj.name.lower()):
    result = bounds(root)
    if not result:
        continue
    low, high = result
    if not intersects_room(low, high):
        continue
    size = high - low
    center = (low + high) * 0.5
    if max(size.x, size.y, size.z) < 0.12:
        continue
    collections = ",".join(collection.name for collection in root.users_collection)
    print(
        root.name,
        "loc=", tuple(round(v, 3) for v in root.location),
        "center=", tuple(round(v, 3) for v in center),
        "size=", tuple(round(v, 3) for v in size),
        "bounds=", tuple(round(v, 3) for v in (*low, *high)),
        "collections=", collections,
    )
