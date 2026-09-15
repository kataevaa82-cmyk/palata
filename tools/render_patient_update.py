"""Isolated review renders; does not save lighting/camera changes to source."""
import bpy, sys, os
from mathutils import Vector

args=sys.argv[sys.argv.index('--')+1:]
kind, output=args[:2]
scene=bpy.context.scene
if kind=='ward':
    root=bpy.data.objects['ward_4_bed_1_patient_v3']
    wanted=set(root.children_recursive)
    target=root.matrix_world@Vector((0,.71,1.00))
    loc=root.matrix_world@Vector((.36,.35,1.65))
    scale=.44
else:
    wanted=set(bpy.data.collections['ASSET_violent_patient_v1'].all_objects)
    target=Vector((0,0,.93)); loc=Vector((2.7,-5,2.3)); scale=2.05
    scene.frame_set(67 if kind=='run' else (133 if kind=='attack' else 1))
    if kind=='face':
        target=Vector((0,-.055,1.67));loc=Vector((.35,-3,1.74));scale=.36
    elif kind=='hands':
        target=Vector((.33,-.02,.90));loc=Vector((1.5,-2.5,1.05));scale=.37
for obj in scene.objects:
    obj.hide_render=obj not in wanted
for obj in wanted:
    obj.hide_render=False
cam_data=bpy.data.cameras.new('ReviewCamera')
cam=bpy.data.objects.new('ReviewCamera',cam_data); scene.collection.objects.link(cam)
cam.location=loc; cam.rotation_euler=(target-loc).to_track_quat('-Z','Y').to_euler()
cam_data.type='ORTHO'; cam_data.ortho_scale=scale; scene.camera=cam
for i,(offset,power,size) in enumerate([((2,-3,4),450,3),((-3,-1,2),250,3),((1,3,3),500,2)]):
    light=bpy.data.lights.new('ReviewLight'+str(i),'AREA'); light.energy=power; light.shape='DISK'; light.size=size
    ob=bpy.data.objects.new(light.name,light); scene.collection.objects.link(ob); ob.location=target+Vector(offset)
    ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
scene.world=bpy.data.worlds.new('ReviewWorld'); scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.065,.075,.085,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
scene.render.engine='CYCLES'; scene.cycles.samples=24
scene.render.resolution_x=900; scene.render.resolution_y=900 if kind in ('ward','face','hands') else 1100
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.filepath=output
os.makedirs(os.path.dirname(output),exist_ok=True)
bpy.ops.render.render(write_still=True)
