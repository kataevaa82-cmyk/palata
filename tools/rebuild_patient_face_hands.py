"""Replace the hostile patient's face and hands without rebuilding his outfit.

The new hands have a neutral anatomical rotation: palms medial, thumbs forward.
All new surfaces are merged into the existing skinned mesh and retain its clips.
"""
import bpy, bmesh, math, os, shutil, json
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

BASE='C:/palata'; OUT=BASE+'/build/patient_update'
body=bpy.data.objects['violent_patient_human_mesh']
rig=bpy.data.objects['violent_patient_rig']
collection=body.users_collection[0]
os.makedirs(OUT,exist_ok=True)
backup=OUT+'/violent_patient_before_face_hands.blend'
if not os.path.exists(backup): bpy.ops.wm.save_as_mainfile(filepath=backup,copy=True)
if body.get('face_hands_v3'): raise RuntimeError('Already rebuilt; use the preserved source for revisions')

def active(ob):
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active=ob

def material(name,color,rough=.7):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=rough
    return m

skin=material('VP4_natural_patient_skin',(.34,.245,.185),.76)
lip=material('VP4_natural_lips',(.27,.145,.12),.73)
dark=material('VP4_mouth_crease',(.065,.031,.023),.85)
eye=material('VP4_eye_sclera',(.55,.55,.50),.3)
iris=material('VP4_grey_green_iris',(.095,.14,.125),.35)
pupil=material('VP4_pupil',(.007,.009,.008),.3)
brow=material('VP4_eyebrows',(.042,.03,.021),.9)
nail=material('VP4_natural_nails',(.40,.305,.255),.58)
new=[]

def mesh(name,verts,faces,mat):
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update()
    bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(me); bm.free()
    ob=bpy.data.objects.new(name,me); collection.objects.link(ob); ob.data.materials.append(mat)
    for p in me.polygons:p.use_smooth=True
    return ob

def ellipsoid(name,loc,scale,mat,segments=32,rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc)
    ob=bpy.context.object; ob.name=name; ob.scale=scale
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    ob.data.materials.append(mat)
    for p in ob.data.polygons:p.use_smooth=True
    return ob

def tube(name,points,radii,mat,segments=12):
    verts=[];faces=[]
    for i,p in enumerate(points):
        p=Vector(p); direction=(Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])).normalized()
        ref=Vector((0,1,0)) if abs(direction.y)<.95 else Vector((1,0,0))
        side=direction.cross(ref).normalized(); front=side.cross(direction).normalized()
        for j in range(segments):
            a=j*math.tau/segments; verts.append(p+radii[i]*(side*math.cos(a)+front*math.sin(a)))
    for i in range(len(points)-1):
        for j in range(segments):
            a=i*segments+j;b=i*segments+(j+1)%segments;faces.append((a,b,b+segments,a+segments))
    faces.extend([tuple(reversed(range(segments))),tuple((len(points)-1)*segments+j for j in range(segments))])
    return mesh(name,verts,faces,mat)

def union(objects,name,voxel,budget):
    active(objects[0])
    for ob in objects:ob.select_set(True)
    bpy.ops.object.join(); ob=bpy.context.object; ob.name=name
    mod=ob.modifiers.new('Continuous anatomy','REMESH');mod.mode='VOXEL';mod.voxel_size=voxel;mod.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    smooth=ob.modifiers.new('Smooth anatomical transitions','SMOOTH');smooth.factor=.65;smooth.iterations=5
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    dec=ob.modifiers.new('Game mesh budget','DECIMATE');dec.ratio=min(1,budget/max(1,sum(len(p.vertices)-2 for p in ob.data.polygons)))
    bpy.ops.object.modifier_apply(modifier=dec.name)
    for p in ob.data.polygons:p.use_smooth=True
    return ob

def bind(ob,bone):
    ob.parent=rig;ob.vertex_groups.clear();ob.vertex_groups.new(name=bone).add(list(range(len(ob.data.vertices))),1,'REPLACE')
    new.append(ob);return ob

