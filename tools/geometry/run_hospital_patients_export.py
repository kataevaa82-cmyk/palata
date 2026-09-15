# -*- coding: utf-8 -*-
"""Improve ward patients only, then export the hospital GLB."""
import runpy

runpy.run_path("C:/palata/tools/geometry/improve_ward_patient_geometry.py")
runpy.run_path("C:/palata/tools/geometry/export_hospital_and_copy.py")
print("HOSPITAL_PATIENTS_EXPORT_DONE")
