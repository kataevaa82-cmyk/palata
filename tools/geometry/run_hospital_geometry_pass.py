# -*- coding: utf-8 -*-
"""One Blender session: improve ward patients, soften remaining furniture, export.

Run: blender --background hospital_models_work.blend --python this_file.py
"""
import runpy

runpy.run_path("C:/palata/tools/geometry/improve_ward_patient_geometry.py")
runpy.run_path("C:/palata/tools/geometry/improve_remaining_scene_geometry.py")
runpy.run_path("C:/palata/tools/geometry/export_hospital_and_copy.py")
print("HOSPITAL_GEOMETRY_PASS_DONE")
