# -*- coding: utf-8 -*-
"""Write project/locale/palata.csv from tools/i18n/translations.json.

The Russian source text is the msgid, so the CSV has to reproduce it byte for
byte - including the newlines inside the night briefs. A hand-written CSV with
a literal backslash-n does NOT work: GDScript's "...\\n..." is a real line feed,
the CSV's is two characters, the keys do not match and tr() silently hands back
the Russian. Python's csv module quotes embedded newlines correctly and Godot's
importer reads them back, which validate_localization.gd checks.

translations.json is a flat object: {"русская строка": "English string"}.
"""
import csv
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCE = os.path.join(ROOT, "tools", "i18n", "translations.json")
TARGET = os.path.join(ROOT, "project", "locale", "palata.csv")

pairs = json.load(open(SOURCE, encoding="utf-8"))
missing = [ru for ru, en in pairs.items() if not en or not en.strip()]
if missing:
    raise SystemExit("untranslated entries: %d, first: %r" % (len(missing), missing[0]))

buffer = io.StringIO()
writer = csv.writer(buffer, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL,
                    lineterminator="\n")
writer.writerow(["keys", "ru", "en"])
for russian, english in pairs.items():
    writer.writerow([russian, russian, english])

os.makedirs(os.path.dirname(TARGET), exist_ok=True)
open(TARGET, "w", encoding="utf-8", newline="").write(buffer.getvalue())
print("LOCALE_CSV rows=%d path=%s" % (len(pairs), TARGET))
