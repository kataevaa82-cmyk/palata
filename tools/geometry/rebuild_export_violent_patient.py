# -*- coding: utf-8 -*-
"""Rebuild the violent patient geometry, retarget the walk cycle, export GLB.

Must be launched with palata_zero.blend (the violent-patient work file), not
hospital_models_work.blend.

Run: blender --background palata_zero.blend --python this_file.py
"""
import runpy
import shutil

import bpy

runpy.run_path("C:/palata/tools/rebuild_violent_patient_human.py")
runpy.run_path("C:/palata/tools/improve_violent_patient_walk.py")

src = "C:/palata/violent_patient_v1.glb"
dst = "C:/palata/project/assets/models/violent_patient_v1.glb"
shutil.copy2(src, dst)
print("VIOLENT_PATIENT_EXPORTED", src, "godot", dst)
print("VIOLENT_BLEND", bpy.data.filepath)
