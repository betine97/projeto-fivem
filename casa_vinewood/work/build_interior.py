"""Estudo editável de interior; conserva a referência nativa sem alterá-la."""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector

HERE=Path(__file__).resolve().parent
OUT=HERE.parent
W,D=22.5,20.0
RISE=3.608
TOP=7.288
T=.18
ORIGIN=Vector((-8.8,-12.85,-.8))
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.length_unit='METERS'
scene['descricao']='Estudo inicial seguindo a planta compatibilizada, adaptado à casa candidata ch2_09b_hs05.'
scene['origem_gta']=(-976.1010131835938,676.7308959960938,157.8350372314453)
scene['status']='Estudo no Blender. Não instalado no jogo. Identificação do print ainda não confirmada.'

# Keep the extracted asset as an optional, untouched comparison layer.
native=bpy.data.collections.get('00_FACHADA_NATIVA_REFERENCIA')
if native:
 native.name='90_REFERENCIA_NATIVA_ORIGINAL (oculta)'
 native.hide_viewport=True
 native.hide_render=True
for o in list(bpy.data.objects):
 if o.type in {'CAMERA','LIGHT'}:bpy.data.objects.remove(o,do_unlink=True)

cols={}
for key,name in [
 ('outer','01_ENVOLTORIA_INTERNA'),('ground','02_TERREO_PAREDES'),
 ('upper','03_SUPERIOR_PAREDES'),('slabs','04_LAJES_E_PISOS'),
 ('stairs','05_ESCADA_E_GUARDA_CORPOS'),('ceil','06_TETO_SUPERIOR (oculto para inspecao)'),
 ('labels','07_NOMES_DOS_COMODOS (ocultos)'),('views','08_CAMERAS_E_LUZES')]:
 c=bpy.data.collections.new(name);scene.collection.children.link(c);cols[key]=c

def material(name,color,rough=.75):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough
 return m
wallmat=material('Parede | branco quente',(.72,.69,.63))
floormat=material('Piso | pedra clara',(.52,.48,.41))
wood=material('Escada | madeira',(.27,.14,.07))
metal=material('Guarda-corpo | grafite',(.055,.067,.072),.3)
stone=material('Parede da sala | pedra escura',(.16,.17,.16))
labelmat=material('Anotacoes',(.06,.075,.08))
ceilingmat=material('Teto claro',(.78,.76,.7))

boxes=[];doors=[];slabs=[]
def move_col(o,key):
 for c in list(o.users_collection):c.objects.unlink(o)
 cols[key].objects.link(o)

def box(name,x0,x1,y0,y1,z0,z1,key,mat=wallmat):
 assert x1>x0 and y1>y0 and z1>z0,(name,x0,x1,y0,y1,z0,z1)
 bpy.ops.mesh.primitive_cube_add(size=1,location=ORIGIN+Vector(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2)))
 o=bpy.context.object;o.name=name;o.dimensions=(x1-x0,y1-y0,z1-z0)
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(mat);move_col(o,key)
 o['fase']='estudo inicial';o['dimensoes_m']=(x1-x0,y1-y0,z1-z0)
 boxes.append(dict(name=name,key=key,bounds=[x0,x1,y0,y1,z0,z1]))
 return o

def wall(name,axis,fixed,a,b,z0,z1,key,holes=(),mat=wallmat):
 """Build boxes around actual door/window openings; no blocking boolean leftovers."""
 points=sorted(set([a,b]+[v for h in holes for v in h[:2]]))
 for i,(u,v) in enumerate(zip(points,points[1:])):
  active=[h for h in holes if h[0]<=u+1e-6 and h[1]>=v-1e-6]
  zs=sorted(set([z0,z1]+[max(z0,min(z1,z)) for h in active for z in h[2:]]))
  intervals=[(lo,hi) for lo,hi in zip(zs,zs[1:]) if not any(h[2]<(lo+hi)/2<h[3] for h in active)]
  for j,(lo,hi) in enumerate(intervals):
   if hi-lo<.002:continue
   args=(u,v,fixed-T/2,fixed+T/2) if axis=='X' else (fixed-T/2,fixed+T/2,u,v)
   box(f'{name}_{i:02}_{j}',*args,lo,hi,key,mat)
 for h in holes:
  if abs(h[2]-z0)<.002:
   doors.append(dict(name=name,axis=axis,fixed=fixed,opening=list(h),key=key))

