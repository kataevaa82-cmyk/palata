import json

import bpy


OBJECT_NAME = "ward_4_bed_1_patient_v3_patient_head"


obj = bpy.data.objects[OBJECT_NAME]
mesh = obj.data
vertex_polygons = [[] for _ in mesh.vertices]
for polygon in mesh.polygons:
    for vertex_index in polygon.vertices:
        vertex_polygons[vertex_index].append(polygon.index)

seen = set()
components = []
for seed in range(len(mesh.polygons)):
    if seed in seen:
        continue
    stack = [seed]
    seen.add(seed)
    polygon_indices = []
    vertex_indices = set()
    while stack:
        polygon_index = stack.pop()
        polygon_indices.append(polygon_index)
        polygon = mesh.polygons[polygon_index]
        for vertex_index in polygon.vertices:
            vertex_indices.add(vertex_index)
            for neighbor in vertex_polygons[vertex_index]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)

    coordinates = [mesh.vertices[index].co for index in vertex_indices]
    minimum = [min(coordinate[axis] for coordinate in coordinates) for axis in range(3)]
    maximum = [max(coordinate[axis] for coordinate in coordinates) for axis in range(3)]
    material_indices = sorted({mesh.polygons[index].material_index for index in polygon_indices})
    components.append({
        "polygons": len(polygon_indices),
        "vertices": len(vertex_indices),
        "minimum": [round(value, 4) for value in minimum],
        "maximum": [round(value, 4) for value in maximum],
        "materials": [mesh.materials[index].name for index in material_indices],
        "polygon_indices": polygon_indices,
    })

components.sort(key=lambda component: (-component["maximum"][2], component["minimum"][1]))
print("PATIENT_COMPONENTS_JSON", json.dumps(components, separators=(",", ":")))
