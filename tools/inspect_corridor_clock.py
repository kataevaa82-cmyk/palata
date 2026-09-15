import bpy
from mathutils import Vector


root = bpy.data.objects.get("corridor_clock_v2")
if root is None:
    raise RuntimeError("corridor_clock_v2 was not found")

print("CLOCK_ROOT", tuple(round(v, 4) for v in root.location), tuple(round(v, 4) for v in root.rotation_euler), tuple(round(v, 4) for v in root.scale))
for obj in [root, *root.children_recursive]:
    if obj.type == "MESH":
        points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        minimum = tuple(round(min(point[i] for point in points), 4) for i in range(3))
        maximum = tuple(round(max(point[i] for point in points), 4) for i in range(3))
    else:
        minimum = maximum = ()
    print("CLOCK_PART", obj.name, obj.type, "loc", tuple(round(v, 4) for v in obj.location), "bounds", minimum, maximum)
