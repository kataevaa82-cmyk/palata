import math

import bpy


board = bpy.data.objects.get("interaction_assignment_board")
if board is None:
    raise RuntimeError("Assignment board was not found")

# Hang the board entirely on the solid N5 wall panel. The wall face toward the
# corridor is y=1.55; the 70 mm back plate is therefore centred at y=1.505 so
# its rear sits almost flush instead of floating in front of the opening.
board.location = (4.50, 1.505, 1.84)
board.rotation_euler = (0.0, 0.0, 0.0)
board.scale = (0.72, 1.0, 0.78)

mounted = []
for obj in bpy.data.objects:
    lower = obj.name.lower()
    if obj.parent is not None:
        continue
    if not (lower.startswith("soviet_outlet") or lower.startswith("soviet_switch")):
        continue
    side = 1.0 if obj.location.y >= 0.0 else -1.0
    obj.location.y = side * 1.5325
    obj.rotation_euler.x = 0.0
    obj.rotation_euler.y = 0.0
    mounted.append(obj.name)

bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath="C:/palata/palata_zero.blend")
print("ASSIGNMENT_BOARD_REHUNG", tuple(round(value, 4) for value in board.location), "scale", tuple(round(value, 3) for value in board.scale))
print("WALL_FIXTURES_FLUSH", len(mounted), mounted)
