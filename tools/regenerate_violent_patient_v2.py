"""Recreate the hostile hospital patient in the open Blender scene.

Run through tools/invoke_blender_mcp.ps1.  All geometry is authored here;
the former patient is preserved as a timestamped .blend and GLB backup.
Vertex colors carry the worn surfaces into glTF without external textures.
"""

import bpy
import bmesh
import json
import math
import os
import shutil
from datetime import datetime
from mathutils import Vector, Quaternion
from mathutils.noise import noise_vector

BASE = 'C:/palata'
OUT = BASE + '/build/patient_regeneration'
COLLECTION = 'ASSET_violent_patient_v1'
TAU = math.tau
os.makedirs(OUT, exist_ok=True)


def active(obj):
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def material(name, color, roughness=.85, metal=0, micro=0):
    mat = bpy.data.materials.new('VP2_' + name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bs = mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = roughness
    bs.inputs['Metallic'].default_value = metal
    col = mat.node_tree.nodes.new('ShaderNodeVertexColor')
    col.layer_name = 'Color'
    mat.node_tree.links.new(col.outputs['Color'], bs.inputs['Base Color'])
    if micro:
        noise = mat.node_tree.nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 230 if micro > .3 else 160
        noise.inputs['Detail'].default_value = 2
        bump = mat.node_tree.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = micro
        bump.inputs['Distance'].default_value = .0006
        mat.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
        mat.node_tree.links.new(bump.outputs['Normal'], bs.inputs['Normal'])
    return mat


def link(obj):
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    asset.objects.link(obj)
    return obj


def mesh(name, verts, faces, mat=None, bone=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    asset.objects.link(obj)
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    for poly in data.polygons:
        poly.use_smooth = True
    if mat:
        obj.data.materials.append(mat)
    if bone:
        bind(obj, bone)
    return obj


def bind(obj, bone):
    obj.vertex_groups.clear()
    group = obj.vertex_groups.new(name=bone)
    group.add(list(range(len(obj.data.vertices))), 1, 'REPLACE')


def uv(name, loc, scale, mat=None, bone=None, segments=32, rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    obj = link(bpy.context.object)
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    if mat:
        obj.data.materials.append(mat)
    if bone:
        bind(obj, bone)
    return obj


def loft(name, profiles, mat=None, bone=None, segments=48, steps=3, folds=0, cap=True):
    # profiles: (z, center_x, center_y, radius_x, radius_y)
    rings = []
    for i in range(len(profiles)-1):
        a, b = profiles[i], profiles[i+1]
        for j in range(steps):
            t = j / steps
            rings.append(tuple(x*(1-t)+y*t for x, y in zip(a, b)))
    rings.append(profiles[-1])
    verts = []
    for k, (z, cx, cy, rx, ry) in enumerate(rings):
        for j in range(segments):
            angle = j * TAU / segments
            wave = folds * (math.sin(angle*9+z*35) + .42*math.sin(angle*15-z*21))
            verts.append((cx+(rx+wave)*math.cos(angle), cy+(ry+wave*.7)*math.sin(angle), z))
    faces = []
    for k in range(len(rings)-1):
        for j in range(segments):
            a = k*segments+j
            b = k*segments+(j+1)%segments
            faces.append((a, b, b+segments, a+segments))
    if cap:
        faces.extend([tuple(reversed(range(segments))), tuple((len(rings)-1)*segments+j for j in range(segments))])
    return mesh(name, verts, faces, mat, bone)


def tube(name, points, radii, mat=None, bone=None, segments=16, squash=1, caps=True):
    verts = []
    for i, p in enumerate(points):
        p = Vector(p)
        direction = Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])
        direction.normalize()
        ref = Vector((0,1,0))
        if abs(direction.dot(ref)) > .95:
            ref = Vector((1,0,0))
        side = direction.cross(ref).normalized()
        front = side.cross(direction).normalized()
        for j in range(segments):
            a = TAU*j/segments
            verts.append(tuple(p + side*(radii[i]*math.cos(a)) + front*(radii[i]*squash*math.sin(a))))
    faces=[]
    for i in range(len(points)-1):
        for j in range(segments):
            a=i*segments+j
            b=i*segments+(j+1)%segments
            faces.append((a,b,b+segments,a+segments))
    if caps:
        faces.extend([tuple(reversed(range(segments))),tuple((len(points)-1)*segments+j for j in range(segments))])
    return mesh(name,verts,faces,mat,bone)


def seam(name, points, radius, mat, bone):
    return tube(name, points, [radius]*len(points),mat,bone,segments=8)


def join(objects, name):
    active(objects[0])
    for obj in objects:
        obj.select_set(True)
    bpy.ops.object.join()
    obj=bpy.context.object
    obj.name=name
    return obj


def union(objects, name, voxel, mat):
    obj=join(objects,name)
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    remesh=obj.modifiers.new('Continuous sculpted surface','REMESH')
    remesh.mode='VOXEL'
    remesh.voxel_size=voxel
    remesh.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=remesh.name)
    smooth=obj.modifiers.new('Relax sculpt','SMOOTH')
    smooth.factor=.68
    smooth.iterations=4
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    return obj


