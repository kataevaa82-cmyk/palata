import math
import bpy


def find_layer_collection(layer, name):
    if layer.name == name:
        return layer
    for child in layer.children:
        found = find_layer_collection(child, name)
        if found:
            return found
    return None


def focus_procedure():
    collection = bpy.data.collections.get("GAMEPLAY_CARE_PROPS_V2")
    if not collection:
        return None
    workspace = bpy.data.workspaces.get("Modeling")
    if workspace:
        bpy.context.window.workspace = workspace
    layer_collection = find_layer_collection(bpy.context.view_layer.layer_collection, collection.name)
    if layer_collection:
        bpy.context.view_layer.active_layer_collection = layer_collection
    bpy.ops.object.select_all(action="DESELECT")
    prefixes = (
        "procedure_", "care_cabinet", "care_medicine_cabinet", "interaction_med_",
        "care_saline", "care_instrument_tray", "care_stethoscope", "care_thermometer"
    )
    selected = []
    for obj in collection.all_objects:
        if obj.type in {"MESH", "CURVE", "EMPTY"} and obj.name.startswith(prefixes):
            obj.hide_set(False)
            obj.select_set(True)
            selected.append(obj)
    active = bpy.data.objects.get("care_medicine_cabinet")
    if active:
        bpy.context.view_layer.objects.active = active
    for area in bpy.context.screen.areas:
        if area.type != "VIEW_3D":
            continue
        area.spaces.active.shading.type = "MATERIAL"
        area.spaces.active.clip_end = 200.0
        region = next((region for region in area.regions if region.type == "WINDOW"), None)
        if region and selected:
            with bpy.context.temp_override(area=area, region=region):
                bpy.ops.view3d.view_axis(type="FRONT", align_active=False)
                bpy.ops.view3d.view_selected(use_all_regions=False)
                bpy.ops.view3d.view_orbit(type="ORBITLEFT", angle=math.radians(16.0))
                bpy.ops.view3d.view_orbit(type="ORBITUP", angle=math.radians(10.0))
        break
    return None


bpy.app.timers.register(focus_procedure, first_interval=1.2)
