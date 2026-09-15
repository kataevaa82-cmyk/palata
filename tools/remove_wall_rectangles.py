"""Remove the meaningless flat rectangles stuck on the corridor walls.

`old_sign_mount_trace` and `wall_wear_decal` were meant to read as faint marks
where a sign used to hang / where the paint is rubbed through. Both use
MAT_wall_repair_patch, and material_system.gd maps any material name containing
"wall_repair" to the dark green oil-paint colour - so instead of a subtle patch
the player sees a hard dark rectangle floating on the light upper wall with no
readable meaning.

The organic wall grime is produced procedurally by material_system.gd's aging
shader, not by these objects, so removing them keeps the stains intact.
"""

import bpy

PREFIXES = ("old_sign_mount_trace", "wall_wear_decal")

doomed = [obj for obj in bpy.data.objects
          if obj.type == "MESH" and obj.name.startswith(PREFIXES)]
report = {}
for obj in doomed:
    key = obj.name.rstrip("0123456789.")
    report[key] = report.get(key, 0) + 1
    bpy.data.objects.remove(obj, do_unlink=True)

bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath="C:/palata/palata_zero.blend")
print("WALL_RECTANGLES_REMOVED", report, "total=", len(doomed))
