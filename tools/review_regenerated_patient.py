"""Render review angles and audit the regenerated patient's animated mesh."""
import bpy
import json
from mathutils import Vector

OUT='C:/palata/build/patient_regeneration'
scene=bpy.context.scene
camera=scene.camera
rig=bpy.data.objects['violent_patient_rig']
body=bpy.data.objects['violent_patient_human_mesh']
engines=scene.render.bl_rna.properties['engine'].enum_items.keys()
scene.render.engine=next((engine for engine in engines if 'EEVEE' in engine),'CYCLES')
scene.render.resolution_x=800
scene.render.resolution_y=1000
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'

def view(name,location,target,scale,frame):
    scene.frame_set(frame)
    camera.location=location
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=scale
    scene.render.filepath=OUT+'/'+name+'.png'
    bpy.ops.render.render(write_still=True)
    print('RENDERED',name,flush=True)

kind=globals().get('PATIENT_REVIEW','full')
if kind=='full':
    view('patient_v2_full',(2.6,-5,2.3),(0,-.05,.94),2.12,1)
elif kind=='face':
    view('patient_v2_face',(.42,-3,1.74),(0,-.10,1.665),.38,1)
elif kind=='back':
    view('patient_v2_back',(-2.8,5,2.1),(0,0,.96),2.13,1)
elif kind=='run':
    view('patient_v2_run',(3,-5,2.4),(0,-.05,.98),2.30,67)
elif kind=='audit':
    results=[]
    for name,start,end in [('idle',1,49),('run',61,85),('attack',121,145)]:
        boxes=[]
        for frame in range(start,end+1):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            dg=bpy.context.evaluated_depsgraph_get()
            ev=body.evaluated_get(dg)
            data=ev.to_mesh()
            points=[ev.matrix_world@v.co for v in data.vertices]
            lo=[min(p[i] for p in points) for i in range(3)]
            hi=[max(p[i] for p in points) for i in range(3)]
            ev.to_mesh_clear()
            boxes.append((lo,hi))
        results.append({'clip':name,'minimum_z':min(lo[2] for lo,hi in boxes),
                        'maximum_height':max(hi[2] for lo,hi in boxes),
                        'max_width':max(hi[0]-lo[0] for lo,hi in boxes),
                        'max_depth':max(hi[1]-lo[1] for lo,hi in boxes)})
    scene.frame_set(1)
    print('ANIMATION_AUDIT',json.dumps(results))
    with open(OUT+'/animation_audit.json','w',encoding='utf-8') as fp:
        json.dump(results,fp,indent=2)
