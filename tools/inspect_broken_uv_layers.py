import bpy


for obj in bpy.data.objects:
    if obj.type != "MESH" or obj.data is None:
        continue
    loop_count = len(obj.data.loops)
    for layer in obj.data.uv_layers:
        uv_count = len(layer.uv)
        if uv_count != loop_count:
            print(
                "BROKEN_UV",
                obj.name,
                "mesh=", obj.data.name,
                "loops=", loop_count,
                "uv=", uv_count,
                "hidden=", obj.hide_get(), obj.hide_viewport,
                "collections=", [collection.name for collection in obj.users_collection],
            )
