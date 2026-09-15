import bpy
from mathutils import Vector


bpy.context.view_layer.update()


def bounds(obj):
    if obj.type not in {"MESH", "CURVE", "FONT"}:
        return None
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return low, high


def combined(root):
    entries = []
    for obj in [root] + list(root.children_recursive):
        item = bounds(obj)
        if item:
            entries.append(item)
    if not entries:
        return None
    low = Vector((min(item[0].x for item in entries), min(item[0].y for item in entries), min(item[0].z for item in entries)))
    high = Vector((max(item[1].x for item in entries), max(item[1].y for item in entries), max(item[1].z for item in entries)))
    return low, high


print("ROOM_LABELS")
for obj in bpy.data.objects:
    if obj.type == "FONT":
        location = obj.matrix_world.translation
        print(obj.name, repr(obj.data.body), tuple(round(v, 3) for v in location))


targets = (
    "interaction_assignment_board",
    "interaction_emergency_button",
    "interaction_fire_exit_seal",
    "interaction_elevator_inspection",
    "night_rules_sheet",
)
print("TARGETS")
for name in targets:
    root = bpy.data.objects.get(name)
    if not root:
        print(name, "MISSING")
        continue
    merged = combined(root)
    print(name, "root", tuple(round(v, 3) for v in root.matrix_world.translation), "bounds", tuple(round(v, 3) for point in merged for v in point) if merged else None)


print("NEARBY_ARCHITECTURE")
target_points = {
    "board": Vector((3.75, 2.42, 1.72)),
    "button": Vector((-1.0, 2.48, 1.34)),
    "fire": Vector((19.78, 1.34, 1.35)),
    "elevator": Vector((12.50, -1.43, 1.92)),
}
for obj in bpy.data.objects:
    lower = obj.name.lower()
    if obj.type != "MESH" or not any(token in lower for token in ("wall", "partition", "stair", "elevator", "door_frame")):
        continue
    item = bounds(obj)
    if not item:
        continue
    low, high = item
    for label, point in target_points.items():
        nearest_x = min(max(point.x, low.x), high.x)
        nearest_y = min(max(point.y, low.y), high.y)
        distance = Vector((nearest_x, nearest_y)) - Vector((point.x, point.y))
        if distance.length < 1.25 and high.z > 0.8:
            print(label, obj.name, tuple(round(v, 3) for v in low), tuple(round(v, 3) for v in high), "dxy", round(distance.length, 3))
