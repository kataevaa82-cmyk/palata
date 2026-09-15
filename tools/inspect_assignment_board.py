import json

import bpy
from mathutils import Vector


saved = {collection.name: collection.hide_viewport for collection in bpy.context.scene.collection.children}
for collection in bpy.context.scene.collection.children:
    collection.hide_viewport = False
bpy.context.view_layer.update()


def world_bounds(obj):
    if not obj.bound_box:
        return obj.matrix_world.translation.copy(), Vector((0.0, 0.0, 0.0))
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    low = Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
    high = Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
    return (low + high) * 0.5, high - low


items = []
for obj in bpy.context.scene.objects:
    if obj.name.startswith("care_assignment") or obj.name == "interaction_assignment_board":
        continue
    center, dimensions = world_bounds(obj)
    if abs(center.x - 3.75) > 3.0 or abs(center.y - 1.435) > 1.5 or center.z < 0.15 or center.z > 3.2:
        continue
    if max(dimensions) < 0.10:
        continue
    items.append({
        "name": obj.name,
        "type": obj.type,
        "center": [round(value, 3) for value in center],
        "dims": [round(value, 3) for value in dimensions],
        "parent": obj.parent.name if obj.parent else None,
    })

items.sort(key=lambda item: (abs(item["center"][1] - 1.435), abs(item["center"][0] - 3.75), item["name"]))
print("ASSIGNMENT_BOARD_NEIGHBORS", json.dumps(items[:100], ensure_ascii=False))

for collection in bpy.context.scene.collection.children:
    collection.hide_viewport = saved[collection.name]
