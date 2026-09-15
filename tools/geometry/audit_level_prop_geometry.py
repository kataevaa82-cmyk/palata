"""Inventory the level-prop geometry so an improvement pass has numbers, not
impressions: per interaction root, how many meshes, how many triangles, how many
of those meshes are flat-shaded, unbevelled boxes or coarse cylinders."""
import bpy, json, math

# The 37 roots main.gd binds (LEVEL_PROP_IDS). Kept explicit so the audit does
# not drift onto the care props that were never part of this pass.
LEVEL_PROPS = [
    "fuse_box", "spare_fuses", "emergency_lamp", "oxygen_pillow", "quarantine_curtain",
    "mask_box", "hand_sanitizer", "sample_tube", "gurney", "body_bag", "death_certificate",
    "blood_fridge", "blood_bag_first", "blood_bag_second", "blood_bag_third", "blood_chart",
    "radiator_key", "blanket_stack", "radiator_valve", "window_latch", "tea_kettle",
    "hospital_slippers", "muddy_trail", "bed_note", "escaped_patient", "duty_journal_form",
    "misplaced_chair", "floor_dirt", "fire_extinguisher", "smoke_source", "fire_alarm_panel",
    "sterile_bix", "surgical_lamp", "surgical_gown", "zero_door", "zero_key", "zero_card",
]
rows = []
for root in [bpy.data.objects["interaction_" + n] for n in LEVEL_PROPS]:
    meshes = [o for o in root.children_recursive if o.type == "MESH"]
    tris = 0
    flat = 0
    smooth = 0
    coarse = []
    for m in meshes:
        me = m.data
        tris += sum(max(len(p.vertices) - 2, 1) for p in me.polygons)
        if me.polygons and all(not p.use_smooth for p in me.polygons):
            flat += 1
        elif any(p.use_smooth for p in me.polygons):
            smooth += 1
        # a cylinder/sphere-ish mesh whose ring resolution is low reads faceted
        ngons = [len(p.vertices) for p in me.polygons if len(p.vertices) > 4]
        if ngons and max(ngons) <= 16:
            coarse.append((m.name, max(ngons)))
    rows.append({
        "root": root.name,
        "meshes": len(meshes),
        "tris": tris,
        "flat": flat,
        "smooth": smooth,
        "coarse": coarse[:6],
    })
rows.sort(key=lambda r: r["tris"])
print("LEVEL_PROP_GEOMETRY_AUDIT")
print(json.dumps(rows, ensure_ascii=False))
print("TOTAL tris=", sum(r["tris"] for r in rows), "roots=", len(rows))
