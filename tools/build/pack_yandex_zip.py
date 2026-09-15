# -*- coding: utf-8 -*-
"""Pack build/yandex/ into build/Palata_0_Yandex.zip the way Yandex expects.

Rules the console enforces, all checked here rather than after an upload is
rejected:
  * index.html sits in the ROOT of the archive, not in a folder;
  * sdk.js must NOT be inside - the platform serves it from /sdk.js;
  * file names are ASCII, no spaces;
  * the uncompressed payload stays under the 100 MB limit.

Prints the numbers that go into YANDEX_RELEASE_CHECKLIST.md.
"""
import hashlib
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCE = os.path.join(ROOT, "build", "yandex")
TARGET = os.path.join(ROOT, "build", "Palata_0_Yandex.zip")
LIMIT_BYTES = 100 * 1024 * 1024

files = sorted(os.listdir(SOURCE))
problems = []
if "index.html" not in files:
    problems.append("index.html missing from build/yandex")
if "sdk.js" in files:
    problems.append("sdk.js must not be packed - Yandex serves it from /sdk.js")
for name in files:
    if not all(ord(char) < 128 for char in name) or " " in name:
        problems.append("bad file name: %r" % name)

# The custom shell is folded into index.html at export time and is not shipped
# as a resource, so validate_yandex_integration.gd cannot see it from inside a
# pack. This is where the produced page gets checked instead: if an export
# silently fell back to Godot's default shell, every SDK hook below is gone.
if "index.html" in files:
    page = open(os.path.join(SOURCE, "index.html"), encoding="utf-8").read()
    for required in ['src="/sdk.js"', "YaGames.init()", "LoadingAPI?.ready()",
                     "GameplayAPI?.start()", "showFullscreenAdv", "player.getData",
                     "player.setData", "rotate-notice", "SHELL_TEXT", "data-i18n"]:
        if required not in page:
            problems.append("index.html is missing %s" % required)

total = sum(os.path.getsize(os.path.join(SOURCE, name)) for name in files)
if total > LIMIT_BYTES:
    problems.append("uncompressed %.2f MiB is over the 100 MB limit" % (total / 1048576))
if problems:
    raise SystemExit("REFUSED:\n  " + "\n  ".join(problems))

with zipfile.ZipFile(TARGET, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for name in files:
        archive.write(os.path.join(SOURCE, name), arcname=name)

digest = hashlib.sha256(open(TARGET, "rb").read()).hexdigest().upper()
print("YANDEX_ZIP files=%d uncompressed=%.2f MiB zipped=%.2f MiB" % (
    len(files), total / 1048576, os.path.getsize(TARGET) / 1048576))
print("YANDEX_ZIP sha256=%s" % digest)
print("YANDEX_ZIP path=%s" % TARGET)
