"""Model every prop the ten new night shifts (level_manager.gd) need.

All 37 props live in one dedicated collection and ship in the same GLB as the
rest of the hospital; main.gd hides them on load and level_manager reveals only
the selected night's whitelist. That is why they can all coexist here.

Two naming rules matter and are enforced at the bottom of this file:

1. Every interactive root is a UNIQUE `interaction_*` empty. main.gd looks it up
   with an exact `LEVEL_PROP_IDS.has(name.to_lower())`, so Blender's `.001`
   auto-suffix on a duplicate root would silently unbind that prop.

2. Child mesh names must dodge main.gd::_needs_collision()'s substring list
   ("floor", "wall", "door", "counter", "cabinet", "bed_", "desk", ...). A patch
   of corridor dirt named *_floor_* would get an auto box collider and become an
   invisible wall in the middle of the corridor - hence `level_dirt_patch`, not
   `level_floor_dirt`. Where a prop SHOULD be solid (the fridge, the zero door)
   the name deliberately opts in via "cabinet"/"door".

Placement is derived from the measured layout: corridor spans x -20.5..20.5 with
its inner wall faces at y = +-1.55, doorways sit at x = -18.05, -13.05, -8.05,
-3.05, 1.95, 6.95, ~11.9, 16.95, so wall fittings go at the midpoints between
them. The escaped patient is deliberately built seated with a blanket over the
head: no face, and therefore none of the standing-vs-lying head frame trouble
that fix_patient_head_orientation.py had to undo.
"""

import bpy
import math

BLEND_PATH = "C:/palata/palata_zero.blend"
COLLECTION_NAME = "GAMEPLAY_LEVEL_PROPS_V1"

_library = {"CARE_GAMEPLAY_LIBRARY_ONLY": True}
exec(compile(open("C:/palata/tools/build_care_gameplay_v2.py", encoding="utf-8").read(),
             "build_care_gameplay_v2.py", "exec"), _library)

add_empty = _library["add_empty"]
cube = _library["cube"]
sphere = _library["sphere"]
cylinder = _library["cylinder"]
cylinder_between = _library["cylinder_between"]
torus = _library["torus"]
curve = _library["curve"]
text_mesh = _library["text_mesh"]
make_material = _library["make_material"]
remove_tree = _library["remove_tree"]

MAT_ENAMEL = _library["MAT_ENAMEL"]
MAT_GLASS = _library["MAT_GLASS"]
MAT_METAL = _library["MAT_METAL"]
MAT_RUST = _library["MAT_RUST"]
MAT_PAPER = _library["MAT_PAPER"]
MAT_RED = _library["MAT_RED"]
MAT_BLUE = _library["MAT_BLUE"]
MAT_AMBER = _library["MAT_AMBER"]
MAT_LINEN = _library["MAT_LINEN"]
MAT_DIRTY_LINEN = _library["MAT_DIRTY_LINEN"]
MAT_WATER = _library["MAT_WATER"]
MAT_SKIN = _library["MAT_SKIN"]
MAT_HAIR = _library["MAT_HAIR"]
MAT_GOWN = _library["MAT_GOWN"]
MAT_BLANKET = _library["MAT_BLANKET"]
MAT_INK = _library["MAT_INK"]
MAT_RUBBER = _library["MAT_RUBBER"]
MAT_CLOTH = _library["MAT_CLOTH"]
MAT_CERAMIC = _library["MAT_CERAMIC"]
MAT_MERCURY = _library["MAT_MERCURY"]
MAT_BOARD = _library["MAT_BOARD"]

MAT_BAKELITE = make_material("MAT_level_bakelite", (0.075, 0.055, 0.040), 0.72)
MAT_BLOOD = make_material("MAT_level_blood", (0.19, 0.012, 0.010), 0.55)
MAT_SMOKE = make_material("MAT_level_smoke", (0.13, 0.135, 0.13), 0.99)
MAT_DIRT = make_material("MAT_level_dirt", (0.085, 0.085, 0.062), 0.99)
MAT_FIRE_RED = make_material("MAT_level_fire_red", (0.34, 0.020, 0.008), 0.78)
MAT_LAMP = make_material("MAT_level_lamp_shell", (0.60, 0.62, 0.55), 0.62, 0.30)
MAT_LAMP_GLASS = make_material("MAT_level_lamp_glass", (0.86, 0.88, 0.74), 0.18)
MAT_PLASTIC_SHEET = make_material("MAT_level_quarantine_film", (0.52, 0.58, 0.54), 0.30)
MAT_GREEN_SIGN = make_material("MAT_level_green_sign", (0.055, 0.20, 0.10), 0.92)

ROOTS = []


def root(name, location, rotation_z=0.0, care_item=None):
    """An interactive prop root. Empties never get auto-collision (main.gd only
    box-collides MeshInstance3D), so the root itself is always safe."""
    obj = add_empty(name, location, COLLECTION)
    if rotation_z:
        obj.rotation_euler.z = math.radians(rotation_z)
    obj["care_item"] = care_item or name.replace("interaction_", "")
    ROOTS.append(name)
    return obj


# ---------------------------------------------------------------- night 2 ----

