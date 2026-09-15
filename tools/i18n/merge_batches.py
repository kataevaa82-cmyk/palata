# -*- coding: utf-8 -*-
"""Merge tools/i18n/batch_*.json into translations.json and report coverage.

Coverage is measured against extract_strings.py, so a string added to the game
later shows up here as missing instead of quietly shipping in Russian.
"""
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TARGET = os.path.join(HERE, "translations.json")

# Russian text the player never sees: a node name, and the substring probes
# _die() used to classify a death by. Translating these would rename a node and
# silently break the ending selection, so they are excluded from coverage
# instead of being handed a translation nobody may use.
INTERNAL = {
    "ПредметВИнвентаре",
    "санитарк",
    "медсестр",
    "луч",
    "медицин",
    "главная_медсестра",
    "пожарная_сирена",
    # The language button always names the language it switches TO, in that
    # language: "EN" while playing in Russian, "РУС" while playing in English.
    # Translating it would make the button read "EN" in both modes.
    "РУС",
}

merged = {}
for path in sorted(glob.glob(os.path.join(HERE, "batch_*.json"))):
    batch = json.load(open(path, encoding="utf-8"))
    for russian, english in batch.items():
        if russian in merged and merged[russian] != english:
            print("CONFLICT %r: %r vs %r" % (russian, merged[russian], english))
        merged[russian] = english

extracted = json.loads(subprocess.run(
    [sys.executable, os.path.join(HERE, "extract_strings.py"), "--json"],
    capture_output=True, check=True,
    env=dict(os.environ, PYTHONIOENCODING="utf-8")).stdout.decode("utf-8"))
wanted = [hit["text"] for hit in extracted if hit["text"] not in INTERNAL]

missing = [text for text in wanted if text not in merged]
extra = [text for text in merged if text not in wanted]

json.dump(merged, open(TARGET, "w", encoding="utf-8"),
          ensure_ascii=False, indent=1, sort_keys=True)
print("MERGED translated=%d wanted=%d missing=%d extra=%d" % (
    len(merged), len(wanted), len(missing), len(extra)))
if "--list-missing" in sys.argv:
    by_file = {}
    for hit in extracted:
        if hit["text"] in missing:
            by_file.setdefault(hit["file"], []).append(hit["text"])
    for path in sorted(by_file):
        print("## %s (%d)" % (path, len(by_file[path])))
        for text in by_file[path]:
            print(repr(text))