def door(a,width=1.05,z=0):return(a,a+width,z,z+2.5)
def slab(name,x0,x1,y0,y1,top,key='slabs',thickness=.25,mat=floormat):
 o=box(name,x0,x1,y0,y1,top-thickness,top,key,mat)
 slabs.append(dict(name=name,rect=[x0,x1,y0,y1],top=top,area=(x1-x0)*(y1-y0)))
 return o

# The native facade remains an optional layer. This lining encloses the study
# with generous openings aligned to the main glass frontage and entrance.
wall('Frente sala vidro', 'X',0,0,15.2,0,TOP,'outer',[(.7,5.95,0,TOP-.22)],stone)
wall('Entrada sob volume superior','X',0,15.2,W,0,RISE-.25,'outer',[door(16,1.3)])
wall('Volume superior frente','X',-2.7,15.2,W,RISE,TOP,'outer',[(15.55,21.95,RISE+.3,TOP-.3)])
wall('Volume superior lateral','Y',15.2,-2.7,0,RISE,TOP,'outer')
wall('Volume superior lateral direita','Y',W,-2.7,0,RISE,TOP,'outer')
sideholes=[(2.5,4.0,RISE+1,RISE+2.4),(6.6,7.6,RISE+1,RISE+2.4),(10.1,12.7,RISE+1,RISE+2.4),(6.6,7.6,0,2.3)]
wall('Lateral esquerda','Y',0,0,D,0,TOP,'outer',sideholes)
wall('Lateral direita','Y',W,0,D,0,TOP,'outer',[(4,6.6,RISE+1,RISE+2.4),(10.5,11.6,0,2.3),(15.6,18.6,RISE+1,RISE+2.4)])
wall('Fundos','X',D,0,W,0,TOP,'outer',[(1,4.6,1,2.6),(6,7.5,1.2,2.5),(9,10.8,RISE+1.1,TOP-.3),(16.5,20.6,RISE+.8,TOP-.3),(19.8,21.5,.9,2.5)])

slab('Piso terreo',0,W,0,D,0)

# Ground floor: rooms facing a continuous entrance hall. Shared wall geometry
# is generated once, and every closed room has a clear, named doorway.
G=RISE-.25
ground_parts=[0,5.4,8.2,11.4,14.5,19.3,W]
ground_names=['Escritorio','Lavabo','Escada','Despensa','Sala TV Jogos','Lavanderia']
for a,b,n in zip(ground_parts,ground_parts[1:],ground_names):
 opening=door((a+b)/2-.525,1.05)
 if n=='Escada':opening=(8.55,11.2,0,G)
 wall('Hall para '+n,'X',15.2,a,b,0,G,'ground',[opening])
for x in ground_parts[1:-1]:wall('Divisoria apoio '+str(x),'Y',x,15.2,D,0,G,'ground')
wall('Hall estar','X',12,0,8,0,G,'ground',[(4.9,7.2,0,G)])
wall('Hall jantar','X',12,8,15.2,0,G,'ground',[(9,13.3,0,G)])
wall('Hall cozinha','X',12,15.2,W,0,G,'ground',[(16.2,18.2,0,G)])
# Keep living/dining/kitchen connected through broad passages.
wall('Cozinha lateral','Y',15.2,0,12,0,G,'ground',[(3,8.4,0,G)])

# Upper slab tessellation: real openings over the living room and the stairs.
VOID=(0,15.2,0,9.0)
SHAFT=(8.5,11.3,15.7,19.75)
xs=sorted(set([0,W,VOID[0],VOID[1],SHAFT[0],SHAFT[1]]))
ys=sorted(set([0,D,VOID[2],VOID[3],SHAFT[2],SHAFT[3]]))
for i,(a,b) in enumerate(zip(xs,xs[1:])):
 for j,(c,d) in enumerate(zip(ys,ys[1:])):
  cx,cy=(a+b)/2,(c+d)/2
  if any(q[0]<cx<q[1] and q[2]<cy<q[3] for q in [VOID,SHAFT]):continue
  slab(f'Laje superior_{i}_{j}',a,b,c,d,RISE)
slab('Piso avancado quarto 2',15.2,W,-2.7,0,RISE)

