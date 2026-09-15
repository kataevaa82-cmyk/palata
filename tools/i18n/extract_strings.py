# -*- coding: utf-8 -*-
"""Pull every Cyrillic string literal out of the GDScript and the scenes.

Used to size and then drive the English localisation: the Russian source text
is the translation key, so this list is literally the msgid column of
project/locale/palata.csv.
"""
import os
import re
import sys
import json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT = os.path.join(ROOT, "project")
CYRILLIC = re.compile(r"[А-Яа-яЁё]")
# GDScript string literal: "..." with escaped quotes, single line.
LITERAL = re.compile(r'"((?:[^"\\]|\\.)*)"')
# ...and the triple-quoted blocks, which a line scanner misses entirely. The
# assignment board was one, and it shipped untranslated until the runtime sweep
# caught it on screen.
BLOCK = re.compile(r'"""(.*?)"""', re.DOTALL)

hits = []
for base, dirs, files in os.walk(PROJECT):
    dirs[:] = [d for d in dirs if d not in {".godot", "assets"}]
    for name in sorted(files):
        if not name.endswith((".gd", ".tscn")):
            continue
        path = os.path.join(base, name)
        rel = os.path.relpath(path, PROJECT).replace("\\", "/")
        if rel.startswith("scripts/tests/"):
            continue
        source = open(path, encoding="utf-8").read()
        for block in BLOCK.finditer(source):
            if CYRILLIC.search(block.group(1)):
                hits.append({"file": rel,
                             "line": source[:block.start()].count("\n") + 1,
                             "text": block.group(1)})
        # Blank the blocks out so their inner lines are not scanned again as
        # single-line literals.
        source = BLOCK.sub(lambda match: '"""%s"""' % ("\n" * match.group(1).count("\n")), source)

        for number, line in enumerate(source.split("\n"), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for literal in LITERAL.findall(line):
                if CYRILLIC.search(literal):
                    # The msgid has to be the RUNTIME string: in the source a
                    # brief is written "...\n..." (two characters), but tr()
                    # is called with a real line feed, so unescape here or every
                    # multi-line string silently misses its translation.
                    text = (literal.replace(r"\n", "\n").replace(r"\t", "\t")
                                   .replace(r'\"', '"').replace(r"\\", "\\"))
                    hits.append({"file": rel, "line": number, "text": text})

unique = []
seen = set()
for hit in hits:
    if hit["text"] in seen:
        continue
    seen.add(hit["text"])
    unique.append(hit)

if "--json" in sys.argv:
    print(json.dumps(unique, ensure_ascii=False, indent=1))
else:
    per_file = {}
    for hit in hits:
        per_file[hit["file"]] = per_file.get(hit["file"], 0) + 1
    for path in sorted(per_file, key=lambda k: -per_file[k]):
        print("%5d  %s" % (per_file[path], path))
    print("occurrences=%d unique=%d" % (len(hits), len(unique)))
    print("chars=%d" % sum(len(hit["text"]) for hit in unique))