# Remove only replaced anatomy and the covered toes. Clothes and forearms stay.
bm=bmesh.new();bm.from_mesh(body.data)
remove=[]
for f in bm.faces:
    c=f.calc_center_median(); name=body.data.materials[f.material_index].name.lower()
    replaced_neck='ashen_skin' in name and any(v.co.z>1.485 for v in f.verts)
    arm_material=any(token in name for token in ('ashen_skin','fingernails','frayed_linen'))
    replaced_arm=arm_material and any(abs(v.co.x)>.19 and .72<v.co.z<1.32 for v in f.verts) and c.z<1.36
    if c.z>1.55 or replaced_neck or replaced_arm or ('ashen_skin' in name and c.z<.09): remove.append(f)
bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(body.data);bm.free();body.data.update()

# Smooth continuous head: chin, jaw, cheeks, temples and rounded cranium.
profiles=[(1.553,-.017,.022,.033),(1.567,-.024,.038,.045),(1.587,-.019,.055,.062),
          (1.612,-.006,.065,.075),(1.644,.001,.071,.080),(1.674,.003,.075,.083),
          (1.704,.008,.078,.082),(1.735,.012,.076,.079),(1.760,.014,.065,.068),
          (1.780,.014,.043,.046),(1.793,.014,.004,.005)]
verts=[];faces=[];n=72
for k in range(len(profiles)-1):
    for j in range(5):
        t=j/5
        p0=profiles[max(0,k-1)];p1=profiles[k];p2=profiles[k+1];p3=profiles[min(len(profiles)-1,k+2)]
        z,cy,rx,ry=[.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t) for a,b,c,d in zip(p0,p1,p2,p3)]
        for i in range(n):
            a=i*math.tau/n;x=rx*math.cos(a);y=cy+ry*math.sin(a)
            front=max(0,min(1,(-y-.015)/.05))
            sockets=sum(math.exp(-((x-s*.034)/.022)**2-((z-1.683)/.015)**2) for s in (-1,1))
            cheek=sum(math.exp(-((x-s*.049)/.023)**2-((z-1.65)/.023)**2) for s in (-1,1))
            y+=front*(.006*sockets-.006*cheek)
            verts.append((x,y,z))
z,cy,rx,ry=profiles[-1]
for i in range(n):a=i*math.tau/n;verts.append((rx*math.cos(a),cy+ry*math.sin(a),z))
rows=len(verts)//n
for k in range(rows-1):
    for i in range(n):a=k*n+i;b=k*n+(i+1)%n;faces.append((a,b,b+n,a+n))
faces.extend([tuple(reversed(range(n))),tuple((rows-1)*n+i for i in range(n))])
head=mesh('Regenerated_patient_head',verts,faces,skin)
parts=[head,
       ellipsoid('Nasal_bridge',(0,-.080,1.675),(.011,.017,.033),skin),
       ellipsoid('Nose_tip',(0,-.101,1.651),(.012,.016,.010),skin),
       tube('New_neck',[(0,.001,1.473),(0,-.003,1.507),(0,-.011,1.544),(0,-.013,1.584)],[.051,.049,.045,.045],skin,40)]
for s in (-1,1):
    parts.extend([ellipsoid('Nasal_wing',(s*.011,-.091,1.646),(.007,.010,.006),skin),
                  ellipsoid('Ear',(s*.079,.008,1.657),(.014,.022,.031),skin)])
head=union(parts,'Regenerated_patient_face',.00165,12500);bind(head,'head')
head.vertex_groups.new(name='neck');head.vertex_groups.new(name='chest')
for v in head.data.vertices:
    head_weight=max(0,min(1,(v.co.z-1.545)/.055))
    chest_weight=max(0,min(1,(1.52-v.co.z)/.045))
    neck_weight=1-head_weight-chest_weight
    for name,w in [('head',head_weight),('neck',neck_weight),('chest',chest_weight)]:
        head.vertex_groups[name].add([v.index],w,'REPLACE')
