"""Rebuild only the 7 bedridden ward patients' heads/faces.

Loads build_care_gameplay_v2.py as a library (CARE_GAMEPLAY_LIBRARY_ONLY
suppresses its own run() call) and invokes rebuild_patients() instead, so
interaction_medical_cart, the clock, and the 15 build_props() objects that
main.gd binds by name are left untouched.
"""

import bpy

namespace = {"CARE_GAMEPLAY_LIBRARY_ONLY": True}
exec(compile(open("C:/palata/tools/build_care_gameplay_v2.py", encoding="utf-8").read(),
             "build_care_gameplay_v2.py", "exec"), namespace)

rebuilt = namespace["rebuild_patients"]()
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath="C:/palata/palata_zero.blend")
print("WARD_PATIENT_FACES_REBUILT patients=", rebuilt)
