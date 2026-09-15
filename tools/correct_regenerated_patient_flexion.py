"""Correct the first preview rig's limb flexion, then reground each clip.

The full generator now includes the same corrected signs. This migration
allows the already-open sculpt to be kept, without regenerating geometry.
"""
import bpy
from mathutils import Vector

scene=bpy.context.scene
rig=bpy.data.objects['violent_patient_rig']
body=bpy.data.objects['violent_patient_human_mesh']

def correct():
    if rig.get('anatomical_flexion_v2'):
        print('FLEXION_ALREADY_CORRECT')
        return
    tracks=list(rig.animation_data.nla_tracks)
    for track in tracks:
        track.mute=True
    for name in ('Violent_Idle','Violent_Run','Violent_Attack'):
        act=bpy.data.actions[name]
        wanted=['forearm.']
        if name!='Violent_Idle':
            wanted.append('upper_arm.')
        if name=='Violent_Run':
            wanted.extend(['thigh.','shin.','foot.'])
        for layer in act.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        if fc.data_path.endswith('rotation_quaternion') and fc.array_index>0 and any('"'+prefix in fc.data_path for prefix in wanted):
                            for point in fc.keyframe_points:
                                point.co.y*=-1
                                point.handle_left.y*=-1
                                point.handle_right.y*=-1
        rig.animation_data.action=act
        rig.animation_data.action_slot=act.slots[0]
        for frame in range(int(act.frame_range[0]),int(act.frame_range[1])+1):
            scene.frame_set(frame)
            rig.pose.bones['pelvis'].location=(0,0,0)
            bpy.context.view_layer.update()
            dg=bpy.context.evaluated_depsgraph_get()
            ev=body.evaluated_get(dg)
            data=ev.to_mesh()
            minz=min((ev.matrix_world@v.co).z for v in data.vertices)
            ev.to_mesh_clear()
            rig.pose.bones['pelvis'].location=rig.data.bones['pelvis'].matrix_local.to_quaternion().inverted()@Vector((0,0,.012-minz))
            rig.pose.bones['pelvis'].keyframe_insert(data_path='location',frame=frame,group='pelvis')
    rig.animation_data.action=None
    for track in tracks:
        track.mute=False
    rig['anatomical_flexion_v2']=True
    scene.frame_set(1)
    print('FLEXION_CORRECTED_AND_GROUNDED')

correct()