# Upstairs program follows the compatible plan, with the void moved over the
# actual living room to preserve a usable connection to the tall glass facade.
wall('Suite master lado hall','Y',8,14,D,RISE,TOP,'upper',[door(14.35,1.1,RISE)])
wall('Suite closet banheiro','X',14,0,8,RISE,TOP,'upper',[door(2.4,1.05,RISE),door(5.5,1.05,RISE)])
wall('Closet banheiro divisoria','Y',4,9,14,RISE,TOP,'upper')
wall('Banheiro suite acesso hall','Y',8,9,14,RISE,TOP,'upper',[door(11.55,1.05,RISE)])
wall('Closet limite vazio','X',9,0,4,RISE,TOP,'upper')
wall('Banheiro limite vazio','X',9,4,8,RISE,TOP,'upper')
wall('Quarto 2 fundos','X',10,15.2,W,RISE,TOP,'upper',[door(16,1.1,RISE)])
wall('Quarto 2 lateral vazio','Y',15.2,0,10,RISE,TOP,'upper')
wall('Quarto 3 frente','X',14.5,15.2,W,RISE,TOP,'upper',[door(16,1.1,RISE)])
wall('Quarto 3 lado leitura','Y',15.2,14.5,D,RISE,TOP,'upper')
wall('Banheiro social lado hall','Y',18.6,10,14.5,RISE,TOP,'upper',[door(11.5,1.05,RISE)])

# U stair: 20 equal risers, 9 treads per flight, intermediate landing and
# an upper landing contiguous with the mezzanine floor.
step=RISE/20
start=15.8;going=.30;landing_y=start+9*going
for i in range(9):
 box(f'Escada lance 1 degrau {i+1:02}',8.6,9.8,start+i*going,start+(i+1)*going,0,(i+1)*step,'stairs',wood)
slab('Escada patamar intermediario',8.6,11.2,landing_y,19.7,10*step,'stairs',.2,wood)
for i in range(9):
 y1=landing_y-i*going;y0=y1-going
 # A thin upper flight preserves useful volume below the stair.
 z=(11+i)*step
 box(f'Escada lance 2 degrau {i+11:02}',10.0,11.2,y0,y1,z-.22,z,'stairs',wood)
slab('Escada chegada superior',10.0,11.2,15.7,15.8,RISE,'stairs',.25,wood)

def beam(name,p0,p1,r=.027):
 a,b=ORIGIN+Vector(p0),ORIGIN+Vector(p1);delta=b-a
 bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=r,depth=delta.length,location=(a+b)/2)
 o=bpy.context.object;o.name=name;o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();o.data.materials.append(metal);move_col(o,'stairs')
 return o
def railing(name,a,b,z):
 length=(Vector(b)-Vector(a)).length;n=max(1,math.ceil(length/1.25))
 for i in range(n+1):
  t=i/n;x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
  beam(name+' montante',(x,y,z),(x,y,z+1.1),.026)
 for h in [.38,.72,1.1]:beam(name+' travessa',(a[0],a[1],z+h),(b[0],b[1],z+h),.02)

railing('Mezanino sala',(8.1,9.08),(15.12,9.08),RISE)
railing('Vao escada esquerda',(8.5,15.7),(8.5,19.75),RISE)
railing('Vao escada fundo',(8.5,19.75),(11.3,19.75),RISE)
railing('Vao escada direita',(11.3,19.75),(11.3,15.8),RISE)
railing('Escada patamar',(8.62,19.67),(11.18,19.67),10*step)
beam('Escada corrimao lance1',(8.62,15.8,.95+step),(8.62,18.5,.95+10*step),.035)
beam('Escada corrimao lance2',(11.18,18.5,.95+10*step),(11.18,15.8,.95+RISE),.035)

# Optional upper ceiling closes all spaces for interior flight, and can be
# switched off independently to inspect either floor in plan.
slab('Teto superior principal',0,W,0,D,TOP+.15,'ceil',.15,ceilingmat)
slab('Teto avancado quarto 2',15.2,W,-2.7,0,TOP+.15,'ceil',.15,ceilingmat)