def paint(obj, style='plain'):
    layer=obj.data.color_attributes.get('Color') or obj.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
    # Materials are normally homogeneous until the final join.
    base=Vector(obj.data.materials[0].diffuse_color[:3])
    for v in obj.data.vertices:
        p=obj.matrix_world@v.co
        grain=noise_vector(p*180)[0]
        stain=noise_vector(p*18+Vector((3,7,1)))[1]
        fine=noise_vector(p*65)[2]
        factor=1+.05*grain+.06*fine
        color=base*factor
        if style=='cloth':
            dirt=max(0,stain-.10)*.62
            low=max(0,min(1,(1.20-p.z)*1.8))
            color*=1-dirt-low*.12
            color=color.lerp(Vector((.12,.09,.055)),max(0,noise_vector(p*7)[0]-.32)*.20)
        elif style=='skin':
            color*=1+.08*stain
            if p.z>1.58:
                for x in (-.045,.045):
                    bruise=math.exp(-((p.x-x)/.034)**2-((p.z-1.711)/.018)**2)*max(0,min(1,(-p.y-.055)*40))
                    color=color.lerp(Vector((.17,.105,.092)),bruise*.68)
                beard=max(0,min(1,(1.68-p.z)*27))*max(0,min(1,(-p.y-.025)*25))
                color=color.lerp(Vector((.15,.155,.135)),beard*.27)
                scalp=max(0,min(1,(p.z-1.77)*19))
                color=color.lerp(Vector((.12,.14,.125)),scalp*.27)
        layer.data[v.index].color=(*[max(.004,min(1,c)) for c in color],1)
    obj.data.color_attributes.active_color=layer


def weight_blend(obj, regions):
    # regions is a short list of body-local bones, preventing cross-limb bleed.
    obj.vertex_groups.clear()
    groups={name:obj.vertex_groups.new(name=name) for name in regions}
    for v in obj.data.vertices:
        weights=[]
        for name in regions:
            a,b=Vector(BONES[name][0]),Vector(BONES[name][1])
            delta=b-a
            t=max(0,min(1,(v.co-a).dot(delta)/delta.length_squared))
            distance=(v.co-a-t*delta).length
            weights.append((name,math.exp(-distance*distance/(.085**2))))
        weights=sorted(weights,key=lambda item:item[1],reverse=True)[:3]
        total=sum(w for _,w in weights)
        if total<1e-15:
            groups[weights[0][0]].add([v.index],1,'REPLACE')
        else:
            for name,w in weights:
                if w/total>.005:
                    groups[name].add([v.index],w/total,'REPLACE')


