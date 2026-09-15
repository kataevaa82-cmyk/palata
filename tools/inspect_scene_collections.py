import bpy


for collection in bpy.context.scene.collection.children:
    objects = [obj for obj in collection.all_objects if obj is not None]
    print(
        "COLLECTION",
        collection.name,
        "objects=", len(objects),
        "mesh=", sum(obj.type == "MESH" for obj in objects),
        "hidden=", collection.hide_viewport,
        "render=", collection.hide_render,
    )