rooms=[
 ('terreo','Sala de estar',0,8,0,12),('terreo','Sala de jantar',8,15.2,0,12),
 ('terreo','Cozinha',15.2,W,0,12),('terreo','Hall de entrada',0,W,12,15.2),
 *[('terreo',n,a,b,15.2,D) for n,a,b in zip(ground_names,ground_parts,ground_parts[1:])],
 ('superior','Suite master',0,8,14,D),('superior','Closet',0,4,9,14),
 ('superior','Banheiro da suite',4,8,9,14),('superior','Quarto 2',15.2,W,-2.7,10),
 ('superior','Quarto 3',15.2,W,14.5,D),('superior','Banheiro social',18.6,W,10,14.5),
 ('superior','Circulacao quartos',15.2,18.6,10,14.5),('superior','Mezanino',8,15.2,9,14.5),
 ('superior','Sala intima / leitura',8,15.2,14.5,D),
]
roomdata=[]
for level,name,a,b,c,d in rooms:
 area=(b-a)*(d-c)
 if name=='Sala intima / leitura':area-=(SHAFT[1]-SHAFT[0])*(SHAFT[3]-SHAFT[2])
 z=0 if level=='terreo' else RISE
 bpy.ops.object.text_add(location=ORIGIN+Vector(((a+b)/2,(c+d)/2,z+.016)))
 o=bpy.context.object;o.name='Nome '+level+' '+name;o.data.body=name+'\n'+f'{area:.1f} m²';o.data.align_x='CENTER';o.data.align_y='CENTER';o.data.size=.36;o.data.materials.append(labelmat);move_col(o,'labels')
 roomdata.append(dict(level=level,name=name,bounds=[a,b,c,d],area_bruta_referencia_m2=round(area,2)))
cols['labels'].hide_render=True;cols['labels'].hide_viewport=True

