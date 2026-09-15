import bpy


COLLECTION_NAME = "ASSET_violent_patient_v1"


def focus_patient():
    collection = bpy.data.collections.get(COLLECTION_NAME)
    if not collection or not bpy.context.screen:
        return 0.5
    for child in bpy.context.scene.collection.children:
        child.hide_viewport = child != collection
    collection.hide_viewport = False
    bpy.context.scene.frame_set(9)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in collection.all_objects:
        obj.hide_set(False)
        obj.hide_viewport = False
        obj.select_set(True)
    rig = bpy.data.objects.get("violent_patient_rig")
    if rig:
        bpy.context.view_layer.objects.active = rig
        rig.show_in_front = True
    for area in bpy.context.screen.areas:
        if area.type != "VIEW_3D":
            continue
        area.spaces.active.shading.type = "MATERIAL"
        window_region = next((region for region in area.regions if region.type == "WINDOW"), None)
        if not window_region:
            continue
        with bpy.context.temp_override(area=area, region=window_region):
            bpy.ops.view3d.view_axis(type="FRONT", align_active=False)
            bpy.ops.view3d.view_selected(use_all_regions=False)
        break
    return None


bpy.app.timers.register(focus_patient, first_interval=0.8)
