import bpy, collections, re
pat = re.compile(r"^(hospital_door|doorframe|ward_1_bed|sink|toilet|shower|radiator|wheelchair|medical_cart|window|office|nurse|notice|elevator|linen)", re.I)
seen = collections.defaultdict(list)
for o in bpy.data.objects:
    if o.type != "MESH": continue
    m = pat.match(o.name)
    if m:
        seen[m.group(1).lower()].append(o.name)
print("NAMES_BEGIN")
for k in sorted(seen):
    print(k, len(seen[k]), sorted(seen[k])[:6])
print("NAMES_END")