bvh=BVHTree.FromPolygons([v.co for v in head.data.vertices],[list(p.vertices) for p in head.data.polygons])
def surface(x,z,lift=.001):
    p=bvh.ray_cast(Vector((x,-.3,z)),Vector((0,1,0)),.5)[0]
    return Vector((x,p.y-lift if p else -.08,z))

# Almond eyes lie on the facial surface, with proper lids and centred pupils.
for s in (-1,1):
    cx=s*.033
    ev=[];ef=[]
    for j in range(25):
        t=j/24;x=cx+(t-.5)*.031;aperture=math.sin(math.pi*t)
        for k in range(7):
            z=1.682+(-.004+k/6*.009)*aperture+s*(t-.5)*.0015
            ev.append(surface(x,z,.0015+.0015*aperture*math.sin(math.pi*k/6)))
    for j in range(24):
        for k in range(6):a=j*7+k;ef.append((a,a+1,a+8,a+7))
    bind(mesh('Almond_eye',ev,ef,eye),'head')
    eye_pos=surface(cx,1.682,.004)
    bind(ellipsoid('Iris',eye_pos,(.0041,.0007,.0043),iris,24,12),'head')
    bind(ellipsoid('Pupil',eye_pos+Vector((0,-.0007,0)),(.0019,.0005,.0022),pupil,20,12),'head')
    for upper in (True,False):
        points=[]
        for j in range(25):
            t=j/24;x=cx+(t-.5)*.032;z=1.682+(.0052 if upper else -.0042)*math.sin(math.pi*t)+s*(t-.5)*.0015
            points.append(surface(x,z,.002))
        bind(tube('Upper_lid' if upper else 'Lower_lid',points,[.0015]*25,skin,8),'head')
    points=[]
    for j in range(18):
        t=j/17;x=s*(.016+.039*t);z=1.697+.005*math.sin(math.pi*t)-.002*t
        points.append(surface(x,z,.0015))
    bind(tube('Natural_eyebrow',points,[.0006+.0012*math.sin(math.pi*j/17) for j in range(18)],brow,8),'head')
    bind(ellipsoid('Nostril',(s*.009,-.109,1.641),(.0035,.0015,.002),dark,20,12),'head')
    bind(ellipsoid('Ear_inner',(s*.088,-.008,1.657),(.006,.0018,.014),lip,24,14),'head')

# Closed lips replace the old exposed-tooth grimace.
for upper in (True,False):
    points=[];radii=[]
    for j in range(33):
        t=j/32;x=(t-.5)*.047;shape=math.sin(math.pi*t)
        z=1.612+(.0024 if upper else -.0028)*shape
        if upper:z+=.001*math.cos(t*math.pi*4)*shape
        points.append(surface(x,z,.003));radii.append(.0004+.0017*shape)
    bind(tube('Upper_lip' if upper else 'Lower_lip',points,radii,lip,10),'head')
points=[surface((j/32-.5)*.048,1.612,.0036) for j in range(33)]
bind(tube('Closed_mouth_crease',points,[.0005]*33,dark,6),'head')