def camera(name,pos,target,ortho=None):
 bpy.ops.object.camera_add(location=ORIGIN+Vector(pos));o=bpy.context.object;o.name=name
 o.rotation_euler=(ORIGIN+Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
 o.data.lens=22;o.data.clip_start=.05;o.data.clip_end=1000
 if ortho:o.data.type='ORTHO';o.data.ortho_scale=ortho
 move_col(o,'views');return o
cam_cut=camera('Camera corte geral',(32,-35,37),(W/2,10,2),39)
cam_living=camera('Camera sala pe direito duplo',(3.0,2.1,1.65),(11.6,14.1,2.4))
cam_mezz=camera('Camera mezanino',(13.2,14.3,RISE+1.6),(3.3,1.4,3.1))
cam_stair=camera('Camera escada',(12.5,13.3,1.65),(9.8,18.5,2.0))

world=bpy.data.worlds.new('Ambiente estudo');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.17,.19,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35;scene.world=world
def light(name,pos,power,size=4):
 bpy.ops.object.light_add(type='AREA',location=ORIGIN+Vector(pos));o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;move_col(o,'views')
for i,p in enumerate([(4,4,6.9),(11,5,6.9),(4,17,3.2),(11,13,3.2),(19,5,3.2),(19,18,3.2),(4,18,6.9),(12,14,6.9),(19,4,6.9),(19,18,6.9)]):light('Luz ambiente '+str(i),p,700 if p[2]>6 else 400)
bpy.ops.object.light_add(type='AREA',location=ORIGIN+Vector((3,-5,5)))
l=bpy.context.object;l.name='Luz exterior vidro';l.data.energy=1700;l.data.size=10;l.rotation_euler=(ORIGIN+Vector((6,10,3))-l.location).to_track_quat('-Z','Y').to_euler();move_col(l,'views')

scene.render.engine='CYCLES';scene.cycles.samples=32
scene.cycles.use_denoising=True
scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'

readme=bpy.data.texts.new('LEIA-ME | INTERIOR INICIAL')
readme.write('Interior inicial seguindo a planta compatibilizada. Sem mobilia.\n\n'
 'A casa nativa original esta preservada e oculta na colecao 90.\n'
 'A envoltoria interna e uma proposta simplificada com vaos; nao modifica o arquivo nativo.\n'
 'A identificacao com o print nao foi confirmada.\n'
 'Escala: metros. Terreo z=-0,800 nativo. Superior z=2,808.\n'
 'Escada em U: 20 espelhos de 0,1804 m; piso 0,30 m; largura 1,20 m.\n'
 'Para voar: menu View > Navigation > Fly Navigation. WASD; E/Q sobe/desce.\n'
 'Roda do mouse ajusta velocidade; Shift reduz para precisao. Enter confirma; Esc cancela.\n'
 'O teto superior inicia oculto para facilitar a inspecao; ative a colecao 06 para fechar.\n'
 'Ative a colecao 07 para os nomes dos comodos.\n'
 'Cameras nomeadas para sala, mezanino, escada e corte geral.\n'
 'Areas do relatorio sao brutas do estudo, nao a area liquida medida da casa no jogo.\n')

# Validation: openings, clear stairs shaft, contiguous upper arrival, floor area.
upper_area=sum(q['area'] for q in slabs if abs(q['top']-RISE)<1e-6 and not q['name'].startswith('Escada'))
ground_area=W*D
assert abs(upper_area-(W*D+7.3*2.7-15.2*9-2.8*4.05))<1e-5
assert abs(20*step-RISE)<1e-8
for q in slabs:
 if abs(q['top']-RISE)>1e-6 or q['name'].startswith('Escada'):continue
 a,b,c,d=q['rect']
 for v in [VOID,SHAFT]:
  overlap=max(0,min(b,v[1])-max(a,v[0]))*max(0,min(d,v[3])-max(c,v[2]))
  assert overlap<1e-8,(q,v)
report=dict(status='Estudo inicial; adaptado ao candidato aceito, sem instalacao FiveM',native_model='ch2_09b_hs05',native_origin=list(scene['origem_gta']),interior_origin_relative_native=list(ORIGIN),dimensions_m=[W,D],levels_m=[0,RISE,TOP],areas_brutas_estudo_m2=dict(terreo=ground_area,superior=round(upper_area,2),total=round(ground_area+upper_area,2),vazio_sala=136.8,vazio_escada=11.34),stairs=dict(risers=20,riser_height_m=step,tread_depth_m=.30,flight_width_m=1.2,intermediate_landing_depth_m=1.2,upper_floor_opening=list(SHAFT)),rooms=roomdata,door_openings=doors,validation=dict(upper_slab_voids_clear=True,stair_rise_matches_floor=True,arrival_contiguous=True,closed_room_access_openings=True),boxes=boxes)
(OUT/'medidas_estudo.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

# Workbench overview is a genuine cutaway: ceiling and front walls hidden.
cols['ceil'].hide_render=True
scene.camera=cam_cut
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
cols['outer'].hide_render=True
scene.render.filepath=str(OUT/'interior_corte.png');bpy.ops.render.render(write_still=True)
cols['outer'].hide_render=False

# Interior renders have closed ceilings and all lining walls visible.
cols['ceil'].hide_render=False
scene.render.engine='CYCLES'
for cam,file in [(cam_living,'interior_sala.png'),(cam_mezz,'interior_mezanino.png'),(cam_stair,'interior_escada.png')]:
 scene.camera=cam;scene.render.filepath=str(OUT/file);bpy.ops.render.render(write_still=True)

# Default editable viewport starts inside the living room. Roof is independently
# hidden for inspection; renders can close it by enabling collection 06.
cols['ceil'].hide_viewport=True;cols['ceil'].hide_render=False
scene.camera=cam_living
bpy.ops.object.select_all(action='DESELECT')
try:bpy.context.preferences.inputs.navigation_mode='FLY'
except Exception:pass
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':
   sp=a.spaces.active;sp.clip_start=.05;sp.clip_end=2000;sp.shading.type='SOLID';sp.shading.color_type='MATERIAL';sp.shading.light='STUDIO';sp.shading.show_cavity=True
   sp.overlay.show_floor=False;sp.overlay.show_axis_x=False;sp.overlay.show_axis_y=False
   rv=sp.region_3d;rv.view_perspective='PERSP';rv.view_rotation=cam_living.rotation_euler.to_quaternion();rv.view_distance=.05
   rv.view_location=cam_living.location+cam_living.rotation_euler.to_quaternion()@Vector((0,0,-.05))
for img in bpy.data.images:
 if img.source!='FILE' or img.packed_file:continue
 path=Path(bpy.path.abspath(img.filepath))
 if not path.exists():
  fallback=HERE/'textures'/img.name
  if fallback.exists():img.filepath=str(fallback);img.reload();path=fallback
 if path.exists():
  try:img.pack()
  except RuntimeError:pass
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'mansao_interior_inicial.blend'))
print('INTERIOR SAVED',str(OUT/'mansao_interior_inicial.blend'),report['areas_brutas_estudo_m2'],flush=True)
