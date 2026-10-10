import bpy,sys,addon_utils,math,bmesh,json
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.kdtree import KDTree
from mathutils import noise
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root.parent/'templates_freemode/01_BASE_ROUPAS.blend'))
sc=bpy.context.scene;rig=bpy.data.objects['MP_M_FREEMODE_01_RIG'];rig.hide_select=False
for o in list(bpy.data.objects):
 if o.type in {'CAMERA','LIGHT'}:bpy.data.objects.remove(o,do_unlink=True)
for c in list(bpy.data.collections):
 if c.name=='00_ORIGINAIS_GTA_NAO_EDITAR':
  for o in list(c.objects):bpy.data.objects.remove(o,do_unlink=True)
  bpy.data.collections.remove(c)
body=list(bpy.data.collections['01_CORPO_REFERENCIA'].objects)
for o in body:o.hide_select=False
samples=[]
for o in body:
 for v in o.data.vertices:samples.append((v.co.copy(),{o.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0}))
kd=KDTree(len(samples))
for i,(p,w) in enumerate(samples):kd.insert(p,i)
kd.balance()
cloth=bpy.data.collections.new('TRAJE_LAB_AUTORAL');sc.collection.children.link(cloth)
def own(o):
 for c in list(o.users_collection):c.objects.unlink(o)
 cloth.objects.link(o)
 return o
def weights(o,bone=None):
 o.vertex_groups.clear()
 names=list(rig.data.bones.keys())
 for n in names:o.vertex_groups.new(name=n)
 for v in o.data.vertices:
  if bone:w={bone:1}
  else:
   acc={}
   for p,idx,dist in kd.find_n(v.co,4):
    fac=1/max(dist,.006)**3
    for n,val in samples[idx][1].items():acc[n]=acc.get(n,0)+val*fac
   top=sorted(acc.items(),key=lambda a:a[1],reverse=True)[:4];s=sum(v for n,v in top);w={n:v/s for n,v in top}
  for n,val in w.items():
   if n in o.vertex_groups:o.vertex_groups[n].add([v.index],val,'REPLACE')
 o.parent=rig
 if not any(m.type=='ARMATURE' for m in o.modifiers):o.modifiers.new('ESQUELETO_GTA','ARMATURE').object=rig
def meshobj(name,vs,fs,mat,bone=None):
 m=bpy.data.meshes.new(name);m.from_pydata(vs,[],fs);m.update();o=bpy.data.objects.new(name,m);cloth.objects.link(o);m.materials.append(mat)
 for p in m.polygons:p.use_smooth=True
 weights(o,bone);return o
