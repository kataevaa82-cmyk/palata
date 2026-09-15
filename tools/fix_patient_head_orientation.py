"""Rebuild the 7 ward patients, then lay each patient's head flat so the face
looks up at the ceiling instead of sideways into the wall/headboard.

build_care_gameplay_v2.py's HEAD_PROFILE authors the head as an upright,
standing head: local Z is the chin-to-crown axis, local Y is the face-forward
(nose) axis. That is correct for a person standing, but every patient here is
lying on their back, and the rig never re-orients the head into the body's
own "lying flat" frame (where Z stays vertical/up and Y runs along the bed
from foot to head). The result: the whole head - and every brow/eye/nostril/
lip/ear/hair mesh riding on its face_surface_y() surface - pointed its face
in the bed's lengthwise direction (into the headboard) with the actual chin-
to-crown axis standing straight up out of the mattress.

Swapping y and z (relative to their respective anchors, HEAD_Y and
HEAD_CHIN_Z) is a clean fix: it is not a rotation (getting the turn direction
right by trial and error kept flipping the face into the pillow - see session
history), just a direct axis relabelling, so it can't be off by a sign. Chin
stays near the neck join, crown extends further up the bed, and the face
bulge now points toward +Z (the ceiling), exactly matching how the rest of
the body (torso/hips laid out with Y as the foot-to-head axis, Z ~ constant
bed height) was already built.
"""

import bpy

HEAD_Y = 0.600
HEAD_CHIN_Z = 0.955

FACE_SUFFIXES = ("_head", "_neck", "_ear_", "_brow_", "_closed_eye_",
                  "_nostril", "_lip", "_hair")

PATIENT_ROOTS = (
    "ward_1_bed_1_patient_v3",
    "ward_2_bed_1_patient_v3",
    "ward_3_bed_1_patient_v3",
    "ward_4_bed_1_patient_v3",
    "ward_5_bed_1_patient_v3",
    "ward_6_bed_1_patient_v3",
    "ward_6_bed_2_patient_v3",
)


def lay_head_flat(root_name):
    objs = [bpy.data.objects[name] for name in bpy.data.objects.keys()
            if name.startswith(root_name + "_patient_")
            and any(k in name for k in FACE_SUFFIXES)]
    for obj in objs:
        me = obj.data
        for v in me.vertices:
            x, y, z = v.co
            v.co.y = HEAD_Y + (z - HEAD_CHIN_Z)
            v.co.z = HEAD_CHIN_Z + (y - HEAD_Y)
        me.update()
    return len(objs)


def run():
    namespace = {"CARE_GAMEPLAY_LIBRARY_ONLY": True}
    exec(compile(open("C:/palata/tools/build_care_gameplay_v2.py", encoding="utf-8").read(),
                 "build_care_gameplay_v2.py", "exec"), namespace)
    rebuilt = namespace["rebuild_patients"]()

    fixed = {}
    for root_name in PATIENT_ROOTS:
        fixed[root_name] = lay_head_flat(root_name)

    bpy.context.view_layer.update()
    bpy.context.scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath="C:/palata/palata_zero.blend")
    print("PATIENTS_REBUILT_AND_FLATTENED", "rebuilt=", rebuilt, "fixed=", fixed)


run()
