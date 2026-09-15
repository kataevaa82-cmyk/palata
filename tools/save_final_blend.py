import bpy


bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath="C:/palata/palata_zero.blend")
print("FINAL_BLEND_SAVED")
