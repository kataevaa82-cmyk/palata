"""Refine the existing game models, retaining roots, skin weights and animation.

Run with -- ward or -- violent in the corresponding working .blend.
Backups are written once before modifying the source files.
"""
import bpy, bmesh, math, os, sys, shutil, runpy
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

BASE='C:/palata'
MODE=sys.argv[sys.argv.index('--')+1]
OUT=BASE+'/build/patient_update'
os.makedirs(OUT,exist_ok=True)
for path in ([BASE+'/hospital_models_work.blend',BASE+'/palata_zero.glb',BASE+'/project/assets/models/palata_zero.glb'] if MODE=='ward' else [BASE+'/violent_patient_work.blend',BASE+'/violent_patient_v1.glb',BASE+'/project/assets/models/violent_patient_v1.glb']):
    backup=OUT+'/'+('game_' if '/project/' in path else '')+os.path.basename(path)+'.before'
    if os.path.exists(path) and not os.path.exists(backup): shutil.copy2(path,backup)

def material(name,color,rough=.8):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=rough
    return m

def mesh(name,verts,faces,mat,parent,collection):
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update()
    bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(me); bm.free()
    ob=bpy.data.objects.new(name,me); collection.objects.link(ob); ob.parent=parent
    me.materials.append(mat)
    for p in me.polygons: p.use_smooth=True
    return ob

