import traceback


try:
    source_path = "C:/palata/tools/improve_violent_patient_walk.py"
    with open(source_path, "r", encoding="utf-8") as handle:
        exec(compile(handle.read(), source_path, "exec"), {"__name__": "__main__"})
except Exception:
    print(traceback.format_exc())