# Model a relaxed hand before rotating it about the wrist. Dorsal side is
# local -Y and palm +Y. +/-90 degrees maps palms towards the thighs and puts
# both thumbs forward; the old pose exposed the palms unnaturally.
for side,s in [('L',1),('R',-1)]:
    wrist=Vector((s*.335,-.06,.943))
    parts=[ellipsoid('Palm',(s*.343,-.059,.902),(.040,.023,.049),skin),
           tube('Forearm_and_wrist',[(s*.226,-.006,1.32),(s*.256,-.008,1.257),(s*.282,-.012,1.182),(s*.291,-.017,1.146),(s*.306,-.034,1.075),(s*.326,-.051,.995),(s*.331,-.057,.970),(s*.337,-.06,.939),(s*.344,-.059,.919)],[.053,.049,.039,.038,.043,.029,.026,.026,.032],skin,28)]
    nails=[]
    for j,length in enumerate([.073,.084,.079,.064]):
        x=s*(.314+j*.021);z=.873-abs(j-1)*.002
        points=[(x,-.058,z),(x+s*.001,-.055,z-length*.32),(x+s*.002,-.047,z-length*.67),(x+s*.003,-.035,z-length)]
        radii=[.0115,.0105,.0090,.0075]
        parts.append(tube('Finger_'+str(j),points,radii,skin,16))
        parts.append(ellipsoid('Fingertip',points[-1],(.0076,.0076,.0082),skin,20,12))
        tip=Vector(points[-1])+Vector((0,-.0065,.006))
        nails.append(ellipsoid('Fingernail',tip,(.0048,.0014,.0065),nail,20,12))
    thumb=[(s*.316,-.055,.917),(s*.295,-.053,.899),(s*.282,-.046,.878),(s*.279,-.035,.865)]
    parts.append(tube('Thumb',thumb,[.016,.014,.011,.009],skin,20))
    parts.append(ellipsoid('Thumb_tip',thumb[-1],(.009,.009,.010),skin,20,12))
    nails.append(ellipsoid('Thumbnail',Vector(thumb[-1])+Vector((0,-.008,.003)),(.0055,.0015,.007),nail,20,12))
    hand=union(parts,'Anatomical_hand_'+side,.0018,5800)
    rotation=Matrix.Rotation(s*math.pi/2,3,'Z')
    for ob in [hand]+nails:
        for v in ob.data.vertices:
            # Blend pronation through the wrist to avoid a hard seam where
            # the replacement meets the preserved forearm geometry.
            weight=max(0,min(1,(.970-v.co.z)/.038))
            local_rotation=Matrix.Rotation(s*math.pi/2*weight,3,'Z')
            v.co=wrist+local_rotation@(v.co-wrist)
        bind(ob,'hand.'+side)
    forearm=hand.vertex_groups.new(name='forearm.'+side)
    upper_arm=hand.vertex_groups.new(name='upper_arm.'+side)
    for v in hand.data.vertices:
        weight=max(0,min(1,(v.co.z-.935)/.03))
        upper_weight=max(0,min(1,(v.co.z-1.13)/.11))
        if weight:
            forearm.add([v.index],weight-upper_weight,'REPLACE');hand.vertex_groups['hand.'+side].add([v.index],1-weight,'REPLACE')
            upper_arm.add([v.index],upper_weight,'REPLACE')

# Keep the authored material rule (one human_mesh) and all three existing clips.
active(body)
for ob in new:ob.select_set(True)
bpy.ops.object.join()
body['face_hands_v3']=True;body['neutral_palms']='medial, thumbs forward'
bpy.context.scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT')
for ob in bpy.data.collections['ASSET_violent_patient_v1'].all_objects:ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=BASE+'/violent_patient_v1.glb',export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_skins=True,export_yup=True,export_cameras=False,export_lights=False,export_apply=False,export_force_sampling=True,export_extras=True,export_anim_slide_to_zero=True)
shutil.copy2(BASE+'/violent_patient_v1.glb',BASE+'/project/assets/models/violent_patient_v1.glb')
bpy.ops.wm.save_as_mainfile(filepath=BASE+'/violent_patient_work.blend')
report={'triangles':sum(len(p.vertices)-2 for p in body.data.polygons),'bones':len(rig.data.bones),'unweighted':sum(not v.groups for v in body.data.vertices),'actions':[t.name for t in rig.animation_data.nla_tracks],'palms':'medial; thumbs forward'}
with open(OUT+'/face_hands_report.json','w') as f:json.dump(report,f,indent=2)
print('FACE_HANDS_REBUILT',json.dumps(report),flush=True)
