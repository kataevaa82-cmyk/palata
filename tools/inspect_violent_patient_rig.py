import bpy


rig = bpy.data.objects.get("violent_patient_rig")
collection = bpy.data.collections.get("ASSET_violent_patient_v1")
if rig is None:
    raise RuntimeError("violent_patient_rig was not found in the open Blender file")

action = rig.animation_data.action if rig.animation_data else None
action_attributes = [name for name in dir(action) if "curve" in name or "layer" in name or "slot" in name] if action else []
print(
    "VIOLENT_RIG",
    "blender=", bpy.app.version_string,
    "bones=", len(rig.data.bones),
    "collection_objects=", len(collection.all_objects) if collection else 0,
    "action=", action.name if action else "NONE",
    "frame_range=", tuple(action.frame_range) if action else (),
    "attributes=", action_attributes,
)
if action:
    print("VIOLENT_ACTION_LAYERS", len(action.layers), "slots", len(action.slots))
    for layer in action.layers:
        print("LAYER", layer.name, "strips", len(layer.strips), "attrs", [name for name in dir(layer) if "strip" in name])
        for strip in layer.strips:
            print("STRIP", strip.type, "attrs", [name for name in dir(strip) if "channel" in name or "curve" in name])
