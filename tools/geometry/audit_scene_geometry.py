# -*- coding: utf-8 -*-
"""Rank the whole ward's geometry by how crude it is, not just the level props.

Two things make a mesh read as cheap in this game's lighting:

  * a raw box - 8 vertices, 6 faces, hard 90-degree edges that catch a hard
    highlight and give away the primitive;
  * a coarse round - a cylinder or sphere with so few segments that its
    silhouette is visibly faceted.

Both are detectable without opening the file by hand, so this prints the worst
offenders grouped by family (the prefix before the first underscore run), with
how many meshes of that family are affected and how big they are - a raw box the
size of a wardrobe matters, a raw box the size of a screw head does not.

Usage: blender --background hospital_models_work.blend --python this.py
"""
import bpy
import collections

RAW_BOX_VERTS = 8
COARSE_RING = 12          # a cylinder with 12 or fewer sides shows its facets
BIG_ENOUGH = 0.18         # metres; below this the silhouette is not readable

families = collections.defaultdict(lambda: {
    "meshes": 0, "tris": 0, "raw_boxes": 0, "coarse_rounds": 0,
    "biggest_raw": 0.0, "examples": [],
})


def family_of(name):
    lowered = name.lower()
    for separator in ("_v2", "_v3", "_v4"):
        lowered = lowered.replace(separator, "")
    parts = lowered.split("_")
    if len(parts) >= 2:
        return "_".join(parts[:2])
    return parts[0]


for obj in bpy.data.objects:
    if obj.type != "MESH" or not obj.data.polygons:
        continue
    mesh = obj.data
    size = max(obj.dimensions)
    entry = families[family_of(obj.name)]
    entry["meshes"] += 1
    entry["tris"] += sum(max(len(p.vertices) - 2, 1) for p in mesh.polygons)

    if len(mesh.vertices) == RAW_BOX_VERTS and len(mesh.polygons) == 6 and size >= BIG_ENOUGH:
        entry["raw_boxes"] += 1
        entry["biggest_raw"] = max(entry["biggest_raw"], size)
        if len(entry["examples"]) < 3:
            entry["examples"].append("%s box %.2fm" % (obj.name, size))
    else:
        # A round primitive's cap is one n-gon whose vertex count is the ring
        # resolution; on a triangulated mesh the ring shows up as the largest
        # face instead, so take the max either way.
        ring = max((len(p.vertices) for p in mesh.polygons), default=0)
        if 4 < ring <= COARSE_RING and size >= BIG_ENOUGH:
            entry["coarse_rounds"] += 1
            if len(entry["examples"]) < 3:
                entry["examples"].append("%s ring=%d %.2fm" % (obj.name, ring, size))

rows = [(name, data) for name, data in families.items()
        if data["raw_boxes"] or data["coarse_rounds"]]
rows.sort(key=lambda row: -(row[1]["raw_boxes"] * row[1]["biggest_raw"] + row[1]["coarse_rounds"] * 0.25))

print("SCENE_GEOMETRY_AUDIT")
print("%-28s %6s %7s %6s %7s %8s  %s" % (
    "family", "meshes", "tris", "boxes", "rounds", "biggest", "examples"))
for name, data in rows[:40]:
    print("%-28s %6d %7d %6d %7d %8.2f  %s" % (
        name, data["meshes"], data["tris"], data["raw_boxes"], data["coarse_rounds"],
        data["biggest_raw"], "; ".join(data["examples"])))

total_boxes = sum(d["raw_boxes"] for d in families.values())
total_rounds = sum(d["coarse_rounds"] for d in families.values())
total_tris = sum(d["tris"] for d in families.values())
total_meshes = sum(d["meshes"] for d in families.values())
print("SCENE_TOTAL meshes=%d tris=%d raw_boxes=%d coarse_rounds=%d" % (
    total_meshes, total_tris, total_boxes, total_rounds))