def build():
    global asset, BONES
    scene=bpy.context.scene
    old=bpy.data.collections.get(COLLECTION)
    if not old:
        raise RuntimeError('Open violent_patient_work.blend before running this script')
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
    backup=OUT+'/backup_'+stamp
    os.makedirs(backup,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=backup+'/violent_patient_before.blend',copy=True)
    for src in (BASE+'/violent_patient_v1.glb',BASE+'/project/assets/models/violent_patient_v1.glb'):
        if os.path.exists(src):
            shutil.copy2(src,backup+('/game_' if '/project/' in src else '/')+'violent_patient_v1.glb')
    if bpy.context.object and bpy.context.object.mode!='OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    # The requested asset is the only destructive replacement target.
    for obj in list(old.all_objects):
        bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.collections.remove(old)
    previous_studio=bpy.data.collections.get('STUDIO_patient_preview')
    if previous_studio:
        for obj in list(previous_studio.all_objects):
            bpy.data.objects.remove(obj,do_unlink=True)
        bpy.data.collections.remove(previous_studio)
    asset=bpy.data.collections.new(COLLECTION)
    scene.collection.children.link(asset)
    for a in list(bpy.data.actions):
        if a.users<=1:
            bpy.data.actions.remove(a)

    skin=material('ashen_skin',(.34,.245,.181),.83,micro=.23)
    lip=material('dry_lips',(.25,.115,.091),.86)
    dark=material('mouth_and_nostrils',(.026,.012,.011),.91)
    eye=material('tired_sclera',(.50,.48,.40),.4)
    iris=material('muted_iris',(.105,.13,.12),.36)
    pupil=material('pupil',(.009,.009,.007),.28)
    teeth=material('aged_teeth',(.49,.43,.29),.7)
    shirt=material('worn_sage_scrubs',(.14,.215,.163),.97,micro=.42)
    trim=material('worn_seams',(.14,.205,.164),.97)
    pants=material('dark_hospital_trousers',(.095,.14,.115),.98,micro=.42)
    linen=material('frayed_linen',(.51,.47,.34),.98,micro=.4)
    ink=material('patient_id_ink',(.052,.068,.055),.9)
    nail=material('fingernails',(.37,.30,.215),.72)

    BONES={
        'pelvis':((0,0,.89),(0,0,1.04),None),
        'spine':((0,0,1.04),(0,.012,1.25),'pelvis'),
        'chest':((0,.012,1.25),(0,.005,1.48),'spine'),
        'neck':((0,.005,1.48),(0,-.026,1.61),'chest'),
        'head':((0,-.026,1.61),(0,-.026,1.83),'neck'),
    }
    for side,s in [('L',1),('R',-1)]:
        BONES.update({
            'clavicle.'+side:((s*.018,.005,1.46),(s*.185,0,1.445),'chest'),
            'upper_arm.'+side:((s*.185,0,1.445),(s*.285,-.012,1.17),'clavicle.'+side),
            'forearm.'+side:((s*.285,-.012,1.17),(s*.335,-.060,.95),'upper_arm.'+side),
            'hand.'+side:((s*.335,-.060,.95),(s*.346,-.082,.856),'forearm.'+side),
            'thigh.'+side:((s*.10,0,.96),(s*.105,-.025,.525),'pelvis'),
            'shin.'+side:((s*.105,-.025,.525),(s*.105,.008,.125),'thigh.'+side),
            'foot.'+side:((s*.105,.008,.125),(s*.105,-.132,.054),'shin.'+side),
            'toe.'+side:((s*.105,-.132,.054),(s*.105,-.208,.047),'foot.'+side),
        })
        for j in range(4):
            x=s*(.32+j*.017)
            BONES['finger%d.%s'%(j,side)]=((x,-.084,.878),(x,-.096,.80),'hand.'+side)
        BONES['thumb.'+side]=((s*.312,-.075,.92),(s*.292,-.12,.86),'hand.'+side)

    arm=bpy.data.armatures.new('violent_patient_skeleton_v2')
    rig=bpy.data.objects.new('violent_patient_rig',arm)
    asset.objects.link(rig)
    active(rig)
    bpy.ops.object.mode_set(mode='EDIT')
    for name,(a,b,parent) in BONES.items():
        bone=arm.edit_bones.new(name)
        bone.head=a
        bone.tail=b
        if parent:
            bone.parent=arm.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.show_in_front=False
    rig.data.display_type='STICK'
    root=bpy.data.objects.new('violent_patient_v1',None)
    asset.objects.link(root)
    rig.parent=root
    root['asset_version']='2.0 - completely regenerated geometry and rig'
    root['authorship']='Procedural original geometry; no downloaded human mesh'
    root['front_axis']='-Y in Blender / +Z in Godot'
    root['material_contract']='human_mesh preserves authored vertex colors in violent_patient.gd'

    # Hollow open-neck top, shoulders and sleeves sewn into a continuous shell.
    torso=loft('scrub_top',[
        (1.00,0,.008,.166,.112),(1.05,0,.006,.16,.109),
        (1.12,0,.012,.143,.093),(1.22,0,.016,.148,.10),
        (1.31,0,.011,.174,.111),(1.40,0,.004,.194,.099),
        (1.46,0,.003,.163,.078),(1.485,0,.002,.09,.060),
        (1.492,0,.001,.059,.047)],shirt,segments=64,steps=5,folds=.0026,cap=False)
    # A V opening reaches down the front of the collar.
    for v in torso.data.vertices:
        if v.co.z>1.40 and v.co.y<0:
            center=max(0,1-abs(v.co.x)/.067)
            v.co.z-=center**1.2*max(0,min(1,(v.co.z-1.40)/.09))*.068
    weight_blend(torso,['pelvis','spine','chest'])
    paint(torso,'cloth')
    cloth_parts=[torso]
    active(torso)
    thickness=torso.modifiers.new('Actual cloth shell','SOLIDIFY')
    thickness.thickness=.006
    bpy.ops.object.modifier_apply(modifier=thickness.name)

    neck=loft('exposed_neck',[(1.425,0,.008,.082,.06),(1.48,0,-.002,.057,.05),(1.535,0,-.018,.043,.044),(1.61,0,-.025,.049,.046)],skin,segments=40,steps=4)
    weight_blend(neck,['chest','neck','head'])
    paint(neck,'skin')
    for s in (-1,1):
        seam('neck_tendon',[(s*.033,-.041,1.505),(s*.022,-.060,1.552),(s*.037,-.056,1.603)],.003,skin,'neck')

    for side,s in [('L',1),('R',-1)]:
        # Short sleeves with relaxed fabric at the shoulder and a stitched hem.
        shoulder=(s*.121,0,1.40)
        sleeve_end=(s*.253,-.008,1.266)
        sleeve=tube('scrub_sleeve.'+side,[shoulder,(s*.186,-.001,1.405),(s*.231,-.004,1.334),sleeve_end],[.056,.075,.067,.065],shirt,segments=40,squash=.94)
        cloth_parts.append(sleeve)
        weight_blend(sleeve,['chest','clavicle.'+side,'upper_arm.'+side])
        paint(sleeve,'cloth')
        cuff=tube('sleeve_double_hem.'+side,[(s*.249,-.008,1.278),sleeve_end],[.066,.066],trim,'upper_arm.'+side,segments=40)
        paint(cuff,'cloth')
        fore=tube('continuous_arm.'+side,[(s*.226,-.006,1.32),(s*.256,-.008,1.257),(s*.282,-.012,1.182),(s*.291,-.017,1.146),(s*.306,-.034,1.075),(s*.326,-.051,.995),(s*.335,-.06,.938)], [.053,.049,.039,.037,.043,.029,.025],skin,segments=32)
        hand=uv('palm.'+side,(s*.343,-.066,.903),(.036,.023,.055),skin)
        hand_parts=[hand]
        for j,length in enumerate([.071,.081,.076,.059]):
            x=s*(.316+j*.018)
            z=.88-(.007 if j in (0,3) else 0)
            points=[(x,-.074,z),(x+s*.002,-.079,z-length*.32),(x+s*.003,-.095,z-length*.68),(x,-.117,z-length*.85)]
            finger=tube('finger.%d.%s'%(j,side),points,[.0095,.0092,.0083,.0065],skin,segments=12)
            hand_parts.append(finger)
            end=points[-1]
            cap=uv('nail.%d.%s'%(j,side),(end[0],end[1]-.003,end[2]+.006),(.0047,.003,.008),nail,'finger%d.%s'%(j,side),segments=12,rings=8)
            paint(cap)
        thumb=tube('thumb.'+side,[(s*.317,-.066,.925),(s*.293,-.082,.904),(s*.286,-.109,.881),(s*.293,-.124,.862)],[.014,.012,.010,.008],skin,segments=14)
        hand_parts.append(thumb)
        hand_parts.append(fore)
        hand=union(hand_parts,'continuous_arm_and_hand.'+side,.0032,skin)
        weight_blend(hand,['upper_arm.'+side,'forearm.'+side,'hand.'+side])
        # Finger surfaces and nails follow the same hand transform.
        for v in hand.data.vertices:
            if v.co.z<.91:
                for group in hand.vertex_groups:
                    group.remove([v.index])
                hand.vertex_groups['hand.'+side].add([v.index],1,'REPLACE')
        paint(hand,'skin')
        for j in range(3):
            seam('hand_tendon',[(s*(.329+j*.011),-.087,.944),(s*(.333+j*.010),-.091,.905),(s*(.33+j*.018),-.090,.878)],.0015,skin,'hand.'+side)

        # Tapered loose trousers with knee bunching and irregular ankle hems.
        leg=loft('trouser_leg.'+side,[
            (.205,s*.105,.008,.055,.047),(.23,s*.105,.01,.061,.052),
            (.28,s*.105,.008,.059,.052),(.34,s*.105,.004,.068,.057),
            (.44,s*.105,-.008,.065,.065),(.51,s*.105,-.027,.060,.067),
            (.55,s*.105,-.03,.066,.061),(.59,s*.105,-.021,.071,.067),
            (.70,s*.105,-.008,.079,.080),(.83,s*.099,.003,.09,.090),
            (.95,s*.088,.012,.097,.104),(1.025,s*.079,.01,.101,.107)],pants,segments=48,steps=4,folds=.0032)
        weight_blend(leg,['pelvis','thigh.'+side,'shin.'+side])
        paint(leg,'cloth')
        ankle=tube('ankle.'+side,[(s*.105,.006,.30),(s*.105,.008,.18),(s*.105,.008,.095)],[.038,.031,.037],skin,segments=24)
        foot=uv('foot.'+side,(s*.105,-.067,.064),(.045,.104,.037),skin)
        heel=uv('heel.'+side,(s*.105,.025,.073),(.039,.045,.049),skin)
        footparts=[ankle,foot,heel]
        for j in range(5):
            x=s*(.068+j*.018)
            y=-.166+abs(j-1)*.008
            toe=uv('toe', (x,y,.049),(.013-j*.0008,.042-j*.003,.020-j*.0015),skin,segments=16,rings=10)
            footparts.append(toe)
        foot=union(footparts,'bare_foot.'+side,.004,skin)
        weight_blend(foot,['shin.'+side,'foot.'+side,'toe.'+side])
        paint(foot,'skin')

    top=union(cloth_parts,'continuous_scrub_top',.0045,shirt)
    weight_blend(top,['pelvis','spine','chest','clavicle.L','clavicle.R','upper_arm.L','upper_arm.R'])
    paint(top,'cloth')

    # Anatomical head: planar cheekbones, narrower jaw, inset orbital regions.
    head=loft('head_sculpt',[
        (1.576,0,-.043,.030,.029),(1.589,0,-.036,.049,.046),
        (1.616,0,-.021,.064,.064),(1.65,0,-.012,.071,.076),
        (1.683,0,-.008,.082,.079),(1.708,0,-.006,.086,.078),
        (1.733,0,-.004,.086,.081),(1.765,0,0,.088,.085),
        (1.797,0,.003,.083,.079),(1.821,0,.006,.068,.065),
        (1.837,0,.006,.044,.044),(1.843,0,.006,.007,.008)],skin,segments=96,steps=5)
    for v in head.data.vertices:
        p=v.co
        front=max(0,min(1,(-p.y-.018)/.055))
        sockets=sum(math.exp(-((p.x-s*.042)/.026)**2-((p.z-1.723)/.021)**2) for s in (-1,1))
        cheeks=sum(math.exp(-((p.x-s*.061)/.024)**2-((p.z-1.69)/.016)**2) for s in (-1,1))
        hollow=sum(math.exp(-((p.x-s*.054)/.025)**2-((p.z-1.652)/.022)**2) for s in (-1,1))
        muzzle=math.exp(-(p.x/.040)**2-((p.z-1.644)/.022)**2)
        p.y+=front*(.014*sockets-.010*cheeks+.007*hollow-.009*muzzle)
    nose=loft('nose_sculpt',[(1.663,0,-.088,.012,.012),(1.674,0,-.096,.022,.018),(1.685,0,-.112,.015,.023),(1.70,0,-.10,.012,.024),(1.73,0,-.083,.009,.015),(1.745,0,-.076,.006,.007)],skin,segments=40,steps=3)
    pieces=[head,nose]
    for s in (-1,1):
        pieces.append(uv('nasal_ala',(s*.015,-.105,1.676),(.01,.014,.008),skin))
        pieces.append(uv('ear_sculpt',(s*.087,.003,1.699),(.017,.024,.036),skin))
    head=union(pieces,'sculpted_head',.0024,skin)
    # Recess a small real oral cavity into the lower face.
    cutter=uv('oral_cavity_cutter',(0,-.091,1.639),(.030,.022,.009),segments=32,rings=16)
    active(head)
    boolean=head.modifiers.new('Recessed mouth opening','BOOLEAN')
    boolean.operation='DIFFERENCE'
    boolean.object=cutter
    bpy.ops.object.modifier_apply(modifier=boolean.name)
    bpy.data.objects.remove(cutter,do_unlink=True)
    bind(head,'head')
    paint(head,'skin')
    uv('mouth_interior',(0,-.088,1.639),(.028,.010,.0075),dark,'head')
    for j in range(6):
        uv('upper_tooth',((j-2.5)*.007,-.105+abs(j-2.5)*.001,1.6425),(.0033,.0027,.0033),teeth,'head',segments=12,rings=8)
    for upper in (True,False):
        points=[]
        for j in range(25):
            t=j/24
            x=(t-.5)*.065
            z=1.639 + ((.0065 if upper else -.006)*math.sin(math.pi*t)) + x*.022
            if upper:
                z+=.0015*math.cos(t*math.pi*4)*math.sin(math.pi*t)
            y=-.098-.012*math.sin(math.pi*t)
            points.append((x,y,z))
        seam('dry_upper_lip' if upper else 'dry_lower_lip',points,.0025,lip,'head')

    for s in (-1,1):
        x=s*.041
        # The sclera is an almond aperture inside the eyelid, not a floating sphere.
        ev=[]
        ef=[]
        for j in range(33):
            t=j/32
            xx=x+(t-.5)*.033
            aperture=math.sin(math.pi*t)
            for k in range(7):
                u=k/6
                z=1.724+(-.0034+u*.0080)*aperture-s*(t-.5)*.004
                y=-.072-.008*aperture*(.75+.25*math.sin(math.pi*u))
                ev.append((xx,y,z))
        for j in range(32):
            for k in range(6):
                a=j*7+k
                ef.append((a,a+1,a+8,a+7))
        mesh('inset_eye_white',ev,ef,eye,'head')
        uv('iris',(x+s*.001,-.080,1.724),(.0046,.0010,.0043),iris,'head',segments=32,rings=16)
        uv('pupil',(x+s*.001,-.081,1.724),(.0022,.0006,.0025),pupil,'head',segments=24,rings=12)
        for upper in (True,False):
            points=[]
            for j in range(25):
                t=j/24
                xx=x+(t-.5)*.035
                z=1.724 + (.0050 if upper else -.0037)*math.sin(math.pi*t) - s*(t-.5)*.004
                y=-.072-.007*math.sin(math.pi*t)
                points.append((xx,y,z))
            seam('upper_eyelid' if upper else 'lower_eyelid',points,.0024 if upper else .0020,skin,'head')
            lidverts=[]
            for j,p in enumerate(points):
                t=j/(len(points)-1)
                xx=x+(t-.5)*.048
                outer_z=1.724+(.018 if upper else -.016)*math.sin(math.pi*t)-s*(t-.5)*.004
                lidverts.extend([p,(xx,-.067-.003*math.sin(math.pi*t),outer_z)])
            mesh('anatomical_eyelid_skin',lidverts,[(j*2,j*2+1,j*2+3,j*2+2) for j in range(len(points)-1)],skin,'head')
        seam('orbital_brow',[(s*.018,-.074,1.738),(s*.034,-.077,1.743),(s*.055,-.071,1.746),(s*.068,-.060,1.741)],.004,skin,'head')
        seam('short_brow',[(s*.021,-.078,1.740),(s*.037,-.08,1.745),(s*.054,-.076,1.748),(s*.066,-.065,1.743)],.0016,ink,'head')
        uv('nostril',(s*.012,-.116,1.673),(.005,.0028,.003),dark,'head',segments=16,rings=10)
        uv('ear_concha',(s*.098,-.017,1.699),(.008,.004,.017),lip,'head',segments=24,rings=16)
        earline=[]
        for j in range(28):
            a=-math.pi*.5+j/27*TAU*.85
            earline.append((s*(.090+.010*math.cos(a)),-.012-.006*math.cos(a),1.700+.028*math.sin(a)))
        seam('ear_helix',earline,.0034,skin,'head')
    # Blend the eyelids, brows and ear rims into the actual facial surface.
    # Surface creases are painted below rather than laid on as visible tubes.
    facial_skin=[obj for obj in asset.objects if obj.type=='MESH' and
                 obj.data.materials and obj.data.materials[0]==skin and
                 obj.vertex_groups.get('head') and len(obj.vertex_groups)==1]
    face=union(facial_skin,'continuous_facial_sculpt',.0022,skin)
    bind(face,'head')
    paint(face,'skin')

    # Neck binding, chest pocket, a sewn identification patch and loose ties.
    seam('V_neck_binding',[(-.062,-.017,1.488),(-.050,-.051,1.465),(0,-.073,1.424),(.050,-.051,1.465),(.062,-.017,1.488)],.0044,trim,'chest')
    pocket=mesh('chest_pocket',[(.054,-.113,1.355),(.13,-.10,1.355),(.127,-.113,1.270),(.089,-.124,1.255),(.052,-.124,1.274)],[(0,1,2,3,4)],shirt,'chest')
    solid=pocket.modifiers.new('Pocket fabric thickness','SOLIDIFY')
    solid.thickness=.0018
    active(pocket)
    bpy.ops.object.modifier_apply(modifier=solid.name)
    paint(pocket,'cloth')
    seam('pocket_stitch',[(.054,-.116,1.353),(.052,-.127,1.274),(.089,-.127,1.255),(.127,-.116,1.270),(.13,-.103,1.353)],.0014,linen,'chest')
    patch=mesh('patient_number_patch',[(-.133,-.108,1.35),(-.05,-.122,1.35),(-.05,-.123,1.317),(-.133,-.110,1.317)],[(0,1,2,3)],linen,'chest')
    paint(patch,'cloth')
    font=bpy.data.curves.new('Patient 04 label','FONT')
    font.body='04 / 17'
    font.size=.020
    font.extrude=.00015
    text=bpy.data.objects.new('patient_04_label',font)
    asset.objects.link(text)
    text.location=(-.127,-.117,1.325)
    text.rotation_euler=(math.pi/2,0,-.14)
    active(text)
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    text=bpy.context.object
    text.data.materials.append(ink)
    bind(text,'chest')
    paint(text)
    seam('hem_seam',[(.168*math.cos(j*TAU/64),.008+.114*math.sin(j*TAU/64),1.017+.002*math.sin(j*.7)) for j in range(65)],.0022,trim,'pelvis')
    # Remnant linen cuff on one wrist; the character is still free to move.
    for i in range(4):
        z=.981+i*.010
        band=loft('linen_wrist_wrap',[(z,.329,-.054,.032,.029),(z+.010,.326,-.052,.031,.029)],linen,'forearm.L',segments=32,steps=1,folds=.0008,cap=False)
        paint(band,'cloth')
    tie=mesh('loose_wrist_linen',[(.359,-.065,.989),(.374,-.066,.989),(.382,-.07,.916),(.362,-.072,.863),(.352,-.071,.87),(.365,-.075,.921)],[(0,1,2,5),(5,2,3,4)],linen,'hand.L')
    active(tie)
    sol=tie.modifiers.new('Linen thickness','SOLIDIFY')
    sol.thickness=.001
    bpy.ops.object.modifier_apply(modifier=sol.name)
    paint(tie,'cloth')

    objects=[o for o in asset.objects if o.type=='MESH']
    for obj in objects:
        if not obj.vertex_groups:
            bind(obj,'head' if max(v.co.z for v in obj.data.vertices)>1.57 else 'chest')
        if not obj.data.color_attributes.get('Color'):
            paint(obj,'skin' if obj.data.materials[0]==skin else 'plain')
    body=join(objects,'violent_patient_human_mesh')
    # Collapse detail just below the visible silhouette; preserve authored weights/colors.
    active(body)
    dec=body.modifiers.new('Game ready sculpt reduction','DECIMATE')
    raw_triangles=sum(len(p.vertices)-2 for p in body.data.polygons)
    dec.ratio=min(1,36000/raw_triangles)
    dec.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=dec.name)
    body.data.validate(verbose=False,clean_customdata=False)
    for polygon in body.data.polygons:
        polygon.use_smooth=True
    def final_z(z):
        t=max(0,min(1,(z-1.53)/.09))
        return z+.028*math.exp(-((z-1.45)/.14)**2)-.045*t*t*(3-2*t)
    for vertex in body.data.vertices:
        vertex.co.z=final_z(vertex.co.z)
    active(rig)
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in rig.data.edit_bones:
        bone.head.z=final_z(bone.head.z)
        bone.tail.z=final_z(bone.tail.z)
    bpy.ops.object.mode_set(mode='OBJECT')
    active(body)
    # Normalize weights after every modifier, including the decimator.
    for v in body.data.vertices:
        all_groups=[(g.group,g.weight) for g in v.groups if g.weight>0]
        groups=sorted(all_groups,key=lambda item:item[1],reverse=True)[:4]
        for index,w in all_groups:
            if index not in [i for i,_ in groups]:
                body.vertex_groups[index].remove([v.index])
        total=sum(w for _,w in groups)
        if not total:
            raise RuntimeError('Unweighted vertex %d'%v.index)
        for index,w in groups:
            body.vertex_groups[index].add([v.index],w/total,'REPLACE')
    body.parent=rig
    mod=body.modifiers.new('Patient skeletal deformation','ARMATURE')
    mod.object=rig
    body['regenerated_original_mesh']=True
    body['surface_details']='Vertex-painted grime, eye bags, stubble, woven linen and scrub seams'

    def rotate(name, axis, angle):
        bone=rig.pose.bones[name]
        rest=rig.data.bones[name].matrix_local.to_quaternion()
        bone.rotation_mode='QUATERNION'
        bone.rotation_quaternion=bone.rotation_quaternion @ rest.inverted() @ Quaternion(Vector(axis),math.radians(angle)) @ rest

    rig.animation_data_create()
    actions=[]
    for action_name,length in [('Violent_Idle',49),('Violent_Run',25),('Violent_Attack',25)]:
        act=bpy.data.actions.new(action_name)
        act.use_fake_user=True
        rig.animation_data.action=act
        for frame in range(1,length+1):
            scene.frame_set(frame)
            t=(frame-1)/(length-1)
            phase=TAU*t
            for b in rig.pose.bones:
                b.rotation_mode='QUATERNION'
                b.rotation_quaternion=(1,0,0,0)
                b.location=(0,0,0)
            rotate('chest',(1,0,0),9)
            rotate('neck',(1,0,0),-6)
            rotate('head',(0,1,0),-4+2*math.sin(phase))
            if action_name=='Violent_Run':
                rotate('pelvis',(0,0,1),4*math.sin(phase))
                rotate('chest',(1,0,0),14+2*math.cos(phase*2))
                rotate('chest',(0,0,1),-5*math.sin(phase))
                for side,offset in [('L',0),('R',math.pi)]:
                    stride=math.sin(phase+offset)
                    rotate('thigh.'+side,(1,0,0),-32*stride-3)
                    rotate('shin.'+side,(1,0,0),9+46*max(0,-stride))
                    rotate('foot.'+side,(1,0,0),15*stride-9)
                    rotate('upper_arm.'+side,(1,0,0),23*stride-9)
                    rotate('forearm.'+side,(1,0,0),-30-8*stride)
                    rotate('hand.'+side,(0,1,0),7 if side=='L' else -10)
            elif action_name=='Violent_Idle':
                rotate('chest',(1,0,0),8+1.2*math.sin(phase))
                for side in ('L','R'):
                    rotate('forearm.'+side,(1,0,0),-8-2*math.sin(phase))
                    rotate('upper_arm.'+side,(0,1,0),-4 if side=='L' else 4)
            else:
                strike=math.sin(math.pi*t)**3
                rotate('chest',(1,0,0),10+14*strike)
                rotate('upper_arm.R',(1,0,0),-10-78*strike)
                rotate('forearm.R',(1,0,0),-36+26*strike)
                rotate('upper_arm.L',(1,0,0),-14-22*strike)
                rotate('forearm.L',(1,0,0),-24)
            bpy.context.view_layer.update()
            # Ground the full deformed mesh each frame to avoid floor penetration.
            dg=bpy.context.evaluated_depsgraph_get()
            evaluated=body.evaluated_get(dg)
            em=evaluated.to_mesh()
            minz=min((evaluated.matrix_world@v.co).z for v in em.vertices)
            evaluated.to_mesh_clear()
            delta=Vector((0,0,.012-minz))
            rig.pose.bones['pelvis'].location=rig.data.bones['pelvis'].matrix_local.to_quaternion().inverted()@delta
            for b in rig.pose.bones:
                b.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=b.name)
                if b.name=='pelvis':
                    b.keyframe_insert(data_path='location',frame=frame,group=b.name)
        actions.append(act)
    rig.animation_data.action=None
    rig['anatomical_flexion_v2']=True
    # Non-overlapping NLA tracks export as three individually named clips.
    for i,act in enumerate(actions):
        track=rig.animation_data.nla_tracks.new()
        track.name=act.name
        strip=track.strips.new(act.name,1+i*60,act)
        strip.extrapolation='NOTHING'
    scene.render.fps=30
    scene.frame_start=1
    scene.frame_end=49
    scene.frame_set(1)

    # Studio is a separate, unexported collection, ready for visual inspection.
    studio=bpy.data.collections.new('STUDIO_patient_preview')
    scene.collection.children.link(studio)
    def stage(obj):
        for col in list(obj.users_collection):
            col.objects.unlink(obj)
        studio.objects.link(obj)
        return obj
    def aim(obj,target):
        obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    for name,pos,power,color,size in [
        ('large_warm_key',(-3,-4,5),420,(1,.83,.68),4),
        ('cool_soft_fill',(3,-2,2.5),180,(.65,.80,1),3),
        ('edge_light',(1,2,3.3),550,(.70,.91,1),2.5),
    ]:
        data=bpy.data.lights.new(name,'AREA')
        data.energy=power
        data.color=color
        data.shape='DISK'
        data.size=size
        obj=bpy.data.objects.new(name,data)
        studio.objects.link(obj)
        obj.location=pos
        aim(obj,(0,0,1))
    bpy.ops.mesh.primitive_plane_add(size=200)
    floor=stage(bpy.context.object)
    floor.name='preview_floor'
    fm=bpy.data.materials.new('Studio charcoal')
    fm.diffuse_color=(.028,.04,.045,1)
    fm.use_nodes=True
    fm.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=fm.diffuse_color
    fm.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.94
    floor.data.materials.append(fm)
    camera_data=bpy.data.cameras.new('Patient portrait camera')
    camera=bpy.data.objects.new('Patient portrait camera',camera_data)
    studio.objects.link(camera)
    camera.location=(2.65,-5.0,2.4)
    aim(camera,(0,0,.96))
    camera_data.type='ORTHO'
    camera_data.ortho_scale=2.20
    scene.camera=camera
    scene.world.color=(.08,.08,.08)
    scene.world.use_nodes=True
    scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.08,.10,.12,1)
    scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.32
    scene.render.engine='CYCLES'
    scene.cycles.samples=32
    scene.cycles.use_denoising=True
    scene.render.resolution_x=900
    scene.render.resolution_y=1100
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='AgX'
    scene.render.filepath=OUT+'/patient_v2_full.png'
    bpy.context.view_layer.update()
    active(body)
    rig.select_set(True)
    root.select_set(True)
    bpy.ops.export_scene.gltf(filepath=OUT+'/violent_patient_v2.glb',export_format='GLB',use_selection=True,
        export_animations=True,export_animation_mode='NLA_TRACKS',export_skins=True,
        export_yup=True,export_cameras=False,export_lights=False,export_apply=False,
        export_force_sampling=True,export_extras=True,export_anim_slide_to_zero=True)
    active(body)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active
                space.shading.type='MATERIAL'
                space.overlay.show_floor=False
                space.overlay.show_extras=False
                space.region_3d.view_distance=3.2
                space.region_3d.view_location=(0,0,.98)
                space.region_3d.view_rotation=camera.rotation_euler.to_quaternion()
    bpy.ops.wm.save_as_mainfile(filepath=BASE+'/violent_patient_work.blend')
    report={'blend':bpy.data.filepath,'candidate_glb':OUT+'/violent_patient_v2.glb','backup':backup,
            'vertices':len(body.data.vertices),'triangles':sum(len(p.vertices)-2 for p in body.data.polygons),
            'bones':len(rig.data.bones),'actions':[a.name for a in actions],
            'materials':len(body.data.materials),'unweighted':sum(not v.groups for v in body.data.vertices)}
    with open(OUT+'/build_report.json','w',encoding='utf-8') as fp:
        json.dump(report,fp,indent=2)
    print('PATIENT_V2_BUILT',json.dumps(report))


build()