def basic(name,color,rough=.35,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;return m
white=basic('TECIDO_BRANCO_PROTECAO',(.80,.81,.82),.52)
blue=basic('NITRILO_AZUL',(.003,.068,.32),.46)
black=basic('BORRACHA_GRAFITE',(.012,.016,.019),.34)
yellow=basic('AMARELO_RADIACAO',(.95,.59,.006),.4)
seam=basic('COSTURAS_BRANCAS',(.69,.72,.74),.39)
def crinkles(mat,scale,strength):
 nt=mat.node_tree;n=nt.nodes;l=nt.links;p=n.get('Principled BSDF')
 tc=n.new('ShaderNodeTexCoord');tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=3;tex.inputs['Roughness'].default_value=.7
 l.new(tc.outputs['Generated'],tex.inputs['Vector'])
 vor=n.new('ShaderNodeTexVoronoi');vor.feature='DISTANCE_TO_EDGE';vor.inputs['Scale'].default_value=16;l.new(tex.outputs['Color'],vor.inputs['Vector'])
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=strength;l.new(vor.outputs['Distance'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
 p.inputs['Coat Weight'].default_value=0;p.inputs['Sheen Weight'].default_value=.12
crinkles(white,2.8,.0007);crinkles(blue,2,.00015)
glass=basic('VISOR_PVC_TRANSPARENTE',(.93,.98,1),.10)
gp=glass.node_tree.nodes.get('Principled BSDF');gp.inputs['Transmission Weight'].default_value=0;gp.inputs['IOR'].default_value=1.46
gp.inputs['Roughness'].default_value=.18
# Thin clear PVC: alpha transmission avoids a lens artefact from the radial
# sheet's centre while retaining the reflection of the same visible surface.
nt=glass.node_tree;tr=nt.nodes.new('ShaderNodeBsdfTransparent');mix=nt.nodes.new('ShaderNodeMixShader');mix.inputs[0].default_value=.075
nt.links.new(tr.outputs[0],mix.inputs[1]);nt.links.new(gp.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],nt.nodes.get('Material Output').inputs['Surface'])

def native(name):
 before=set(bpy.data.objects)
 bpy.ops.sollumz.import_assets(directory=str(root/'source'),files=[{'name':name+'.ydd'}],use_custom_settings=True,dwd_import_external_skeleton='FROM_DIR')
 added=set(bpy.data.objects)-before;o=next(o for o in added if o.type=='MESH');world=o.matrix_world.copy();o.parent=None;o.matrix_world=world
 for m in o.modifiers:
  if m.type=='ARMATURE':m.object=rig
 own(o)
 for a in added:
  if a!=o:bpy.data.objects.remove(a,do_unlink=True)
 o.parent=rig;o.name=name;o.data=o.data.copy();return o
top=native('jbib_014_u');bottom=native('lowr_007_u')
for o in [top,bottom]:
 # GTA stores duplicate seam vertices for UV/normal discontinuities. Weld before
 # subdivision so those seams do not shrink into disconnected holes.
 bm=bmesh.new();bm.from_mesh(o.data)
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0003)
 if o==top:
  bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 o.data.materials.clear();o.data.materials.append(white)
 for p in o.data.polygons:p.material_index=0;p.use_smooth=True
 bpy.context.view_layer.objects.active=o;o.select_set(True)
 sub=o.modifiers.new('DOBRAS_SUBDIVISAO','SUBSURF');sub.levels=2;sub.render_levels=2
 # Apply before the armature: preserve the native rest shape and interpolate weights.
 bpy.ops.object.modifier_move_up(modifier=sub.name)
 bpy.ops.object.modifier_apply(modifier=sub.name)
 o.select_set(False)
 o.data.update()
 for v in o.data.vertices:
  p=v.co.copy();r=noise.noise_vector(p*15.0)[0]*.0028+math.sin(p.z*88+p.x*58+noise.noise(p*16)*7)*.0021
  v.co+=v.normal*r
 # Looser disposable suit fit.
 if o==top:
  min_top=min(v.co.z for v in o.data.vertices)
  for v in o.data.vertices:
   if v.co.z>.48:
    collar=max(0,min(1,(.15-abs(v.co.x))/.06))
    v.co.z-=collar*(v.co.z-.48)*.78
   if abs(v.co.x)<.24:
    v.co.x*=1.07;v.co.y*=1.12
    if v.co.z<.10:v.co.z=.10+(v.co.z-.10)*((-.165-.10)/(min_top-.10))
 else:
  old_min=min(v.co.z for v in o.data.vertices)
  for v in o.data.vertices:
   side=1 if v.co.x>=0 else -1;axis=.12*side
   v.co.x=axis+(v.co.x-axis)*1.12;v.co.y*=1.12
   if v.co.z<-.58:
    v.co.z=-.58+(v.co.z+.58)*((-.875+.58)/(old_min+.58))
top.name='MACACAO_TRONCO';bottom.name='MACACAO_PERNAS'

# A single sewn quad surface replaces the inherited upper clothing panels.
# The armhole boundary is shared with each sleeve, so the shoulder seams cannot
# separate or overlap when the inherited skeleton bends.
legacy_top=top
N=64;vs=[];fs=[]
levels=[-.19+i*.035 for i in range(21)]
for j,z in enumerate(levels):
 rx=.186+.037*math.exp(-((z-.36)/.22)**2)
 ry=.146+.023*math.exp(-((z-.33)/.25)**2)
 for i in range(N):
  a=math.tau*i/N
  fold=.0015*math.sin(z*55+a*5)+.001*math.sin(a*11+z*31)
  vs.append(Vector(((rx+fold)*math.cos(a),.021+(ry+fold)*math.sin(a),z)))
j0=14;j1=20;width=6
def hole(j,i):
 return j0<=j<j1 and any((i-c)%N<width or (c-i-1)%N<width for c in [0,32])
for j in range(20):
 for i in range(N):
  if not hole(j,i):fs.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
# Shoulder-to-neck yoke; height decreases at the left and right ends.
for j in range(1,6):
 q=j/5
 for i in range(N):
  a=math.tau*i/N;outer=vs[20*N+i]
  neck=Vector((.085*math.cos(a),.024+.079*math.sin(a),.548))
  v=outer.lerp(neck,q);v.z+=.016*math.sin(math.pi*q)
  vs.append(v)
for j in range(20,25):
 for i in range(N):fs.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
for side,center in [('L',0),('R',32)]:
 ids=[]
 def vi(j,i):return j*N+(i%N)
 ids.extend(vi(j0,i) for i in range(center-width,center+width+1))
 ids.extend(vi(j,center+width) for j in range(j0+1,j1+1))
 ids.extend(vi(j1,i) for i in range(center+width-1,center-width-1,-1))
 ids.extend(vi(j,center-width) for j in range(j1-1,j0,-1))
 start=sum((vs[i] for i in ids),Vector())/len(ids)
 elbow=rig.data.bones['SKEL_'+side+'_Forearm'].head_local.copy()
 end=rig.data.bones['SKEL_'+side+'_Hand'].head_local.copy()
 end=end.lerp(elbow,.06)
 axis=(end-start).normalized();u=Vector((0,1,0));v=axis.cross(u).normalized();u=v.cross(axis).normalized()
 angles=[math.atan2((vs[i]-start).dot(v),(vs[i]-start).dot(u)) for i in ids]
 previous=ids
 for j in range(1,35):
  t=j/34
  if t<.52:co=start.lerp(elbow,t/.52)
  else:co=elbow.lerp(end,(t-.52)/.48)
  co=co+u*.008*math.sin(t*math.pi)
  radius=.078*(1-t)+.035*t
  radius+=.008*math.exp(-((t-.55)/.18)**2)
  current=[]
  for i,a in enumerate(angles):
   rr=radius+.004*math.sin(t*61+a*2.3)*math.sin(math.pi*t)+.0015*math.sin(t*99-a*3)
   point=co+(u*math.cos(a)+v*math.sin(a))*rr
   if t<.12:point=vs[ids[i]].lerp(point,t/.12)
   current.append(len(vs));vs.append(point)
  for i in range(len(ids)):k=(i+1)%len(ids);fs.append((previous[i],current[i],current[k],previous[k]))
  previous=current
top=meshobj('MACACAO_TRONCO_NOVO',vs,fs,white)
bm=bmesh.new();bm.from_mesh(top.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(top.data);bm.free()
bpy.data.objects.remove(legacy_top,do_unlink=True);top.name='MACACAO_TRONCO'

# A fitted glove retains all original finger weights and articulation.
src=bpy.data.objects['REF_TRONCO_015'];glove=src.copy();glove.data=src.data.copy();cloth.objects.link(glove);glove.name='LUVAS_AZUIS'
bm=bmesh.new();bm.from_mesh(glove.data);bm.faces.ensure_lookup_table()
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0003)
def inhand(v):
 side='L' if v.co.x>0 else 'R';hand=rig.data.bones['SKEL_'+side+'_Hand'].head_local;forearm=rig.data.bones['SKEL_'+side+'_Forearm'].head_local
 return (v.co-hand).dot((forearm-hand).normalized())<.027 and abs(v.co.x)>.43
bmesh.ops.delete(bm,geom=[f for f in bm.faces if not all(inhand(v) for v in f.verts)],context='FACES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(glove.data);bm.free()
glove.data.materials.clear();glove.data.materials.append(blue)
for p in glove.data.polygons:p.material_index=0;p.use_smooth=True
for v in glove.data.vertices:v.co+=v.normal*.002

# Fabric tubes, cuffs and boot covers use explicit rings and the original rig.
def tube(name,rings,mat,n=64,bone=None,wrinkle=0):
 vs=[];fs=[]
 for j,(cx,cy,z,rx,ry) in enumerate(rings):
  for i in range(n):
   a=2*math.pi*i/n;w=wrinkle*math.sin(i*1.31+j*2.13)*math.sin(math.pi*j/max(1,len(rings)-1))
   vs.append((cx+(rx+w)*math.cos(a),cy+(ry+w)*math.sin(a),z+wrinkle*.3*math.sin(i*.9+j)))
 for j in range(len(rings)-1):
  for i in range(n):k=j*n+i;fs.append((k,j*n+(i+1)%n,(j+1)*n+(i+1)%n,k+n))
 return meshobj(name,vs,fs,mat,bone)
for side in ['L','R']:
 hand=rig.data.bones['SKEL_'+side+'_Hand'].head_local
 axis=(hand-rig.data.bones['SKEL_'+side+'_Forearm'].head_local).normalized()
 u=Vector((0,1,0));v=axis.cross(u).normalized();u=v.cross(axis).normalized()
 vs=[];fs=[]
 for j in range(7):
  center=hand+axis*(-.025+j*.0035)
  for i in range(48):
   a=i*math.tau/48;r=.034+.0015*math.sin(a*12)+.001*math.sin(j*math.pi)
   vs.append(center+(u*math.cos(a)+v*math.sin(a))*r)
 for j in range(6):
  for i in range(48):fs.append((j*48+i,j*48+(i+1)%48,(j+1)*48+(i+1)%48,(j+1)*48+i))
 meshobj('ELASTICO_PUNHO_'+side,vs,fs,white)
for side,s in [('L',1),('R',-1)]:
 cx=.1585*s
 tube('COBRE_BOTA_'+side,[(cx,-.038,-1.013,.057,.155),(cx,-.038,-1.008,.065,.160),(cx,-.043,-.979,.070,.155),(cx,-.035,-.949,.068,.15),(cx,-.018,-.919,.062,.126),(cx,.012,-.89,.053,.08),(cx,.042,-.863,.046,.053)],blue,bone='SKEL_'+side+'_Foot',wrinkle=.003)
 tube('ELASTICO_TORNOZELO_'+side,[(cx,.043,z,.048+.001*math.sin(i*2),.057) for i,z in enumerate([-.867,-.86,-.853,-.846,-.839])],white,bone='SKEL_'+side+'_Calf')

# Hood surface grows from a rounded rectangular face opening around the head.
n=96;vs=[];fs=[];rim=[]
for j in range(25):
 t=j/24
 for i in range(n):
  a=2*math.pi*i/n;c=math.cos(a);s=math.sin(a)
  # Rounded rectangle at the face, smoothly becoming an ellipsoidal hood.
  xr=.107*math.copysign(abs(c)**.55,c);zr=.145*math.copysign(abs(s)**.55,s)
  if t<=.35:
   q=t/.35;ease=q*q*(3-2*q)
   x=xr*(1-ease)+.145*c*ease;zoff=zr*(1-ease)+.190*s*ease
  else:
   q=(t-.35)/.65;r=math.cos(q*math.pi/2)
   x=.145*c*r;zoff=.190*s*r
  y=-.170+.32*t
  w=math.sin(math.pi*t)*.0015*math.sin(a*13+t*35)
  vs.append((x+w*c,y,.659+zoff+w*s))
  if j==0:rim.append(Vector(vs[-1]))
for j in range(24):
 for i in range(n):fs.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
hood=meshobj('CAPUZ_BRANCO',vs,fs,white,'SKEL_Head')

def cord(name,points,radius,mat,bone=None):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=2;cu.bevel_depth=radius;cu.bevel_resolution=2
 sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
 for p,co in zip(sp.points,points):p.co=(*co,1)
 o=bpy.data.objects.new(name,cu);cloth.objects.link(o);cu.materials.append(mat)
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');o=bpy.context.object;weights(o,bone)
 return o
cord('VEDACAO_VISOR',rim+[rim[0]],.0058,black,'SKEL_Head')
cord('COSTURA_CAPUZ',[p+Vector((p.x*.045,.004,(p.z-.659)*.045)) for p in rim+[rim[0]]],.002,white,'SKEL_Head')
# Actual curved transparent sheet; the visible face belongs to the ped.
vs=[(0,-.184,.659)];fs=[]
for j in range(1,13):
 t=j/12
 for p in rim:vs.append((p.x*t,-.170-.014*(1-t*t),.659+(p.z-.659)*t))
for i in range(n):fs.append((0,1+i,1+(i+1)%n))
for j in range(1,12):
 for i in range(n):a=1+(j-1)*n+i;b=1+(j-1)*n+(i+1)%n;fs.append((a,b,b+n,a+n))
visor=meshobj('VISOR_TRANSPARENTE',vs,fs,glass,'SKEL_Head')
solid=visor.modifiers.new('ESPESSURA_PVC','SOLIDIFY');solid.thickness=.0006

# Front flap and zipper follow the real surface instead of floating in front.
from mathutils.bvhtree import BVHTree
tree=BVHTree.FromPolygons([v.co for v in top.data.vertices],[list(p.vertices) for p in top.data.polygons])
def front(x,z,offset=.003):
 hit=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
 return Vector((x,(hit[0].y if hit[0] is not None else -.14)-offset,z))
flap=[]
for j in range(51):
 z=-.16+j*.0126
 for x in [-.014,.014]:flap.append(front(x,z,.004))
meshobj('ABA_ZIPER',flap,[(j*2,j*2+1,j*2+3,j*2+2) for j in range(50)],white)
for x in [-.014,.014]:cord('COSTURA_ZIPER',[front(x,-.16+j*.0126,.005) for j in range(51)],.0007,seam)
# Waist seam, kept narrow and white like the reference.
tube('COSTURA_CINTURA',[(0,.013,z,.189,.150) for z in [.024,.028,.034,.038]],white)

# Black patch, yellow disk and radiation trefoil on the wearer's left chest.
cx=.119;cz=.365;size=.069
badge=[front(cx+x,cz+z,.007) for x,z in [(-size/2,-size/2),(size/2,-size/2),(size/2,size/2),(-size/2,size/2)]]
meshobj('PATCH_PRETO',badge,[(0,1,2,3)],black)
cord('BORDA_PATCH',badge+[badge[0]],.0011,seam)
def badgeface(name,r,mat,a0=0,a1=2*math.pi,inner=0,offset=.0085):
 vs=[];fs=[];steps=64
 for i in range(steps+1):
  a=a0+(a1-a0)*i/steps
  for rr in [inner,r]:vs.append(front(cx+rr*math.cos(a),cz+rr*math.sin(a),offset))
 for i in range(steps):fs.append((i*2,i*2+1,i*2+3,i*2+2))
 return meshobj(name,vs,fs,mat)
badgeface('DISCO_AMARELO',.029,yellow)
badgeface('NUCLEO_RADIACAO',.0048,black,offset=.0095)
for i in range(3):badgeface('SETOR_RADIACAO',.025,black,math.radians(30+i*120),math.radians(90+i*120),inner=.008,offset=.0095)

# Hide covered skin, leaving the original face in the preview.
for o in body:
 if o.name!='REF_CABECA_000':o.hide_render=True;o.hide_set(True)
head=bpy.data.objects['REF_CABECA_000']
face=basic('ROSTO_PREVIEW_GTA',(.6,.4,.28),.55)
native_face=head.data.materials[0]
if native_face.node_tree:
 node=native_face.node_tree.nodes.get('DiffuseSampler')
 if node and node.image:
  image=face.node_tree.nodes.new('ShaderNodeTexImage');image.image=node.image
  face.node_tree.links.new(image.outputs['Color'],face.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
head.data.materials.clear();head.data.materials.append(face)
for p in head.data.polygons:p.material_index=0
for o in cloth.objects:
 o['traje_lab']=True
 if o.type=='MESH' and not o.data.uv_layers:
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(1,1,1,1);sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.25
sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.use_denoising=True
sc.render.resolution_x=1000;sc.render.resolution_y=1250;sc.render.resolution_percentage=100
if '--quick' in sys.argv:
 sc.cycles.samples=20;sc.render.resolution_x=700;sc.render.resolution_y=875
sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
studio=bpy.data.collections.new('ESTUDIO');sc.collection.children.link(studio)
def aim(o,pos,target):o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',cd);studio.objects.link(cam);sc.camera=cam;cd.type='ORTHO';cd.ortho_scale=2.17;aim(cam,(0,-5,-.07),(0,0,-.07))
for name,pos,power,size in [('KEY',(-3,-4,4),500,4),('FILL',(3,-3,1),250,3),('RIM',(2,2,3),450,3)]:
 d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);studio.objects.link(o);d.energy=power;d.size=size;aim(o,pos,(0,0,0))
ground=basic('FUNDO_BRANCO',(.92,.92,.92),.65)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-1.016));o=bpy.context.object;o.name='CHAO_ESTUDIO';o.data.materials.append(ground)
for c in list(o.users_collection):c.objects.unlink(o)
studio.objects.link(o)
# Authoring file is saved in the native rest pose, never a modified bind pose.
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.wm.save_as_mainfile(filepath=str(root/'TRAJE_LABORATORIO.blend'))
for side,angle in [('L',.42),('R',-.42)]:
 b=rig.pose.bones['SKEL_'+side+'_UpperArm'];r=b.bone.matrix_local.to_quaternion();b.rotation_mode='QUATERNION';b.rotation_quaternion=r.inverted()@Quaternion((0,1,0),angle)@r
bpy.context.view_layer.update()
sc.render.filepath=str(root/'preview_frente.png');bpy.ops.render.render(write_still=True)
aim(cam,(3,-5,.05),(0,0,-.07));sc.render.filepath=str(root/'preview_perspectiva.png');bpy.ops.render.render(write_still=True)
(root/'work/build_stats.json').write_text(json.dumps({'objects':[{ 'name':o.name,'verts':len(o.data.vertices),'faces':len(o.data.polygons)} for o in cloth.objects if o.type=='MESH'],'bones':len(rig.data.bones)},indent=2))
print('BUILD_OK')
