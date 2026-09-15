# -*- coding: utf-8 -*-
"""Export the open hospital blend to palata_zero.glb and copy it into Godot."""
import runpy
import shutil

runpy.run_path("C:/palata/tools/geometry/export_hospital_glb.py")
src = "C:/palata/palata_zero.glb"
dst = "C:/palata/project/assets/models/palata_zero.glb"
shutil.copy2(src, dst)
print("HOSPITAL_COPIED_TO_GODOT", dst)