def ward():
    colours=[(.045,.032,.022),(.12,.105,.085),(.07,.038,.025),(.035,.026,.022),(.16,.15,.135),(.055,.05,.042),(.095,.049,.029)]
    roots=sorted([o for o in bpy.data.objects if o.name.startswith('ward_') and o.name.endswith('_patient_v3')],key=lambda o:o.name)
    assert len(roots)==7
    for index,root in enumerate(roots):
        if root.get('hair_groom_v1'): continue
        body=bpy.data.objects[root.name+'_patient_head']
        # The old cap is part of the same mesh as the skin. Turn it into a
        # smooth scalp beneath the new groom so there are no open skull holes.
        hair_indices={i for i,m in enumerate(body.data.materials) if 'hair' in m.name}
        skin=next(i for i,m in enumerate(body.data.materials) if 'skin' in m.name)
        bm=bmesh.new(); bm.from_mesh(body.data)
        hv={v for f in bm.faces if f.material_index in hair_indices for v in f.verts}
        scalp_indices={v.index for v in hv}
        for _ in range(4): bmesh.ops.smooth_vert(bm,verts=list(hv),factor=.35,use_axis_x=True,use_axis_y=True,use_axis_z=True)
        for f in bm.faces:
            if f.material_index in hair_indices: f.material_index=skin
        bm.to_mesh(body.data); bm.free(); body.data.update()
        # Crown is local +Y; the lying face points +Z. The front hairline
        # stays above the brows, while the sides continue behind the ears.
        centre=Vector((0,.704,.968)); radii=Vector((.107,.109,.123))
        # Keep the former polygonal scalp strictly inside the smooth cap.
        # Radial ray projection alone misses overlapping source triangles.
        for i in scalp_indices:
            v=body.data.vertices[i]; relative=v.co-centre
            radial=math.sqrt(sum((relative[a]/radii[a])**2 for a in range(3)))
            if radial>.94: v.co=centre+relative*(.94/radial)
        def limit(phi):
            front=math.cos(phi)
            return 1.22+.72*(1-front)/2+.34*(1-abs(front)) + .025*math.sin(phi*3+index)
        def surface(t,phi,lift=0):
            theta=t*limit(phi)
            direction=Vector((math.sin(theta)*math.sin(phi),math.cos(theta),math.sin(theta)*math.cos(phi)))
            sweep=.012*math.sin(theta)*math.sin(phi+index*.2)
            relative=Vector((radii.x*direction.x+sweep,radii.y*direction.y,radii.z*direction.z))
            return centre+relative+relative.normalized()*lift
        color=colours[index]
        mats=[material('MAT_patient_hair_groom_%d_%d'%(index,k),tuple(c*scale for c in color),.77) for k,scale in enumerate([1,.8,1.25])]
        verts=[]; faces=[]; rows=16; cols=64
        for j in range(rows+1):
            for i in range(cols): verts.append(surface(max(.001,j/rows),i*math.tau/cols,.002))
        for j in range(rows):
            for i in range(cols):
                a=j*cols+i; b=j*cols+(i+1)%cols
                faces.append((a,b,b+cols,a+cols))
        cap=mesh(root.name+'_patient_hair_groom',verts,faces,mats[0],root,root.users_collection[0])
        for m in mats[1:]: cap.data.materials.append(m)
        # Tapered low-poly locks follow the scalp; no alpha cards or particle
        # system are needed in the exported web model.
        verts=[]; faces=[]
        for strand in range(90):
            phi0=strand*math.tau/90
            start=.10+.06*math.sin(strand*2.3)
            end=1.005+.016*math.sin(strand*3.7)
            base=len(verts)
            for step in range(13):
                t=start+(end-start)*step/12
                phi=phi0+.24*math.sin(t*math.pi)*math.sin(phi0+.65)
                mid=surface(t,phi,.0023)
                normal=(mid-centre).normalized()
                tangent=(surface(min(1.03,t+.002),phi)-surface(max(0,t-.002),phi)).normalized()
                side=tangent.cross(normal).normalized()
                width=.0008*(math.sin(math.pi*step/12)**.4)+.00008
                for k in range(4):
                    angle=math.tau*k/4
                    verts.append(mid+side*(width*math.cos(angle))+normal*(width*.6*math.sin(angle)))
            for step in range(12):
                for k in range(4):
                    a=base+step*4+k; b=base+step*4+(k+1)%4
                    faces.append((a,b,b+4,a+4))
        locks=mesh(root.name+'_patient_hair_strands',verts,faces,mats[0],root,root.users_collection[0])
        for m in mats[1:]: locks.data.materials.append(m)
        for p in locks.data.polygons: p.material_index=(p.index//48)%3
        # Previously authored lids were left floating above the crown when
        # the downloaded face was substituted. Fit them to the actual face.
        bvh=BVHTree.FromPolygons([v.co for v in body.data.vertices],[list(p.vertices) for p in body.data.polygons])
        for child in root.children:
            if '_closed_eye_' not in child.name and '_closed_lash_' not in child.name: continue
            centre_eye=sum((v.co for v in child.data.vertices),Vector())/len(child.data.vertices)
            target_y=.695
            hit=bvh.ray_cast(Vector((centre_eye.x,target_y,1.3)),Vector((0,0,-1)),.5)[0]
            if hit:
                delta=Vector((0,target_y-centre_eye.y,hit.z+.0015-centre_eye.z))
                for v in child.data.vertices: v.co+=delta
        root['hair_groom_v1']=True
        print('GROOMED',root.name,'hair_triangles',sum(len(p.vertices)-2 for o in (cap,locks) for p in o.data.polygons),flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=BASE+'/hospital_models_work.blend')
    runpy.run_path(BASE+'/tools/geometry/export_hospital_and_copy.py')

def violent():
    body=bpy.data.objects['violent_patient_human_mesh']; rig=bpy.data.objects['violent_patient_rig']
    if body.get('pajamas_v1'): raise RuntimeError('Clothes already updated')
    col=body.users_collection[0]
    # Use the existing fitted garment and its tested deformation weights.
    # A packed cotton texture gives consistent stripes in Blender and Godot.
    m=material('VP3_patient_blue_striped_cotton',(.26,.35,.43),.91)
    size=512; y,x=np.mgrid[0:size,0:size]
    base=np.array([.24,.34,.43]); stripe=np.array([.48,.56,.62])
    bands=((x%64)<5).astype(float)*.75+((x%64)>60).astype(float)*.22
    weave=(np.sin(x*math.pi)*.004+np.cos(y*math.pi)*.008+np.sin(x*1.713+y*2.117)*.009)
    pixels=np.empty((size,size,4),dtype=np.float32)
    pixels[:,:,:3]=np.clip(base[None,None,:]*(1-bands[:,:,None])+stripe[None,None,:]*bands[:,:,None]+weave[:,:,None],0,1)
    pixels[:,:,3]=1
    image=bpy.data.images.new('Patient_pajama_cotton',width=size,height=size,alpha=False)
    image.pixels.foreach_set(pixels.ravel()); image.filepath_raw=OUT+'/patient_pajama_cotton.png'; image.file_format='PNG'; image.save(); image.pack()
    tex=m.node_tree.nodes.new('ShaderNodeTexImage'); tex.image=image
    m.node_tree.links.new(tex.outputs['Color'],m.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    trim=material('VP3_patient_navy_piping',(.06,.10,.14),.85)
    buttonmat=material('VP3_patient_bone_buttons',(.58,.56,.49),.48)
    sole=material('VP3_patient_slipper_sole',(.028,.035,.038),.91)
    slippermat=material('VP3_patient_slipper_canvas',(.065,.105,.13),.88)
    for i,old in enumerate(list(body.data.materials)):
        if 'scrubs' in old.name or 'trousers' in old.name: body.data.materials[i]=m
        elif 'worn_seams' in old.name: body.data.materials[i]=trim
    uv=body.data.uv_layers.get('PajamaUV') or body.data.uv_layers.new(name='PajamaUV')
    body.data.uv_layers.active=uv
    uv.active_render=True
    for loop in body.data.loops:
        co=body.data.vertices[loop.vertex_index].co; uv.data[loop.index].uv=(co.x*4,co.z*2)
    # Cloth colours come from the image, not the former blotchy vertex paint.
    for attr in body.data.color_attributes:
        for p in body.data.polygons:
            if body.data.materials[p.material_index] in (m,trim):
                for li in p.loop_indices:
                    attr.data[li if attr.domain=='CORNER' else body.data.loops[li].vertex_index].color=(1,1,1,1)
    kd=KDTree(len(body.data.vertices))
    for v in body.data.vertices: kd.insert(v.co,v.index)
    kd.balance()
    added=[]
    def bind(ob,bone=None):
        if bone:
            ob.vertex_groups.new(name=bone).add(list(range(len(ob.data.vertices))),1,'REPLACE')
        else:
            for group in body.vertex_groups: ob.vertex_groups.new(name=group.name)
            for v in ob.data.vertices:
                near=kd.find_n(v.co,4); totals={}; denom=sum(1/max(d,.002)**2 for co,i,d in near)
                for co,i,d in near:
                    factor=(1/max(d,.002)**2)/denom
                    for g in body.data.vertices[i].groups: totals[g.group]=totals.get(g.group,0)+g.weight*factor
                top=sorted(totals.items(),key=lambda t:-t[1])[:4]; total=sum(w for i,w in top)
                for i,w in top: ob.vertex_groups[i].add([v.index],w/total,'REPLACE')
        added.append(ob); return ob
    bvh=BVHTree.FromPolygons([v.co for v in body.data.vertices],[list(p.vertices) for p in body.data.polygons])
    def front(x,z,extra=.005):
        hit=bvh.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2)[0]
        return Vector((x,hit.y-extra if hit else -.12,z))
    # Overlapping front placket makes the V-neck scrub top a buttoned pajama.
    verts=[]; faces=[]
    for j in range(25):
        z=1.008+j*(1.428-1.008)/24
        verts.extend([front(-.014,z),front(.014,z)])
        if j: faces.append((2*j-2,2*j-1,2*j+1,2*j))
    bind(mesh('pajama_front_placket',verts,faces,trim,rig,col))
    for j in range(6):
        pos=front(0,1.055+j*.065,.01)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=pos)
        ob=bpy.context.object; ob.name='pajama_button_%d'%j; ob.scale=(.005,.0025,.005)
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        ob.data.materials.append(buttonmat); ob.parent=rig; bind(ob)
    for sign in (-1,1):
        coords=[(sign*.052,1.49),(sign*.099,1.459),(sign*.066,1.382),(sign*.02,1.427)]
        points=[front(x,z,.009) for x,z in coords]
        collar=mesh('pajama_folded_collar',points,[(0,1,2,3)],m,rig,col)
        bind(collar)
    # Join the trouser legs into a continuous pelvis, removing internal
    # surfaces. A loose overlapping flap is not a sewn trouser crotch.
    pants_index=4
    selected=[p for p in body.data.polygons if p.material_index==pants_index]
    indices=sorted({v for p in selected for v in p.vertices})
    mapping={v:i for i,v in enumerate(indices)}
    pants=mesh('pajama_trousers', [body.data.vertices[i].co.copy() for i in indices],
               [tuple(mapping[v] for v in p.vertices) for p in selected],m,rig,col)
    bm=bmesh.new(); bm.from_mesh(body.data)
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index==pants_index],context='FACES')
    bm.to_mesh(body.data); bm.free(); body.data.update()
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,location=(0,.01,.996))
    pelvis=bpy.context.object; pelvis.scale=(.176,.108,.123)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    bpy.ops.object.select_all(action='DESELECT'); pelvis.select_set(True); pants.select_set(True)
    bpy.context.view_layer.objects.active=pants; bpy.ops.object.join()
    remesh=pants.modifiers.new('Continuous trouser seams','REMESH'); remesh.mode='VOXEL'; remesh.voxel_size=.0045; remesh.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=remesh.name)
    smooth=pants.modifiers.new('Relax sewn fabric','SMOOTH'); smooth.factor=.8; smooth.iterations=5
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    dec=pants.modifiers.new('Game garment budget','DECIMATE')
    dec.ratio=min(1.0,10000/max(1,sum(len(p.vertices)-2 for p in pants.data.polygons)))
    bpy.ops.object.modifier_apply(modifier=dec.name)
    # Rebuild the source lookup after removing the old trousers, using a
    # position-based leg blend for the replacement rather than torso weights.
    for group in body.vertex_groups: pants.vertex_groups.new(name=group.name)
    for v in pants.data.vertices:
        side='L' if v.co.x>=0 else 'R'
        pelvis_weight=max(0,min(1,(v.co.z-.82)/.18))
        shin_weight=max(0,min(1,(.63-v.co.z)/.20))*(1-pelvis_weight)
        weights={'pelvis':pelvis_weight,'thigh.'+side:1-pelvis_weight-shin_weight,'shin.'+side:shin_weight}
        for name,w in weights.items():
            if w>0: pants.vertex_groups[name].add([v.index],w,'REPLACE')
    added.append(pants)
    # Closed fabric slippers cover toes, with a separate dark rubber sole.
    for side,sign in [('L',1),('R',-1)]:
        for name,location,scale,mat in [('sole',(sign*.105,-.072,.032),(.065,.151,.024),sole),('upper',(sign*.105,-.086,.061),(.063,.148,.055),slippermat)]:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,location=location)
            ob=bpy.context.object; ob.name='pajama_slipper_'+name+'.'+side; ob.scale=scale
            bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
            ob.parent=rig; ob.data.materials.append(mat); bind(ob,'foot.'+side)
            for p in ob.data.polygons:p.use_smooth=True
    for ob in added:
        uv=ob.data.uv_layers.new(name='PajamaUV')
        for loop in ob.data.loops:
            co=ob.data.vertices[loop.vertex_index].co; uv.data[loop.index].uv=(co.x*4,co.z*2)
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    for ob in added: ob.select_set(True)
    bpy.context.view_layer.objects.active=body
    bpy.ops.object.join()
    body['pajamas_v1']=True
    bpy.context.scene.frame_set(1)
    # All wardrobe additions are in the authored human mesh; the runtime's
    # material-preservation rule continues to work without special cases.
    bpy.ops.object.select_all(action='DESELECT')
    for ob in bpy.data.collections['ASSET_violent_patient_v1'].all_objects: ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=BASE+'/violent_patient_v1.glb',export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_skins=True,export_yup=True,export_cameras=False,export_lights=False,export_apply=False,export_force_sampling=True,export_extras=True,export_anim_slide_to_zero=True)
    shutil.copy2(BASE+'/violent_patient_v1.glb',BASE+'/project/assets/models/violent_patient_v1.glb')
    bpy.ops.wm.save_as_mainfile(filepath=BASE+'/violent_patient_work.blend')
    print('PAJAMAS_EXPORTED triangles=',sum(len(p.vertices)-2 for p in body.data.polygons),'bones=',len(rig.data.bones),flush=True)

ward() if MODE=='ward' else violent()
