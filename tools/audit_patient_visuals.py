import bpy

patient = bpy.data.objects.get("ward_4_bed_1_patient_v3")
bed = bpy.data.objects.get("ward_4_bed_1_v3") or bpy.data.objects.get("ward_4_bed_1")

for label, root in (("PATIENT", patient), ("BED", bed)):
    print(label, root.name if root else None)
    if not root:
        continue
    for obj in root.children_recursive:
        lower = obj.name.lower()
        if label == "PATIENT" or any(token in lower for token in ("blanket", "pillow", "mattress", "linen", "patient")):
            dimensions = tuple(round(value, 3) for value in obj.dimensions)
            location = tuple(round(value, 3) for value in obj.location)
            scale = tuple(round(value, 3) for value in obj.scale)
            world_scale = tuple(round(value, 3) for value in obj.matrix_world.to_scale())
            print(" ", obj.name, obj.type, "loc", location, "scale", scale, "world_scale", world_scale, "dim", dimensions)
