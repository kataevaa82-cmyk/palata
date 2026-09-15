# -*- coding: utf-8 -*-
"""Check the English build the way a reviewer would: not "does the test pass"
but "is there anything the player can still see in Russian".

Writes a report next to itself so console codepages cannot mangle it.
"""
import csv
import io
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
PROJECT = ROOT / "project"
OUT = ROOT / "build" / "locale_audit.txt"

CYRILLIC = re.compile(r"[Ѐ-ӿ]")
STRING = re.compile(r'"((?:[^"\\]|\\.)*)"')

report = []


def unescape(raw):
    """GDScript and .tscn store newlines as backslash-n; the CSV stores the
    real character. Compare like for like or every multi-line string looks
    untranslated."""
    return (raw.replace(chr(92) + "n", chr(10))
               .replace(chr(92) + "t", chr(9))
               .replace(chr(92) + chr(34), chr(34))
               .replace(chr(92) + chr(92), chr(92)))


def say(line=""):
    report.append(line)


rows = list(csv.reader(io.open(PROJECT / "locale" / "palata.csv", encoding="utf-8")))
header, rows = rows[0], rows[1:]
keys = {r[0] for r in rows}
say("CSV %s rows=%d columns=%s" % ("locale/palata.csv", len(rows), header))

blank_en = [r[0] for r in rows if len(r) < 3 or not r[2].strip()]
cyr_en = [r[0] for r in rows if len(r) > 2 and CYRILLIC.search(r[2])]
say("  untranslated (empty en): %d" % len(blank_en))
for k in blank_en[:20]:
    say("    %s" % k)
say("  en still containing Cyrillic: %d" % len(cyr_en))
for k in cyr_en[:20]:
    say("    %s -> %s" % (k, dict((r[0], r[2]) for r in rows)[k]))

# ---------------------------------------------------------------- sources ----

say()
say("RUSSIAN LITERALS IN CODE THAT ARE NOT LOCALISATION KEYS")
missing = []
for path in sorted(PROJECT.rglob("*.gd")):
    text = path.read_text(encoding="utf-8")
    for line_no, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        for match in STRING.finditer(line):
            value = unescape(match.group(1))
            if not CYRILLIC.search(value):
                continue
            if value in keys:
                continue
            missing.append((path.relative_to(ROOT).as_posix(), line_no, value))
say("  count=%d" % len(missing))
for path, line_no, value in missing[:60]:
    say("    %s:%d  %s" % (path, line_no, value[:90]))

# ------------------------------------------------------------------ scenes ---

say()
say("RUSSIAN TEXT BAKED INTO SCENES THAT IS NOT A KEY")
scene_missing = []
for path in sorted(PROJECT.rglob("*.tscn")):
    text = path.read_text(encoding="utf-8")
    for line_no, line in enumerate(text.splitlines(), 1):
        if not CYRILLIC.search(line):
            continue
        for match in STRING.finditer(line):
            value = unescape(match.group(1))
            if CYRILLIC.search(value) and value not in keys:
                scene_missing.append((path.relative_to(ROOT).as_posix(), line_no, value))
say("  count=%d" % len(scene_missing))
for path, line_no, value in scene_missing[:40]:
    say("    %s:%d  %s" % (path, line_no, value[:90]))

# ------------------------------------------------------------------ config ---

say()
say("PROJECT SETTINGS")
godot = (PROJECT / "project.godot").read_text(encoding="utf-8")
for line in godot.splitlines():
    if any(word in line for word in ("locale", "translation", "config/name", "boot_splash")):
        say("  " + line)

# ------------------------------------------------------------------- html ----

web = PROJECT / "web"
if web.exists():
    say()
    say("WEB SHELL")
    for path in sorted(web.rglob("*")):
        if path.is_file():
            say("  %s (%d bytes)" % (path.relative_to(ROOT).as_posix(), path.stat().st_size))

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(report), encoding="utf-8")
print("LOCALE_AUDIT_WRITTEN", OUT)
print("summary: blank_en=%d cyr_en=%d code_literals=%d scene_literals=%d"
      % (len(blank_en), len(cyr_en), len(missing), len(scene_missing)))
