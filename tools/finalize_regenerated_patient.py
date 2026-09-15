"""Clean and export the reviewed v2 model in the connected Blender scene."""
import bpy
import bmesh
import json

OUT='C:/palata/build/patient_regeneration'
scene=bpy.context.scene
body=bpy.data.objects['violent_patient_human_mesh']
rig=bpy.data.objects['violent_patient_rig']
root=bpy.data.objects['violent_patient_v1']
if bpy.context.object and bpy.context.object.mode!='OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
bpy.context.view_layer.objects.active=body
repaired=body.data.validate(verbose=True,clean_customdata=False)
bm=bmesh.new()
bm.from_mesh(body.data)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(body.data)
bm.free()
count=sum(len(p.vertices)-2 for p in body.data.polygons)
if count>39000:
    dec=body.modifiers.new('Final game mesh budget','DECIMATE')
    dec.ratio=36000/count
    dec.use_collapse_triangulate=True
    bpy.ops.object.modifier_move_up(modifier=dec.name)
    bpy.ops.object.modifier_apply(modifier=dec.name)
body.data.validate(verbose=True,clean_customdata=False)
for v in body.data.vertices:
    groups=sorted([(g.group,g.weight) for g in v.groups if g.weight>0],key=lambda item:item[1],reverse=True)
    kept=groups[:4]
    for i,w in groups[4:]:
        body.vertex_groups[i].remove([v.index])
    total=sum(w for i,w in kept)
    if not total:
        raise RuntimeError('Unweighted vertex '+str(v.index))
    for i,w in kept:
        body.vertex_groups[i].add([v.index],w/total,'REPLACE')
for poly in body.data.polygons:
    poly.use_smooth=True
scene.frame_set(1)
rig.select_set(True)
root.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT+'/violent_patient_v2.glb',export_format='GLB',use_selection=True,
    export_animations=True,export_animation_mode='NLA_TRACKS',export_skins=True,
    export_yup=True,export_cameras=False,export_lights=False,export_apply=False,
    export_force_sampling=True,export_extras=True,export_anim_slide_to_zero=True)
report={'vertices':len(body.data.vertices),'triangles':sum(len(p.vertices)-2 for p in body.data.polygons),
        'bones':len(rig.data.bones),'unweighted':sum(not v.groups for v in body.data.vertices),
        'max_influences':max(len(v.groups) for v in body.data.vertices),
        'mesh_valid':not body.data.validate(verbose=False,clean_customdata=False),
        'initial_mesh_repaired':repaired,
        'actions':[(track.name,float(track.strips[0].action_frame_end-track.strips[0].action_frame_start)/30) for track in rig.animation_data.nla_tracks]}
with open(OUT+'/final_report.json','w',encoding='utf-8') as fp:
    json.dump(report,fp,indent=2)
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.wm.save_as_mainfile(filepath='C:/palata/violent_patient_work.blend')
print('PATIENT_FINAL',json.dumps(report))
