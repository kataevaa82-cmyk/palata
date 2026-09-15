import bpy
doors=[o.name.replace("pivot_hospital_door_","") for o in bpy.data.objects if o.name.startswith("pivot_hospital_door_")]
print("DOORS", len(doors))
no_glass=[t for t in doors if not bpy.data.objects.get("door_glass_"+t)]
no_panel=[t for t in doors if not bpy.data.objects.get("door_detail_panel_"+t)]
no_bead=[t for t in doors if not bpy.data.objects.get("door_detail_bead_top_"+t)]
print("NO_GLASS", no_glass)
print("NO_PANEL", no_panel)
print("NO_BEAD", no_bead)