def build_power_night():
    # Wall fuse panel, west corridor, midway between the ward 1 and ward 2 doors.
    box = root("interaction_fuse_box", (-15.50, 1.50, 1.55))
    cube("level_fuse_panel_shell", (0, 0.05, 0), (0.62, 0.16, 0.78), MAT_ENAMEL, COLLECTION, box, bevel=0.020)
    cube("level_fuse_panel_face", (0, -0.045, 0), (0.54, 0.035, 0.70), MAT_BAKELITE, COLLECTION, box, bevel=0.012)
    for index, z in enumerate((0.22, 0.0, -0.22)):
        for x in (-0.15, 0.0, 0.15):
            cylinder("level_fuse_socket", (x, -0.070, z), 0.042, 0.045, MAT_CERAMIC, COLLECTION, box,
                     rotation=(math.radians(90), 0, 0), vertices=16)
            cylinder("level_fuse_cap", (x, -0.088, z), 0.030, 0.022, MAT_RUST if index == 0 else MAT_METAL,
                     COLLECTION, box, rotation=(math.radians(90), 0, 0), vertices=14)
    cube("level_fuse_hinge", (-0.30, -0.03, 0), (0.035, 0.10, 0.66), MAT_METAL, COLLECTION, box, bevel=0.008)
    cylinder("level_fuse_latch", (0.27, -0.078, 0), 0.020, 0.070, MAT_METAL, COLLECTION, box,
             rotation=(math.radians(90), 0, 0), vertices=12)
    text_mesh("level_fuse_warning", "220V", (0, -0.070, 0.315), 0.052, MAT_RED, COLLECTION, box)

    # Spare porcelain fuses in a cardboard tray, medical storage shelf.
    spares = root("interaction_spare_fuses", (16.20, 4.30, 1.02))
    cube("level_spare_fuse_tray", (0, 0, 0), (0.34, 0.22, 0.055), MAT_PAPER, COLLECTION, spares, bevel=0.010)
    for index in range(4):
        x = -0.105 + (index % 2) * 0.21
        y = -0.055 + (index // 2) * 0.11
        cylinder("level_spare_fuse_body", (x, y, 0.055), 0.038, 0.058, MAT_CERAMIC, COLLECTION, spares, vertices=16)
        cylinder("level_spare_fuse_contact", (x, y, 0.090), 0.026, 0.016, MAT_METAL, COLLECTION, spares, vertices=14)

    # Rechargeable emergency lantern, storage room.
    lamp = root("interaction_emergency_lamp", (17.40, 3.90, 1.02))
    cube("level_lantern_body", (0, 0, 0.11), (0.20, 0.15, 0.22), MAT_ENAMEL, COLLECTION, lamp, bevel=0.020)
    cylinder("level_lantern_lens", (0, -0.082, 0.14), 0.070, 0.030, MAT_LAMP_GLASS, COLLECTION, lamp,
             rotation=(math.radians(90), 0, 0), vertices=20)
    torus("level_lantern_bezel", (0, -0.090, 0.14), 0.072, 0.012, MAT_METAL, COLLECTION, lamp,
          rotation=(math.radians(90), 0, 0))
    cylinder_between("level_lantern_handle_L", (-0.075, 0, 0.22), (-0.055, 0, 0.30), 0.010, MAT_METAL, COLLECTION, lamp, 10)
    cylinder_between("level_lantern_handle_R", (0.075, 0, 0.22), (0.055, 0, 0.30), 0.010, MAT_METAL, COLLECTION, lamp, 10)
    cylinder_between("level_lantern_grip", (-0.055, 0, 0.30), (0.055, 0, 0.30), 0.012, MAT_RUBBER, COLLECTION, lamp, 10)
    cube("level_lantern_switch", (0.085, 0.02, 0.06), (0.030, 0.045, 0.055), MAT_RED, COLLECTION, lamp, bevel=0.006)

    # Rubberised oxygen pillow with a spigot, propped against the procedure wall.
    # z clears the floor: the bladder's own half-height sinks 0.28 below origin.
    pillow = root("interaction_oxygen_pillow", (-1.30, 4.92, 0.30))
    body = sphere("level_oxygen_bladder", (0, 0, 0), (0.34, 0.13, 0.26), MAT_RUBBER, COLLECTION, pillow, 28)
    body.rotation_euler.x = math.radians(8)
    cube("level_oxygen_seam", (0, -0.005, 0.255), (0.66, 0.055, 0.020), MAT_RUBBER, COLLECTION, pillow, bevel=0.008)
    cylinder("level_oxygen_spigot", (0.30, -0.02, 0.14), 0.020, 0.14, MAT_METAL, COLLECTION, pillow,
             rotation=(0, math.radians(58), 0), vertices=14)
    curve("level_oxygen_hose", [(0.36, -0.02, 0.20), (0.50, -0.06, 0.10), (0.55, -0.02, -0.10)],
          0.014, MAT_RUBBER, COLLECTION, pillow)
    cube("level_oxygen_tag", (-0.16, -0.10, 0.12), (0.16, 0.010, 0.09), MAT_PAPER, COLLECTION, pillow, bevel=0.004)


# ---------------------------------------------------------------- night 3 ----

def build_quarantine_night():
    # Sheet film taped across the ward 6 doorway (door S_3 at x -8.05, y -1.72).
    # No child name matches _needs_collision, so the player can push through it.
    curtain = root("interaction_quarantine_curtain", (-8.05, -1.60, 1.05))
    for index, x in enumerate((-0.40, -0.13, 0.14, 0.41)):
        panel = cube("level_quarantine_film", (x, 0, 0), (0.27, 0.010, 2.06), MAT_PLASTIC_SHEET,
                     COLLECTION, curtain, bevel=0.004)
        panel.rotation_euler.y = math.radians(-3 + index * 2)
    cube("level_quarantine_rail", (0, 0, 1.05), (1.24, 0.045, 0.045), MAT_METAL, COLLECTION, curtain, bevel=0.010)
    cube("level_quarantine_tape_top", (0, -0.012, 0.98), (1.22, 0.012, 0.075), MAT_RED, COLLECTION, curtain, bevel=0.004)
    text_mesh("level_quarantine_sign", "КАРАНТИН", (0, -0.020, 0.42), 0.105, MAT_RED, COLLECTION, curtain)

    # Carton of gauze masks, set on the sterilizer drum's lid. It used to sit on
    # the medicine cabinet shelf, but interaction_med_saline and
    # interaction_med_bandage are always present there and their own boxes
    # intercepted the ray first, leaving the masks visible but unusable.
    masks = root("interaction_mask_box", (-0.43, 2.58, 0.88))
    cube("level_mask_carton", (0, 0, 0), (0.30, 0.20, 0.15), MAT_PAPER, COLLECTION, masks, bevel=0.012)
    cube("level_mask_carton_lid", (0, 0, 0.082), (0.31, 0.21, 0.020), MAT_PAPER, COLLECTION, masks, bevel=0.008)
    for index, y in enumerate((-0.045, 0.010, 0.055)):
        folded = cube("level_mask_folded", (0.02, y, 0.105), (0.22, 0.075, 0.016), MAT_LINEN,
                      COLLECTION, masks, bevel=0.006)
        folded.rotation_euler.z = math.radians(-6 + index * 5)
    cube("level_mask_label", (0, -0.104, 0.01), (0.20, 0.008, 0.08), MAT_GREEN_SIGN, COLLECTION, masks, bevel=0.004)

    # Wall-mounted alcohol dispenser beside the quarantined ward.
    gel = root("interaction_hand_sanitizer", (-9.20, -1.50, 1.25))
    cube("level_sanitizer_bracket", (0, -0.06, 0), (0.16, 0.12, 0.34), MAT_ENAMEL, COLLECTION, gel, bevel=0.014)
    cylinder("level_sanitizer_bottle", (0, -0.13, 0.02), 0.055, 0.26, MAT_GLASS, COLLECTION, gel, vertices=20)
    cylinder("level_sanitizer_fluid", (0, -0.13, -0.03), 0.046, 0.15, MAT_AMBER, COLLECTION, gel, vertices=18)
    cylinder("level_sanitizer_pump", (0, -0.13, 0.175), 0.024, 0.075, MAT_METAL, COLLECTION, gel, vertices=14)
    cube("level_sanitizer_lever", (0, -0.185, 0.155), (0.048, 0.11, 0.022), MAT_METAL, COLLECTION, gel, bevel=0.006)

    # Sputum sample tube in a wire stand on the instrument tray.
    tube = root("interaction_sample_tube", (-3.90, 3.10, 1.02))
    cube("level_sample_stand_base", (0, 0, 0), (0.15, 0.10, 0.022), MAT_METAL, COLLECTION, tube, bevel=0.006)
    for x in (-0.042, 0.042):
        cylinder("level_sample_stand_post", (x, 0, 0.055), 0.006, 0.10, MAT_METAL, COLLECTION, tube, vertices=8)
    cylinder("level_sample_glass", (0, 0, 0.085), 0.021, 0.15, MAT_GLASS, COLLECTION, tube, vertices=16)
    cylinder("level_sample_contents", (0, 0, 0.038), 0.017, 0.048, MAT_AMBER, COLLECTION, tube, vertices=14)
    cylinder("level_sample_stopper", (0, 0, 0.168), 0.023, 0.030, MAT_RUBBER, COLLECTION, tube, vertices=14)
    cube("level_sample_tag", (0, -0.024, 0.075), (0.030, 0.006, 0.045), MAT_PAPER, COLLECTION, tube, bevel=0.002)


# ---------------------------------------------------------------- night 4 ----

def build_mortuary_night():
    # Wheeled transport stretcher parked along the north corridor wall between
    # the doctors' room and lift doorways, leaving the walking lane clear.
    gurney = root("interaction_gurney", (9.60, 1.02, 0.03))
    cube("level_gurney_deck", (0, 0, 0.74), (1.92, 0.64, 0.070), MAT_ENAMEL, COLLECTION, gurney, bevel=0.030)
    cube("level_gurney_pad", (0, 0, 0.795), (1.84, 0.58, 0.055), MAT_DIRTY_LINEN, COLLECTION, gurney, bevel=0.030)
    for x in (-0.80, 0.80):
        for y in (-0.26, 0.26):
            cylinder("level_gurney_leg", (x, y, 0.37), 0.022, 0.68, MAT_METAL, COLLECTION, gurney, vertices=12)
            torus("level_gurney_castor", (x, y, 0.055), 0.055, 0.020, MAT_RUBBER, COLLECTION, gurney,
                  rotation=(math.radians(90), 0, 0))
    for x in (-0.86, 0.86):
        cylinder_between("level_gurney_rail_post_a", (x, -0.30, 0.78), (x, -0.30, 1.02), 0.016, MAT_METAL, COLLECTION, gurney, 10)
        cylinder_between("level_gurney_rail_post_b", (x, 0.30, 0.78), (x, 0.30, 1.02), 0.016, MAT_METAL, COLLECTION, gurney, 10)
        cylinder_between("level_gurney_rail_top", (x, -0.30, 1.02), (x, 0.30, 1.02), 0.018, MAT_METAL, COLLECTION, gurney, 10)
    cylinder_between("level_gurney_strut", (-0.80, 0, 0.42), (0.80, 0, 0.42), 0.016, MAT_METAL, COLLECTION, gurney, 10)

    # Rubberised transport bag lying on the deck; its own tarnished zip runs the
    # length of the lid so the "unzipped and empty" beat reads at a glance.
    bag = root("interaction_body_bag", (9.60, 1.02, 0.87))
    shell = sphere("level_bodybag_shell", (0, 0, 0), (0.86, 0.30, 0.13), MAT_RUBBER, COLLECTION, bag, 32)
    shell.scale.x *= 1.04
    cube("level_bodybag_zip", (0, 0, 0.115), (1.62, 0.030, 0.014), MAT_METAL, COLLECTION, bag, bevel=0.004)
    for x in (-0.62, 0.0, 0.62):
        cube("level_bodybag_strap", (x, 0, 0.02), (0.055, 0.62, 0.020), MAT_CLOTH, COLLECTION, bag, bevel=0.006)
    cube("level_bodybag_tag", (0.74, -0.16, 0.06), (0.16, 0.010, 0.10), MAT_PAPER, COLLECTION, bag, bevel=0.004)

    # Death certificate blank on the nurses' desk, beside the patient journal.
    form = root("interaction_death_certificate", (2.25, 2.60, 0.855))
    cube("level_certificate_sheet", (0, 0, 0), (0.42, 0.30, 0.006), MAT_PAPER, COLLECTION, form, bevel=0.002)
    cube("level_certificate_carbon", (0.012, -0.010, -0.007), (0.42, 0.30, 0.005), MAT_BAKELITE, COLLECTION, form, bevel=0.002)
    text_mesh("level_certificate_heading", "ВРАЧЕБНОЕ", (0, 0.085, 0.005), 0.038, MAT_INK, COLLECTION, form,
              rotation=(0, 0, 0))
    text_mesh("level_certificate_heading_two", "СВИДЕТЕЛЬСТВО", (0, 0.040, 0.005), 0.034, MAT_INK, COLLECTION, form,
              rotation=(0, 0, 0))
    for index, y in enumerate((-0.010, -0.055, -0.100)):
        cube("level_certificate_rule", (0, y, 0.004), (0.34, 0.004, 0.002), MAT_INK, COLLECTION, form, bevel=0.001)
    cylinder("level_certificate_pen", (0.16, -0.135, 0.010), 0.008, 0.17, MAT_BAKELITE, COLLECTION, form,
             rotation=(0, math.radians(90), math.radians(24)), vertices=10)


# ---------------------------------------------------------------- night 5 ----

def build_transfusion_night():
    # Squat blood refrigerator in the procedure room's south-west corner. The
    # "cabinet_body" in the shell name deliberately opts this prop INTO
    # _needs_collision so the player cannot walk through it.
    fridge = root("interaction_blood_fridge", (-4.58, 2.28, 0.0))
    cube("level_fridge_cabinet_body", (0, 0, 0.62), (0.66, 0.62, 1.24), MAT_ENAMEL, COLLECTION, fridge, bevel=0.030)
    cube("level_fridge_cabinet_door", (0, -0.315, 0.66), (0.60, 0.045, 1.06), MAT_ENAMEL, COLLECTION, fridge, bevel=0.025)
    cylinder_between("level_fridge_handle", (0.22, -0.36, 0.42), (0.22, -0.36, 0.92), 0.015, MAT_METAL, COLLECTION, fridge, 12)
    cube("level_fridge_gasket", (0, -0.292, 0.66), (0.62, 0.014, 1.10), MAT_RUBBER, COLLECTION, fridge, bevel=0.008)
    cube("level_fridge_thermometer", (-0.20, -0.345, 1.04), (0.16, 0.020, 0.11), MAT_BAKELITE, COLLECTION, fridge, bevel=0.008)
    sphere("level_fridge_thermo_dial", (-0.20, -0.358, 1.04), (0.052, 0.010, 0.052), MAT_LAMP_GLASS, COLLECTION, fridge, 16)
    cube("level_fridge_plinth", (0, 0, 0.045), (0.68, 0.64, 0.09), MAT_METAL, COLLECTION, fridge, bevel=0.014)
    for angle_x in (-0.24, 0.24):
        cube("level_fridge_vent_slat", (angle_x, 0.315, 1.16), (0.20, 0.030, 0.055), MAT_INK, COLLECTION, fridge, bevel=0.006)

    # Three donor units on top of the fridge, each with a different group label.
    groups = (
        ("first", "I(0)", MAT_RED, -0.19),
        ("second", "II(A)", MAT_BLUE, 0.0),
        ("third", "III(B)", MAT_GREEN_SIGN, 0.19),
    )
    for suffix, caption, label_material, offset_x in groups:
        bag = root("interaction_blood_bag_%s" % suffix, (-4.58 + offset_x, 2.20, 1.30))
        cube("level_blood_pouch", (0, 0, 0), (0.155, 0.050, 0.235), MAT_BLOOD, COLLECTION, bag, bevel=0.030)
        cube("level_blood_pouch_seal", (0, 0, 0.125), (0.150, 0.048, 0.022), MAT_RUBBER, COLLECTION, bag, bevel=0.008)
        cube("level_blood_group_label", (0, -0.031, 0.030), (0.115, 0.008, 0.075), label_material, COLLECTION, bag, bevel=0.004)
        text_mesh("level_blood_group_text", caption, (0, -0.038, 0.030), 0.034, MAT_PAPER, COLLECTION, bag)
        curve("level_blood_line", [(0.0, 0.0, -0.115), (0.035, -0.02, -0.20), (0.02, 0.0, -0.27)],
              0.007, MAT_GLASS, COLLECTION, bag)
        cylinder("level_blood_clamp", (0.028, -0.010, -0.205), 0.014, 0.028, MAT_BAKELITE, COLLECTION, bag,
                 rotation=(math.radians(90), 0, 0), vertices=10)

    # Compatibility table screwed to the procedure room's east wall.
    chart = root("interaction_blood_chart", (-0.14, 2.95, 1.70), rotation_z=90.0)
    cube("level_blood_chart_backing", (0, 0.02, 0), (0.72, 0.045, 0.56), MAT_BOARD, COLLECTION, chart, bevel=0.014)
    cube("level_blood_chart_sheet", (0, -0.010, 0), (0.64, 0.010, 0.48), MAT_PAPER, COLLECTION, chart, bevel=0.006)
    text_mesh("level_blood_chart_title", "ГРУППЫ КРОВИ", (0, -0.018, 0.185), 0.052, MAT_INK, COLLECTION, chart)
    for index, (caption, z) in enumerate((("I(0)", 0.085), ("II(A)", 0.000), ("III(B)", -0.085), ("IV(AB)", -0.170))):
        text_mesh("level_blood_chart_row", caption, (-0.19, -0.018, z), 0.042, MAT_INK, COLLECTION, chart)
        cube("level_blood_chart_swatch", (0.16, -0.016, z),
             (0.20, 0.006, 0.045), (MAT_RED, MAT_BLUE, MAT_GREEN_SIGN, MAT_AMBER)[index], COLLECTION, chart, bevel=0.003)
    for x in (-0.30, 0.30):
        sphere("level_blood_chart_screw", (x, -0.020, 0.245), (0.016, 0.008, 0.016), MAT_METAL, COLLECTION, chart, 10)


# ---------------------------------------------------------------- night 6 ----

def build_cold_night():
    # Square radiator key on a wire ring, medical storage shelf.
    key = root("interaction_radiator_key", (16.80, 4.30, 1.02))
    cube("level_radkey_shank", (0, 0, 0.025), (0.030, 0.115, 0.030), MAT_METAL, COLLECTION, key, bevel=0.005)
    cube("level_radkey_socket", (0, -0.070, 0.025), (0.055, 0.048, 0.055), MAT_METAL, COLLECTION, key, bevel=0.006)
    cube("level_radkey_wing", (0, 0.075, 0.025), (0.105, 0.045, 0.014), MAT_METAL, COLLECTION, key, bevel=0.005)
    torus("level_radkey_ring", (0, 0.125, 0.025), 0.040, 0.005, MAT_RUST, COLLECTION, key, rotation=(math.radians(90), 0, 0))

    # Stack of spare blankets in the sanitary room next to the clean linen.
    blankets = root("interaction_blanket_stack", (9.10, -5.18, 0.88))
    for index, (z, material) in enumerate(((0.0, MAT_BLANKET), (0.115, MAT_DIRTY_LINEN), (0.230, MAT_BLANKET))):
        layer = cube("level_blanket_fold", (0, 0, z), (0.74, 0.46, 0.105), material, COLLECTION, blankets, bevel=0.040)
        layer.rotation_euler.z = math.radians(-3 + index * 3)
        curve("level_blanket_hem", [(-0.30, -0.24, z + 0.05), (0, -0.245, z + 0.058), (0.30, -0.24, z + 0.05)],
              0.007, MAT_LINEN, COLLECTION, blankets)

    # Ward 3 already carries a cast-iron radiator under its window
    # (cast_iron_radiator_2_v2, spanning x -8.30..-6.40, z 0.19..0.99). An extra
    # radiator modelled beside it just read as a duplicate, so this prop is only
    # the bleed fitting screwed into that radiator's east end - which is the
    # part night 6 actually asks the player to turn with the square key.
    valve = root("interaction_radiator_valve", (-6.36, 5.53, 0.86))
    cylinder("level_radiator_bleed_collar", (-0.030, 0, 0), 0.036, 0.030, MAT_METAL, COLLECTION, valve,
             rotation=(0, math.radians(90), 0), vertices=16)
    cylinder("level_radiator_bleed_body", (0.030, 0, 0), 0.026, 0.095, MAT_RUST, COLLECTION, valve,
             rotation=(0, math.radians(90), 0), vertices=14)
    cube("level_radiator_bleed_square", (0.088, 0, 0), (0.030, 0.030, 0.030), MAT_METAL, COLLECTION, valve, bevel=0.004)
    sphere("level_radiator_bleed_drip", (0.02, -0.030, -0.080), (0.028, 0.014, 0.080), MAT_RUST, COLLECTION, valve, 12)

    # Upper transom sash with its latch, on the ward 3 north window.
    latch = root("interaction_window_latch", (-7.50, 5.48, 1.72))
    cube("level_transom_sash", (0, 0, 0), (0.78, 0.055, 0.44), MAT_ENAMEL, COLLECTION, latch, bevel=0.014)
    cube("level_transom_pane", (0, -0.012, 0), (0.68, 0.014, 0.34), MAT_GLASS, COLLECTION, latch, bevel=0.006)
    cube("level_transom_catch_plate", (0.33, -0.045, -0.12), (0.075, 0.030, 0.10), MAT_METAL, COLLECTION, latch, bevel=0.008)
    cylinder("level_transom_handle", (0.33, -0.075, -0.12), 0.014, 0.13, MAT_METAL, COLLECTION, latch,
             rotation=(math.radians(90), 0, math.radians(24)), vertices=12)
    cube("level_transom_draught_tape", (0, -0.030, 0.215), (0.74, 0.012, 0.030), MAT_DIRTY_LINEN, COLLECTION, latch, bevel=0.004)

    # Enamel kettle on the doctors' room desk.
    kettle = root("interaction_tea_kettle", (6.60, 4.30, 0.86))
    cylinder("level_kettle_body", (0, 0, 0.105), 0.135, 0.21, MAT_CERAMIC, COLLECTION, kettle, vertices=28)
    cylinder("level_kettle_shoulder", (0, 0, 0.222), 0.105, 0.035, MAT_CERAMIC, COLLECTION, kettle, vertices=24)
    cylinder("level_kettle_lid", (0, 0, 0.248), 0.070, 0.024, MAT_METAL, COLLECTION, kettle, vertices=20)
    sphere("level_kettle_knob", (0, 0, 0.272), (0.026, 0.026, 0.020), MAT_BAKELITE, COLLECTION, kettle, 14)
    curve("level_kettle_spout", [(0.115, 0.0, 0.16), (0.185, 0.0, 0.20), (0.215, 0.0, 0.255)],
          0.024, MAT_CERAMIC, COLLECTION, kettle)
    curve("level_kettle_handle", [(-0.115, 0.0, 0.19), (-0.185, 0.0, 0.27), (-0.06, 0.0, 0.30)],
          0.014, MAT_BAKELITE, COLLECTION, kettle)
    cube("level_kettle_scorch", (0, -0.132, 0.06), (0.13, 0.014, 0.09), MAT_INK, COLLECTION, kettle, bevel=0.006)


# ---------------------------------------------------------------- night 7 ----

def build_escape_night():
    # A pair of ward slippers left neatly by the fire door.
    slippers = root("interaction_hospital_slippers", (19.55, 0.60, 0.02))
    for index, y in enumerate((-0.10, 0.10)):
        shoe = sphere("level_slipper_sole", (0, y, 0.020), (0.135, 0.058, 0.022), MAT_BAKELITE, COLLECTION, slippers, 20)
        shoe.rotation_euler.z = math.radians(-8 + index * 16)
        vamp = sphere("level_slipper_vamp", (-0.045, y, 0.045), (0.075, 0.052, 0.038), MAT_DIRTY_LINEN, COLLECTION, slippers, 18)
        vamp.rotation_euler.z = math.radians(-8 + index * 16)
    cube("level_slipper_dirt_smear", (0.13, 0, 0.004), (0.17, 0.24, 0.004), MAT_DIRT, COLLECTION, slippers, bevel=0.002)

    # Wet footprints down the corridor. "dirt_patch", never "floor_*", so
    # _needs_collision leaves them alone - otherwise they would wall the corridor.
    trail = root("interaction_muddy_trail", (16.00, 0.30, 0.012))
    for index in range(9):
        x = -1.65 + index * 0.42
        y = 0.16 if index % 2 else -0.16
        print_patch = sphere("level_dirt_patch_step", (x, y, 0.0), (0.115, 0.058, 0.004),
                             MAT_DIRT, COLLECTION, trail, 16)
        print_patch.rotation_euler.z = math.radians(-16 if index % 2 else 16)
        sphere("level_dirt_patch_heel", (x - 0.085, y, 0.0), (0.052, 0.045, 0.0035), MAT_DIRT, COLLECTION, trail, 12)

    # Folded note left on the empty pillow in ward 1.
    note = root("interaction_bed_note", (-18.75, 4.34, 0.735))
    sheet = cube("level_note_sheet", (0, 0, 0), (0.20, 0.145, 0.004), MAT_PAPER, COLLECTION, note, bevel=0.002)
    sheet.rotation_euler.z = math.radians(-12)
    cube("level_note_crease", (0, 0, 0.003), (0.20, 0.006, 0.002), MAT_DIRTY_LINEN, COLLECTION, note,
         rotation=(0, 0, math.radians(-12)), bevel=0.001)
    for index, y in enumerate((0.035, 0.005, -0.025)):
        line = cube("level_note_line", (0, y, 0.004), (0.135, 0.005, 0.002), MAT_INK, COLLECTION, note, bevel=0.001)
        line.rotation_euler.z = math.radians(-12)

    # The escaped patient, found hunched on the east stair landing with a
    # blanket pulled over the head. No face is modelled at all - which is both
    # the scarier read and a deliberate dodge of the head-orientation trap that
    # fix_patient_head_orientation.py had to correct on the bedridden patients.
    # Pulled west off the 20.5 corridor end so the shoulder does not enter the
    # east stair wall once the -115 deg turn is applied.
    figure = root("interaction_escaped_patient", (19.45, -0.65, 0.0), rotation_z=-115.0)
    hips = sphere("level_escapee_hips", (0, 0, 0.30), (0.21, 0.19, 0.17), MAT_GOWN, COLLECTION, figure, 24)
    hips.rotation_euler.x = math.radians(-6)
    torso = sphere("level_escapee_torso", (0, -0.05, 0.58), (0.22, 0.20, 0.27), MAT_GOWN, COLLECTION, figure, 26)
    torso.rotation_euler.x = math.radians(24)
    for side in (-1.0, 1.0):
        cylinder_between("level_escapee_thigh", (side * 0.11, 0.02, 0.30), (side * 0.13, 0.36, 0.26),
                         0.075, MAT_GOWN, COLLECTION, figure, 14)
        cylinder_between("level_escapee_shin", (side * 0.13, 0.36, 0.26), (side * 0.12, 0.30, 0.05),
                         0.058, MAT_SKIN, COLLECTION, figure, 14)
        sphere("level_escapee_foot", (side * 0.12, 0.24, 0.045), (0.062, 0.105, 0.042), MAT_SKIN, COLLECTION, figure, 14)
        cylinder_between("level_escapee_upper_arm", (side * 0.19, -0.06, 0.72), (side * 0.20, 0.14, 0.46),
                         0.052, MAT_GOWN, COLLECTION, figure, 12)
        cylinder_between("level_escapee_forearm", (side * 0.20, 0.14, 0.46), (side * 0.10, 0.26, 0.34),
                         0.044, MAT_SKIN, COLLECTION, figure, 12)
        sphere("level_escapee_hand", (side * 0.09, 0.28, 0.32), (0.052, 0.070, 0.034), MAT_SKIN, COLLECTION, figure, 14)
    # The blanket cowl: a closed hood, so the head under it is never seen.
    cowl = sphere("level_escapee_cowl", (0, -0.03, 0.90), (0.235, 0.245, 0.225), MAT_BLANKET, COLLECTION, figure, 28)
    cowl.rotation_euler.x = math.radians(16)
    drape = sphere("level_escapee_cowl_drape", (0, 0.02, 0.70), (0.27, 0.26, 0.20), MAT_BLANKET, COLLECTION, figure, 26)
    drape.rotation_euler.x = math.radians(28)
    shadow = sphere("level_escapee_cowl_void", (0, -0.20, 0.86), (0.135, 0.075, 0.125), MAT_INK, COLLECTION, figure, 20)
    shadow.rotation_euler.x = math.radians(12)


# ---------------------------------------------------------------- night 8 ----

def build_inspection_night():
    # Duty logbook waiting to be filled in, on the nurses' desk.
    logbook = root("interaction_duty_journal_form", (3.40, 2.86, 0.855))
    cube("level_dutylog_cover", (0, 0, 0), (0.46, 0.33, 0.020), MAT_BOARD, COLLECTION, logbook, bevel=0.008)
    cube("level_dutylog_pages", (0.010, 0, 0.017), (0.43, 0.30, 0.016), MAT_PAPER, COLLECTION, logbook, bevel=0.004)
    cube("level_dutylog_spine", (-0.235, 0, 0.006), (0.030, 0.33, 0.036), MAT_BAKELITE, COLLECTION, logbook, bevel=0.008)
    text_mesh("level_dutylog_title", "ЖУРНАЛ", (0.02, 0.095, 0.026), 0.042, MAT_INK, COLLECTION, logbook, rotation=(0, 0, 0))
    text_mesh("level_dutylog_subtitle", "ДЕЖУРСТВ", (0.02, 0.050, 0.026), 0.036, MAT_INK, COLLECTION, logbook, rotation=(0, 0, 0))
    for index, y in enumerate((0.005, -0.030, -0.065, -0.100)):
        cube("level_dutylog_rule", (0.02, y, 0.026), (0.36, 0.004, 0.002), MAT_INK, COLLECTION, logbook, bevel=0.001)
    cylinder("level_dutylog_pen", (0.20, -0.115, 0.030), 0.008, 0.16, MAT_BAKELITE, COLLECTION, logbook,
             rotation=(0, math.radians(90), math.radians(-18)), vertices=10)

    # Stacking chair dragged across the corridor. No name matches the collision
    # list, so it is an eyesore to clear rather than a physical roadblock.
    chair = root("interaction_misplaced_chair", (0.20, 0.35, 0.0), rotation_z=38.0)
    cube("level_chair_seat_pan", (0, 0, 0.44), (0.42, 0.40, 0.045), MAT_BAKELITE, COLLECTION, chair, bevel=0.018)
    back = cube("level_chair_back_rest", (0, 0.185, 0.68), (0.40, 0.045, 0.30), MAT_BAKELITE, COLLECTION, chair, bevel=0.018)
    back.rotation_euler.x = math.radians(-11)
    for x in (-0.17, 0.17):
        for y in (-0.16, 0.16):
            cylinder("level_chair_leg", (x, y, 0.215), 0.017, 0.43, MAT_METAL, COLLECTION, chair, vertices=10)
    cylinder_between("level_chair_brace_front", (-0.17, -0.16, 0.16), (0.17, -0.16, 0.16), 0.013, MAT_METAL, COLLECTION, chair, 10)
    cylinder_between("level_chair_brace_side", (-0.17, -0.16, 0.16), (-0.17, 0.16, 0.16), 0.013, MAT_METAL, COLLECTION, chair, 10)
    cylinder_between("level_chair_upright", (-0.17, 0.16, 0.44), (-0.17, 0.185, 0.80), 0.016, MAT_METAL, COLLECTION, chair, 10)
    cylinder_between("level_chair_upright_r", (0.17, 0.16, 0.44), (0.17, 0.185, 0.80), 0.016, MAT_METAL, COLLECTION, chair, 10)

    # Trodden-in dirt on the corridor linoleum. Same naming caution as the trail.
    dirt = root("interaction_floor_dirt", (-11.00, 0.0, 0.012))
    for index, (x, y, sx, sy) in enumerate(((0.0, 0.0, 0.62, 0.42), (0.52, -0.22, 0.38, 0.26),
                                             (-0.48, 0.20, 0.44, 0.30), (0.18, 0.34, 0.30, 0.22))):
        smear = sphere("level_dirt_patch_smear", (x, y, 0.0), (sx, sy, 0.004), MAT_DIRT, COLLECTION, dirt, 20)
        smear.rotation_euler.z = math.radians(index * 27)
    for x, y in ((-0.20, -0.30), (0.34, 0.10), (-0.66, -0.06)):
        sphere("level_dirt_patch_speck", (x, y, 0.001), (0.075, 0.055, 0.003), MAT_INK, COLLECTION, dirt, 12)


# ---------------------------------------------------------------- night 9 ----

def build_fire_night():
    # Wall-bracketed foam extinguisher in the east corridor.
    extinguisher = root("interaction_fire_extinguisher", (14.50, 1.36, 0.0))
    cylinder("level_extinguisher_cylinder", (0, 0, 0.55), 0.098, 0.62, MAT_FIRE_RED, COLLECTION, extinguisher, vertices=24)
    sphere("level_extinguisher_dome", (0, 0, 0.86), (0.098, 0.098, 0.075), MAT_FIRE_RED, COLLECTION, extinguisher, 22)
    sphere("level_extinguisher_base_dome", (0, 0, 0.245), (0.098, 0.098, 0.060), MAT_FIRE_RED, COLLECTION, extinguisher, 22)
    cylinder("level_extinguisher_neck", (0, 0, 0.925), 0.032, 0.070, MAT_METAL, COLLECTION, extinguisher, vertices=14)
    cube("level_extinguisher_lever", (0, -0.045, 0.965), (0.048, 0.135, 0.024), MAT_METAL, COLLECTION, extinguisher, bevel=0.006)
    cylinder("level_extinguisher_pin", (0.045, 0.0, 0.955), 0.007, 0.055, MAT_RUST, COLLECTION, extinguisher,
             rotation=(0, math.radians(90), 0), vertices=8)
    curve("level_extinguisher_hose", [(0.03, -0.09, 0.93), (0.17, -0.13, 0.72), (0.13, -0.06, 0.44)],
          0.016, MAT_RUBBER, COLLECTION, extinguisher)
    cylinder("level_extinguisher_horn", (0.125, -0.055, 0.40), 0.045, 0.13, MAT_BAKELITE, COLLECTION, extinguisher,
             rotation=(math.radians(14), 0, 0), vertices=16)
    cube("level_extinguisher_label", (0, -0.100, 0.60), (0.13, 0.010, 0.20), MAT_PAPER, COLLECTION, extinguisher, bevel=0.006)
    cube("level_extinguisher_bracket", (0, 0.085, 0.62), (0.15, 0.070, 0.075), MAT_METAL, COLLECTION, extinguisher, bevel=0.010)

    # Smouldering cable duct above the fuse panel: char, sagging conduit and a
    # slow roll of smoke. Nothing here is solid.
    # Top puff reaches +1.21 locally; 1.85 keeps it under the 3.06 ceiling slab.
    smoke = root("interaction_smoke_source", (-15.50, 1.30, 1.85))
    cube("level_smoke_duct", (0, 0.10, 0.28), (1.05, 0.16, 0.14), MAT_METAL, COLLECTION, smoke, bevel=0.014)
    cube("level_smoke_char", (0.06, 0.015, 0.24), (0.52, 0.055, 0.14), MAT_INK, COLLECTION, smoke, bevel=0.010)
    for index, (x, z, scale) in enumerate(((-0.06, 0.42, 0.20), (0.10, 0.60, 0.27), (-0.02, 0.78, 0.33),
                                            (0.16, 0.94, 0.38))):
        puff = sphere("level_smoke_puff", (x, 0.02, z), (scale, scale * 0.62, scale * 0.72),
                      MAT_SMOKE, COLLECTION, smoke, 20)
        puff.rotation_euler.z = math.radians(index * 31)
    for x in (-0.34, 0.02, 0.38):
        curve("level_smoke_cable", [(x - 0.06, 0.02, 0.20), (x, 0.0, 0.10), (x + 0.07, 0.03, 0.19)],
              0.011, MAT_INK, COLLECTION, smoke)
    sphere("level_smoke_ember", (0.05, 0.0, 0.235), (0.045, 0.020, 0.030), MAT_FIRE_RED, COLLECTION, smoke, 12)

    # Fire alarm annunciator on the corridor wall by the nurses' post.
    panel = root("interaction_fire_alarm_panel", (-0.50, 1.48, 1.78))
    cube("level_alarm_case", (0, 0.05, 0), (0.44, 0.13, 0.34), MAT_FIRE_RED, COLLECTION, panel, bevel=0.016)
    cube("level_alarm_face", (0, -0.028, 0), (0.37, 0.022, 0.27), MAT_BAKELITE, COLLECTION, panel, bevel=0.010)
    for index, x in enumerate((-0.11, 0.0, 0.11)):
        sphere("level_alarm_indicator", (x, -0.046, 0.065), (0.030, 0.012, 0.030),
               (MAT_FIRE_RED, MAT_AMBER, MAT_GREEN_SIGN)[index], COLLECTION, panel, 14)
    text_mesh("level_alarm_caption", "ПОЖАР", (0, -0.044, -0.055), 0.048, MAT_PAPER, COLLECTION, panel)
    cylinder("level_alarm_bell", (0.0, -0.075, 0.185), 0.075, 0.045, MAT_METAL, COLLECTION, panel,
             rotation=(math.radians(90), 0, 0), vertices=20)
    sphere("level_alarm_bell_dome", (0.0, -0.098, 0.185), (0.075, 0.030, 0.075), MAT_METAL, COLLECTION, panel, 18)
    cube("level_alarm_break_glass", (0, -0.042, -0.145), (0.16, 0.012, 0.075), MAT_GLASS, COLLECTION, panel, bevel=0.004)


# --------------------------------------------------------------- night 10 ----

def build_surgery_night():
    # Sterilising drum (bix) standing open beside the existing sterilizer.
    bix = root("interaction_sterile_bix", (-0.92, 2.58, 0.0))
    cylinder("level_bix_shell", (0, 0, 0.24), 0.215, 0.44, MAT_METAL, COLLECTION, bix, vertices=28)
    torus("level_bix_band_lower", (0, 0, 0.075), 0.216, 0.014, MAT_RUST, COLLECTION, bix)
    torus("level_bix_band_upper", (0, 0, 0.415), 0.216, 0.014, MAT_METAL, COLLECTION, bix)
    lid = cylinder("level_bix_lid", (0.14, -0.16, 0.50), 0.225, 0.045, MAT_ENAMEL, COLLECTION, bix, vertices=28)
    lid.rotation_euler.x = math.radians(22)
    cylinder_between("level_bix_lid_handle", (0.06, -0.20, 0.545), (0.22, -0.12, 0.545), 0.012, MAT_METAL, COLLECTION, bix, 10)
    for angle in range(0, 360, 60):
        radians = math.radians(angle)
        sphere("level_bix_vent_hole", (math.cos(radians) * 0.217, math.sin(radians) * 0.217, 0.30),
               (0.020, 0.011, 0.020), MAT_INK, COLLECTION, bix, 10)
    cube("level_bix_gauze_pack", (0, 0, 0.455), (0.30, 0.26, 0.075), MAT_LINEN, COLLECTION, bix, bevel=0.020)
    # The 02:10 beat calls these "already used": rust-brown staining on the packs.
    sphere("level_bix_stain", (0.06, -0.04, 0.492), (0.095, 0.070, 0.006), MAT_BLOOD, COLLECTION, bix, 16)
    cube("level_bix_indicator_tape", (0, -0.13, 0.47), (0.17, 0.010, 0.030), MAT_AMBER, COLLECTION, bix, bevel=0.004)

    # Ceiling-mounted shadowless operating lamp over the procedure couch.
    lamp = root("interaction_surgical_lamp", (-2.60, 4.20, 2.34))
    cylinder("level_oplamp_ceiling_plate", (0, 0, 0.30), 0.115, 0.055, MAT_METAL, COLLECTION, lamp, vertices=20)
    cylinder_between("level_oplamp_stem", (0, 0, 0.28), (0, 0.18, 0.06), 0.030, MAT_METAL, COLLECTION, lamp, 14)
    sphere("level_oplamp_knuckle", (0, 0.18, 0.06), (0.055, 0.055, 0.055), MAT_METAL, COLLECTION, lamp, 16)
    dish = sphere("level_oplamp_dish", (0, 0.22, -0.10), (0.42, 0.42, 0.13), MAT_LAMP, COLLECTION, lamp, 32)
    dish.scale.z *= 0.8
    cylinder("level_oplamp_rim", (0, 0.22, -0.175), 0.415, 0.030, MAT_METAL, COLLECTION, lamp, vertices=32)
    for index in range(6):
        angle = math.tau * index / 6.0
        sphere("level_oplamp_bulb", (math.cos(angle) * 0.235, 0.22 + math.sin(angle) * 0.235, -0.185),
               (0.070, 0.070, 0.040), MAT_LAMP_GLASS, COLLECTION, lamp, 16)
    sphere("level_oplamp_centre_bulb", (0, 0.22, -0.19), (0.085, 0.085, 0.045), MAT_LAMP_GLASS, COLLECTION, lamp, 18)
    cylinder("level_oplamp_grip", (0, 0.22, -0.235), 0.026, 0.10, MAT_BAKELITE, COLLECTION, lamp, vertices=14)

    # Sterile gown and gloves hanging on the procedure room's west wall.
    gown = root("interaction_surgical_gown", (-4.93, 4.20, 1.52), rotation_z=90.0)
    cylinder_between("level_gown_peg", (0, 0.10, 0.44), (0, -0.02, 0.44), 0.014, MAT_METAL, COLLECTION, gown, 10)
    sphere("level_gown_peg_knob", (0, -0.03, 0.44), (0.028, 0.028, 0.028), MAT_BAKELITE, COLLECTION, gown, 12)
    body = cube("level_gown_body", (0, -0.04, 0.0), (0.52, 0.075, 0.86), MAT_LINEN, COLLECTION, gown, bevel=0.045)
    body.rotation_euler.y = math.radians(2)
    cube("level_gown_shoulder", (0, -0.04, 0.395), (0.44, 0.085, 0.14), MAT_LINEN, COLLECTION, gown, bevel=0.055)
    for side in (-1.0, 1.0):
        sleeve = cube("level_gown_sleeve", (side * 0.30, -0.045, 0.14), (0.14, 0.075, 0.50), MAT_LINEN, COLLECTION, gown, bevel=0.040)
        sleeve.rotation_euler.y = math.radians(side * 9)
        cube("level_gown_cuff", (side * 0.335, -0.045, -0.115), (0.135, 0.080, 0.070), MAT_DIRTY_LINEN, COLLECTION, gown, bevel=0.020)
    cube("level_gown_tie", (0.09, -0.082, -0.24), (0.030, 0.020, 0.36), MAT_LINEN, COLLECTION, gown, bevel=0.010)
    for side in (-1.0, 1.0):
        glove = sphere("level_gown_glove", (side * 0.335, -0.10, -0.235), (0.062, 0.038, 0.115), MAT_RUBBER, COLLECTION, gown, 18)
        glove.rotation_euler.y = math.radians(side * 6)


# --------------------------------------------------------------- night 11 ----

def build_zero_night():
    # The door that is not on the plan, in the blank stretch of north wall
    # between the ward 3 (x -8.05) and procedure room (x -3.05) doorways.
    # "door" in the leaf names deliberately opts it into _needs_collision.
    zero = root("interaction_zero_door", (-5.55, 1.56, 0.0))
    cube("level_zero_door_frame_head", (0, 0.03, 2.12), (1.26, 0.14, 0.14), MAT_ENAMEL, COLLECTION, zero, bevel=0.020)
    for x in (-0.60, 0.60):
        cube("level_zero_door_frame_jamb", (x, 0.03, 1.05), (0.11, 0.14, 2.10), MAT_ENAMEL, COLLECTION, zero, bevel=0.018)
    leaf = cube("level_zero_door_leaf", (0, -0.02, 1.03), (1.08, 0.060, 2.02), MAT_ENAMEL, COLLECTION, zero, bevel=0.016)
    for index, z in enumerate((0.46, 1.03, 1.60)):
        cube("level_zero_door_panel_inset", (0, -0.055, z), (0.82, 0.014, 0.42), MAT_BOARD, COLLECTION, zero, bevel=0.014)
    cylinder("level_zero_door_handle_rose", (0.40, -0.062, 1.02), 0.045, 0.020, MAT_METAL, COLLECTION, zero,
             rotation=(math.radians(90), 0, 0), vertices=16)
    cylinder_between("level_zero_door_lever", (0.40, -0.085, 1.02), (0.26, -0.085, 0.985), 0.017, MAT_METAL, COLLECTION, zero, 12)
    cube("level_zero_door_keyhole_plate", (0.40, -0.070, 0.90), (0.055, 0.014, 0.090), MAT_BAKELITE, COLLECTION, zero, bevel=0.006)
    # Deliberately blank: the plaque screwed above it carries no number.
    cube("level_zero_plaque_blank", (0, -0.058, 1.86), (0.40, 0.016, 0.15), MAT_PAPER, COLLECTION, zero, bevel=0.006)
    for x in (-0.15, 0.15):
        sphere("level_zero_plaque_screw", (x, -0.068, 1.86), (0.013, 0.007, 0.013), MAT_METAL, COLLECTION, zero, 10)

    # Long-shanked key on a wooden fob, in the nurses' desk drawer.
    key = root("interaction_zero_key", (1.50, 2.42, 0.855))
    cylinder("level_zerokey_shank", (0, 0, 0.010), 0.009, 0.20, MAT_RUST, COLLECTION, key,
             rotation=(0, math.radians(90), 0), vertices=10)
    torus("level_zerokey_bow", (-0.115, 0, 0.010), 0.038, 0.008, MAT_RUST, COLLECTION, key, rotation=(0, math.radians(90), 0))
    cube("level_zerokey_ward_bit", (0.082, 0, -0.014), (0.055, 0.012, 0.040), MAT_RUST, COLLECTION, key, bevel=0.003)
    cube("level_zerokey_ward_bit_two", (0.058, 0, -0.010), (0.020, 0.012, 0.026), MAT_RUST, COLLECTION, key, bevel=0.002)
    fob = cube("level_zerokey_fob", (-0.185, 0.01, 0.008), (0.085, 0.050, 0.012), MAT_PAPER, COLLECTION, key, bevel=0.005)
    fob.rotation_euler.z = math.radians(-14)
    text_mesh("level_zerokey_fob_text", "0", (-0.185, 0.005, 0.016), 0.030, MAT_INK, COLLECTION, key, rotation=(0, 0, 0))

    # The admission card for a room that does not exist.
    card = root("interaction_zero_card", (2.10, 3.06, 0.855))
    sheet = cube("level_zerocard_sheet", (0, 0, 0), (0.26, 0.36, 0.005), MAT_PAPER, COLLECTION, card, bevel=0.002)
    sheet.rotation_euler.z = math.radians(7)
    text_mesh("level_zerocard_heading", "ПАЛАТА 0", (0, 0.125, 0.004), 0.040, MAT_INK, COLLECTION, card, rotation=(0, 0, 0))
    for index, y in enumerate((0.060, 0.020, -0.020, -0.060, -0.100)):
        rule = cube("level_zerocard_rule", (0, y, 0.004), (0.20, 0.004, 0.002), MAT_INK, COLLECTION, card, bevel=0.001)
        rule.rotation_euler.z = math.radians(7)
    cube("level_zerocard_stamp", (0.055, -0.135, 0.005), (0.105, 0.075, 0.003), MAT_BLUE, COLLECTION, card,
         rotation=(0, 0, math.radians(-19)), bevel=0.002)
    cube("level_zerocard_clip", (-0.085, 0.155, 0.010), (0.045, 0.055, 0.014), MAT_METAL, COLLECTION, card, bevel=0.005)


BUILDERS = (
    build_power_night,
    build_quarantine_night,
    build_mortuary_night,
    build_transfusion_night,
    build_cold_night,
    build_escape_night,
    build_inspection_night,
    build_fire_night,
    build_surgery_night,
    build_zero_night,
)


def run():
    global COLLECTION
    existing = bpy.data.collections.get(COLLECTION_NAME)
    if existing:
        for obj in list(existing.all_objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(existing)
    COLLECTION = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(COLLECTION)

    ROOTS.clear()
    for builder in BUILDERS:
        builder()

    # A duplicate root would come back from Blender as "...001" and main.gd's
    # exact-name lookup would silently skip it, so fail loudly instead.
    duplicates = [name for name in ROOTS if ROOTS.count(name) > 1]
    missing = [name for name in ROOTS if bpy.data.objects.get(name) is None]
    if duplicates or missing:
        raise RuntimeError("root name problem: duplicates=%s missing=%s" % (sorted(set(duplicates)), missing))

    bpy.context.view_layer.update()
    bpy.context.scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("LEVEL_PROPS_BUILT roots=%d objects=%d" % (len(ROOTS), len(COLLECTION.all_objects)))
    print("LEVEL_PROP_ROOTS=%s" % sorted(ROOTS))


run()
