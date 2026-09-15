import bpy


BLEND_PATH = "C:/palata/palata_zero.blend"
ORPHAN_PARTS = (
    "interaction_mop_bucket_body",
    "interaction_mop_bucket_rim",
    "interaction_mop_handle",
    "interaction_mop_head",
)


removed = []
for name in ORPHAN_PARTS:
    obj = bpy.data.objects.get(name)
    if obj and obj.parent is None:
        removed.append(name)
        bpy.data.objects.remove(obj, do_unlink=True)

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print(f"CORRIDOR_BUCKET_CLEANUP removed={len(removed)} names={removed}")
