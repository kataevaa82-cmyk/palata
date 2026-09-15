# -*- coding: utf-8 -*-
"""Wrap every user-visible Russian literal in the GDScript in tr().

Two rules make this safe to run mechanically:

1. `const` blocks are skipped. GDScript will not evaluate a function call in a
   constant, so ASSIGNMENTS / ITEM_NAMES / LEVELS / LEVEL_OBJECT_TASKS / HINTS
   keep their Russian text and are translated where they are *used* instead -
   those use sites are listed in USE_SITES below and patched by hand.
2. INTERNAL strings are never touched: a node name and the audio sting ids are
   Russian but are identifiers, not text for the player.

Idempotent: a literal already inside tr(...) is left alone, so re-running after
adding new text only wraps the new lines.
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT = os.path.join(ROOT, "project")
CYRILLIC = re.compile(r"[А-Яа-яЁё]")
LITERAL = re.compile(r'"((?:[^"\\]|\\.)*)"')

INTERNAL = {
    "ПредметВИнвентаре",
    "главная_медсестра",
    "пожарная_сирена",
}

FILES = [
    "scripts/systems/care_manager.gd",
    "scripts/systems/level_manager.gd",
    "scripts/systems/game_director.gd",
    "scripts/systems/main.gd",
    "scripts/anomalies/anomaly_manager.gd",
    "scripts/anomalies/orderly_enemy.gd",
    "scripts/anomalies/violent_patient.gd",
    "scripts/events/event_manager.gd",
    "scripts/interaction/care_interactable.gd",
    "scripts/interaction/document.gd",
    "scripts/interaction/door.gd",
    "scripts/interaction/elevator.gd",
    "scripts/interaction/exit_door.gd",
    "scripts/interaction/interactive_prop.gd",
    "scripts/interaction/light_switch.gd",
    "scripts/interaction/patient_interaction.gd",
    "scripts/interaction/phone.gd",
    "scripts/ui/hud.gd",
    "scripts/ui/mobile_controls.gd",
]

# The type annotation may itself carry brackets - `const LEVELS: Array[Dictionary] = [`
# is the one that matters, and a stricter pattern misses it, wraps tr() inside a
# constant and fails the parse with "isn't a constant expression".
CONST_START = re.compile(r"^\s*const\s+\w+\s*(:=|:[^=]*=)\s*[\[{]")


def wrap_line(line):
    """Wrap the Cyrillic literals on one line, leaving already-wrapped ones."""
    out = []
    index = 0
    changed = False
    for match in LITERAL.finditer(line):
        text = match.group(1)
        out.append(line[index:match.start()])
        index = match.end()
        already_wrapped = line[max(0, match.start() - 3):match.start()] == "tr("
        if (CYRILLIC.search(text) and text not in INTERNAL and not already_wrapped):
            out.append('tr("%s")' % text)
            changed = True
        else:
            out.append(match.group(0))
    out.append(line[index:])
    return "".join(out), changed


total = 0
for relative in FILES:
    path = os.path.join(PROJECT, relative)
    lines = io.open(path, encoding="utf-8").read().split("\n")
    depth = 0
    in_const = False
    result = []
    touched = 0
    for line in lines:
        stripped = line.strip()
        if not in_const and CONST_START.match(line):
            in_const = True
            depth = 0
        if in_const:
            depth += line.count("{") + line.count("[") - line.count("}") - line.count("]")
            result.append(line)
            if depth <= 0:
                in_const = False
            continue
        if stripped.startswith("#"):
            result.append(line)
            continue
        new_line, changed = wrap_line(line)
        touched += 1 if changed else 0
        result.append(new_line)
    io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(result))
    total += touched
    if touched:
        print("%-46s wrapped_lines=%d" % (relative, touched))
print("WRAP_TR total_lines=%d" % total)
