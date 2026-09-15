import bpy


for obj in bpy.data.objects:
    if obj.type != "FONT":
        continue
    lower = obj.name.lower()
    if lower.startswith("sign_text") or "nurse_station_label" in lower:
        print("ROOM_LABEL", obj.name, repr(obj.data.body), tuple(round(value, 3) for value in obj.matrix_world.translation))
