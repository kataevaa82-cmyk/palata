import bpy
from mathutils import Vector


def world_bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return (
        min(p.x for p in points),
        max(p.x for p in points),
        min(p.y for p in points),
        max(p.y for p in points),
        min(p.z for p in points),
        max(p.z for p in points),
    )


def merged_bounds(objects):
    bounds = [world_bounds(obj) for obj in objects if obj.type in {"MESH", "CURVE"}]
    if not bounds:
        return None
    return (
        min(b[0] for b in bounds),
        max(b[1] for b in bounds),
        min(b[2] for b in bounds),
        max(b[3] for b in bounds),
        min(b[4] for b in bounds),
        max(b[5] for b in bounds),
    )


def has_ancestor(obj, ancestor):
    current = obj.parent
    while current:
        if current == ancestor:
            return True
        current = current.parent
    return False


print("WARD_BOUNDS")
for ward in range(1, 7):
    prefix = f"ward_{ward}_"
    objects = [obj for obj in bpy.data.objects if obj.name.lower().startswith(prefix)]
    print(ward, len(objects), merged_bounds(objects))
    roots = [
        obj for obj in objects
        if obj.type == "EMPTY"
        and obj.name.lower() in {
            f"ward_{ward}_bed_1",
            f"ward_{ward}_bed_2",
            f"ward_{ward}_bedside_cabinet_1",
            f"ward_{ward}_bedside_cabinet_2",
        }
    ]
    for root in roots:
        descendants = [obj for obj in objects if has_ancestor(obj, root)]
        print(" ROOT", root.name, merged_bounds(descendants))
        print("  CHAIN", root.name, [parent.name for parent in [root.parent, root.parent.parent if root.parent else None] if parent])

print("DOORS")
door_pivots = [obj for obj in bpy.data.objects if obj.name.lower().startswith("pivot_hospital_door_")]
for pivot in door_pivots:
    print(pivot.name, tuple(round(v, 3) for v in pivot.matrix_world.translation))
    slab_name = pivot.name.replace("pivot_", "")
    slab = bpy.data.objects.get(slab_name)
    if slab:
        print(" SLAB", tuple(round(v, 3) for v in world_bounds(slab)))

print("DOOR_OBSTACLE_CANDIDATES")
tokens = ("socket", "outlet", "rosette", "stick", "pole", "rod", "strip", "rail", "pipe")
for obj in bpy.data.objects:
    lower = obj.name.lower()
    if obj.type in {"MESH", "CURVE"} and any(token in lower for token in tokens):
        b = world_bounds(obj)
        print(obj.name, tuple(round(v, 3) for v in b))
