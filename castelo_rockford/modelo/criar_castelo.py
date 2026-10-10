import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'casa_vinewood/work/pydeps'),str(ROOT/'laboratorio_fivem/work/pydeps')]
from shapely.geometry import Polygon,Point,box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles,affinity
import numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True
s.render.resolution_x=1400;s.render.resolution_y=1050;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('Céu claro');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.68,.78,1,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.45
s.view_settings.view_transform='AgX'
collections={}
for name in ['00_IMPLANTACAO','01_TERREO','02_SUITES','03_REUNIAO','04_COBERTURA','05_REFERENCIAS_ESCALA','06_LEGENDAS','07_ILUMINACAO']:
 c=bpy.data.collections.new(name);s.collection.children.link(c);collections[name]=c
C=collections['00_IMPLANTACAO']
def link(o,name):
 o.name=name
 for c in list(o.users_collection):c.objects.unlink(o)
 C.objects.link(o);return o
def mat(name,color,rough=.5,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;return m
stone=mat('Calcario creme / juntas e relevo',(.65,.56,.4),.8)
nt=stone.node_tree;n=nt.nodes;l=nt.links;tc=n.new('ShaderNodeTexCoord');brick=n.new('ShaderNodeTexBrick');brick.inputs['Scale'].default_value=1;brick.inputs['Brick Width'].default_value=.8;brick.inputs['Row Height'].default_value=.36;brick.inputs['Mortar Size'].default_value=.008;brick.inputs['Color1'].default_value=(.67,.6,.47,1);brick.inputs['Color2'].default_value=(.52,.45,.32,1);brick.inputs['Mortar'].default_value=(.37,.32,.24,1);l.new(tc.outputs['UV'],brick.inputs['Vector']);l.new(brick.outputs['Color'],n.get('Principled BSDF').inputs['Base Color']);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.23;bump.inputs['Distance'].default_value=.025;l.new(brick.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],n.get('Principled BSDF').inputs['Normal'])
trim=mat('Cantaria esculpida / marfim',(.75,.67,.51),.65)
roof=mat('Ardosia cinza azulada',(.065,.085,.11),.55)
nt=roof.node_tree;n=nt.nodes;l=nt.links;tc=n.new('ShaderNodeTexCoord');brick=n.new('ShaderNodeTexBrick');brick.inputs['Scale'].default_value=1;brick.inputs['Brick Width'].default_value=.30;brick.inputs['Row Height'].default_value=.20;brick.inputs['Mortar Size'].default_value=.005;brick.inputs['Color1'].default_value=(.045,.065,.085,1);brick.inputs['Color2'].default_value=(.105,.13,.16,1);brick.inputs['Mortar'].default_value=(.022,.025,.03,1);l.new(tc.outputs['Object'],brick.inputs['Vector']);l.new(brick.outputs['Color'],n.get('Principled BSDF').inputs['Base Color']);b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.30;b.inputs['Distance'].default_value=.022;l.new(brick.outputs['Fac'],b.inputs['Height']);l.new(b.outputs['Normal'],n.get('Principled BSDF').inputs['Normal'])
def image_mat(name,path,scale,rough):
 m=mat(name,(.8,.8,.75),rough);nt=m.node_tree;t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(path));tex=nt.nodes.new('ShaderNodeTexCoord');v=nt.nodes.new('ShaderNodeVectorMath');v.operation='SCALE';v.inputs[3].default_value=scale;nt.links.new(tex.outputs['Object'],v.inputs[0]);nt.links.new(v.outputs[0],t.inputs['Vector']);nt.links.new(t.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color']);return m
floor= image_mat('Piso da mansao / pedra polida',OUT/'texturas/piso_mansao.png',1/1.2,.30)
white=image_mat('Parede branca / textura da mansao',OUT/'texturas/parede_branca.png',1/1.8,.85)
nt=white.node_tree;tx=next(n for n in nt.nodes if n.type=='TEX_IMAGE');mix=nt.nodes.new('ShaderNodeMixRGB');mix.inputs[0].default_value=.16;mix.inputs[1].default_value=(.90,.91,.90,1);nt.links.new(tx.outputs['Color'],mix.inputs[2]);nt.links.new(mix.outputs[0],nt.nodes.get('Principled BSDF').inputs['Base Color'])
wood=mat('Madeira nogueira',(.12,.055,.025),.4);gold=mat('Bronze envelhecido',(.40,.24,.08),.35,.75);iron=mat('Ferro preto',(.025,.032,.035),.4,.8)
glass=mat('Vidro levemente azul',(.16,.26,.3),.15,.1);glass.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value=.45
grass=mat('Jardins / verde natural',(.09,.16,.065),.95);paving=mat('Pavers acesso',(.37,.29,.20),.8);asphalt=mat('Acesso veicular fosco',(.14,.15,.16),.9);fabric=mat('Linho claro',(.66,.60,.48),.85);water=mat('Fonte agua',(.08,.25,.30),.13,.2)
def cube(name,loc,size,m,bevel=0):
 x,y,z=[v/2 for v in size]
 vs=[(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
 o=mesh(name,vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)],m);o.location=loc
 if bevel:
  mod=o.modifiers.new('Arestas suaves','BEVEL');mod.width=bevel;mod.segments=2
 return o
def cyl(name,loc,r,depth,m,verts=20,r2=None):
 r2=r if r2 is None else r2
 vs=[(radius*math.cos(j*math.tau/verts),radius*math.sin(j*math.tau/verts),zz) for radius,zz in [(r,-depth/2),(r2,depth/2)] for j in range(verts)]
 fs=[tuple(range(verts-1,-1,-1)),tuple(range(verts,verts*2))]+[(j,(j+1)%verts,(j+1)%verts+verts,j+verts) for j in range(verts)]
 o=mesh(name,vs,fs,m);o.location=loc;return o
def mesh(name,vs,fs,m):
 d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new(name,d);C.objects.link(o);o.data.materials.append(m);return o
def slab(name,poly,z,thick,m):
 vs=[];fs=[]
 for tri in constrained_delaunay_triangles(poly).geoms:
  p=list(tri.exterior.coords)[:3]
  if np.linalg.det(np.stack([np.array(p[1])-p[0],np.array(p[2])-p[0]]))<0:p=p[::-1]
  i=len(vs);vs.extend([(x,y,z) for x,y in p]+[(x,y,z-thick) for x,y in p]);fs.extend([(i,i+1,i+2),(i+5,i+4,i+3)])
 for ring in [poly.exterior]+list(poly.interiors):
  p=list(ring.coords)
  for a,b in zip(p,p[1:]):
   i=len(vs);vs.extend([(a[0],a[1],z),(b[0],b[1],z),(b[0],b[1],z-thick),(a[0],a[1],z-thick)]);fs.append((i,i+1,i+2,i+3))
 o=mesh(name,vs,fs,m)
 if m==floor:
  o.data.materials.append(white)
  for p in o.data.polygons:
   if p.normal.z<-.5:p.material_index=1
 return o
def beam(name,a,b,w,h,m):
 d=Vector(b)-Vector(a);o=cube(name,(Vector(a)+Vector(b))/2,(d.length,w,h),m);o.rotation_euler[2]=math.atan2(d.y,d.x);return o
def wallseg(name,a,b,z,h,m=stone,th=.32):
 a=np.array(a);b=np.array(b);u=(b-a)/np.linalg.norm(b-a)
 if m==stone:
  n=np.array([u[1],-u[0]])
  def offset(p):
   q=CORNER_OFFSETS.get(tuple(np.round(p,6)),n)
   return q*th/2
  aa=offset(a);bb=offset(b);ring=[a+aa,b+bb,b-bb,a-aa]
  v=[(*p,z) for p in ring]+[(*p,z+h) for p in ring]
  o=mesh(name,v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(2,3,7,6),(0,4,7,3),(1,2,6,5)],stone)
  o.data.materials.append(white)
  o.data.polygons[3].material_index=1
 else:o=beam(name,(*a,z+h/2),(*b,z+h/2),th,h,m)
 return o
def rail(name,a,b,z,classic=False):
 beam(name+' corrimao',(*a,z+1.05),(*b,z+1.05),.13 if classic else .055,.12 if classic else .055,trim if classic else iron)
 beam(name+' base',(*a,z+.12),(*b,z+.12),.12,.12,trim if classic else iron)
 length=math.dist(a,b);n=max(2,int(length/.34))
 for j in range(n+1):
  t=j/n;x=a[0]*(1-t)+b[0]*t;y=a[1]*(1-t)+b[1]*t
  if classic:
   cyl(name+' balaustre',(x,y,z+.57),.065,.80,trim,8,r2=.045);cyl(name+' anel',(x,y,z+.53),.10,.18,trim,8)
  else:cube(name+' montante',(x,y,z+.58),(.035,.035,.93),iron)
def arch(name,center,width,height,depth,m):
 x,y,z=center;spring=height-width/2
 cube(name+' lateral E',(x-width/2-.12,y,z+spring/2),(.24,depth,spring),m);cube(name+' lateral D',(x+width/2+.12,y,z+spring/2),(.24,depth,spring),m)
 vs=[];fs=[]
 for j in range(25):
  a=j*math.pi/24
  for yy in [y-depth/2,y+depth/2]:
   for r in [width/2,width/2+.24]:vs.append((x+math.cos(a)*r,yy,z+spring+math.sin(a)*r))
 for j in range(24):
  i=4*j;k=i+4;fs.extend([(i,k,k+1,i+1),(i+2,i+3,k+3,k+2),(i,i+2,k+2,k),(i+1,k+1,k+3,i+3)])
 mesh(name+' arco',vs,fs,m)
def label(text,loc,size=.40):
 old=C;bpy.ops.object.text_add(location=loc);o=link(bpy.context.object,text);o.data.body=text;o.data.size=size;o.data.align_x='CENTER';o.data.materials.append(iron);return o
def chair(name,x,y,z,angle=0):
 objs=[];objs.append(cube(name+' assento',(x,y,z+.46),(.52,.52,.13),fabric,.035));objs.append(cube(name+' encosto',(x,y+.23,z+.86),(.52,.09,.66),fabric,.035))
 for dx in [-.20,.20]:
  for dy in [-.20,.20]:objs.append(cube(name+' pe',(x+dx,y+dy,z+.22),(.055,.055,.44),wood))
 for o in objs:
  p=o.location-Vector((x,y,z));c=math.cos(angle);a=math.sin(angle);o.location=Vector((x+p.x*c-p.y*a,y+p.x*a+p.y*c,z+p.z));o.rotation_euler[2]=angle
def table(name,x,y,z,dx,dy):
 cube(name+' tampo',(x,y,z+.76),(dx,dy,.12),wood,.035)
 for xx in [-dx/2+.2,dx/2-.2]:
  for yy in [-dy/2+.2,dy/2-.2]:cube(name+' pe',(x+xx,y+yy,z+.35),(.14,.14,.7),wood)
def bed(name,x,y,z):
 cube(name+' estrado',(x,y,z+.28),(2.1,2.3,.35),wood,.05);cube(name+' colchao',(x,y,z+.52),(2.0,2.2,.22),fabric,.06);cube(name+' cabeceira',(x,y+1.13,z+.85),(2.2,.15,1.35),wood,.05)
 for xx in [-.5,.5]:cube(name+' travesseiro',(x+xx,y+.7,z+.68),(.75,.42,.15),white,.05)
def human(x,y,z):
 for xx in [-.11,.11]:cyl('Pessoa 1,80m perna',(x+xx,y,z+.46),.09,.80,fabric,10)
 cyl('Pessoa 1,80m corpo',(x,y,z+1.12),.22,.58,iron,12,r2=.27);cyl('Pessoa 1,80m cabeca',(x,y,z+1.66),.14,.27,trim,16)
 for xx in [-.31,.31]:cyl('Pessoa 1,80m braco',(x+xx,y,z+1.05),.07,.62,iron,10)
def car(name,x,y,angle=0,m=iron):
 parts=[cube(name+' carroceria',(x,y,.70),(1.9,4.8,.72),m,.12),cube(name+' cabine',(x,y+.1,1.25),(1.64,2.3,.68),glass,.1)]
 for xx in [-.92,.92]:
  for yy in [-1.55,1.55]:
   o=cyl(name+' roda',(x+xx,y+yy,.38),.34,.18,iron,16);o.rotation_euler[1]=math.pi/2;parts.append(o)
 for o in parts:
  v=o.location-Vector((x,y,0));c=math.cos(angle);a=math.sin(angle);o.location=(x+v.x*c-v.y*a,y+v.x*a+v.y*c,v.z);o.rotation_euler[2]+=angle

# New building is inside the previously cleared polygon; site is accurately georeferenced.
MEAS=json.loads((ROOT/'castelo_rockford/medidas.json').read_text());ANGLE=math.radians(60);ANCHOR=(-946.,207.,66.47)
foot=unary_union([box(-14,-10,14,10)]+[Point(x,y).buffer(3.1,quad_segs=10) for x in [-11.5,11.5] for y in [-8,8]])
worldfoot=affinity.translate(affinity.rotate(foot,60,origin=(0,0)),*ANCHOR[:2]);cleared=Polygon(MEAS['removed_footprint_polygons'][0]);assert worldfoot.difference(cleared).area<.1
sitepoly=affinity.rotate(affinity.translate(box(*MEAS['lot_model_bounds']['min'][:2],*MEAS['lot_model_bounds']['max'][:2]),-ANCHOR[0],-ANCHOR[1]),-60,origin=(0,0))
slab('Envelope medido do lote / apenas referencia',sitepoly,-.12,.2,grass)
slab('Patio de chegada',box(-17,-21,23,-10),.01,.15,paving)
slab('Via esquerda / faixa livre 5m',box(-19.8,-22,-14.8,15),.03,.16,asphalt)
slab('Acesso traseiro / manobra 5,8m',box(-19.8,11.2,21,17),.03,.16,asphalt)
slab('Visitantes direita frontal',box(15,-20.5,23,-4),.025,.15,paving)
for y in [-17,-13.8,-10.6,-7.4]:
 cube('Vaga visitante 2,7 x 5,3',(19,y,.065),(5.3,.055,.015),white)
 car('Visitante',19,y,math.pi/2,wood if y<-15 else iron)
for y in [-15,-7,1,9]:
 # Direction arrows built from triangles, not viewport annotation.
 mesh('Sentido escolta / fundos',[(-17.3,y-.8,.07),(-17.3,y+.4,.07),(-17.8,y+.4,.07),(-17.3,y+1,.07),(-16.8,y+.4,.07)],[(0,1,2),(2,3,4),(0,4,1)],white)
car('Escolta / veiculo 4,8m',-17.3,-4,0)
# Rear covered garage: four 3.1 m stalls, actual 3 m clearance.
for x in [8.85,11.95,15.05,18.15]:
 cube('Garagem pilar',(x-1.5,24.85,1.6),(.3,.3,3.2),stone)
 car('Carro garagem',x,21,0)
cube('Garagem traseira cobertura',(13.5,21,3.5),(13.6,8,.28),trim)
cube('Garagem traseira fundo',(13.5,24.84,1.7),(13.6,.32,3.4),stone)
for x in [6.8,20.2]:cube('Garagem lateral',(x,21,1.7),(.32,8,3.4),stone)
slab('Piso garagem traseira',box(6.7,17,20.3,25),.04,.16,paving)
courtdata=json.loads((OUT/'quadra_original_local.json').read_text())
court=unary_union([Polygon(p) for p in courtdata['polygon']])
courtmat=mat('Quadra existente / referencia de implantacao',(.16,.31,.30),.9)
for poly in (list(court.geoms) if hasattr(court,'geoms') else [court]):
 slab('Quadra original preservada / localizacao medida',poly,-.02,.1,courtmat)
for region in [box(-19.8,-22,-14.8,15),box(-19.8,11.2,21,17),box(6.7,17,20.3,25)]:assert region.intersection(court).area<.01
rect=court.minimum_rotated_rectangle;corners=list(rect.exterior.coords)
for a,b in zip(corners,corners[1:]):beam('Linha perimetro quadra',(*a,.02),(*b,.02),.08,.02,white)
mid1=(np.array(corners[0])+np.array(corners[1]))/2;mid2=(np.array(corners[2])+np.array(corners[3]))/2
beam('Rede quadra referencia',(*mid1,.85),(*mid2,.85),.06,1.6,iron)
for i in range(4):
 cyl('Fonte bacia',(0,-18,.18+i*.10),2.6-i*.06,.12,trim,48)
cyl('Fonte agua',(0,-18,.6),2.3,.04,water,48);cyl('Fonte pedestal',(0,-18,1),.32,1.0,trim,24);cyl('Fonte superior',(0,-18,1.55),1,.2,trim,32,r2=.7)
for x in [-8,8]:
 for y in [-17,-13]:
  cyl('Vaso exterior',(x,y,.55),.5,1.1,trim,16,r2=.65);cyl('Topiaria',(x,y,1.7),.72,1.5,grass,16,r2=.45)
for i in range(5):cube('Escadaria principal',(0,-12.8+i*.4,(i+1)*.14/2),(8,2.8-i*.4,(i+1)*.14),trim)
slab('Patamar chegada porta principal',box(-4,-10.8,4,-9.9),.7,.7,trim)
for i in range(4):
 height=.7-i*.175;cube('Escada acesso funcionarios fundos',(0,10.16+i*.32,height/2),(3.4,.32,height),trim)

BASES=[.7,4.9,9.1];H=4.2;STAIR_HOLE=box(-2.65,3.25,2.65,9.5)
outline=affinity.orient(foot,sign=1) if hasattr(affinity,'orient') else foot
from shapely.geometry.polygon import orient
outline=orient(foot,sign=1)
coords=list(outline.exterior.coords)
CORNER_OFFSETS={}
ring=np.array(coords[:-1])
for j,p in enumerate(ring):
 u=p-ring[j-1];u/=np.linalg.norm(u);v=ring[(j+1)%len(ring)]-p;v/=np.linalg.norm(v)
 n=np.array([u[1],-u[0]]);m=np.array([v[1],-v[0]])
 CORNER_OFFSETS[tuple(np.round(p,6))]=(n+m)/(1+n@m)
def facade(level,z):
 for index,(a,b) in enumerate(zip(coords,coords[1:])):
  a=np.array(a);b=np.array(b);d=b-a;length=float(np.linalg.norm(d));u=d/length
  straight=length>3.5;n=max(1,int(length/3.3));pieces=[]
  if straight:
   for j in range(n):
    start=j*length/n;end=(j+1)*length/n;mid=(start+end)/2
    front=abs(a[1]+10)<.01 and abs(b[1]+10)<.01
    rear=abs(a[1]-10)<.01 and abs(b[1]-10)<.01
    pt=a+u*mid;door=(level==0 and front and abs(pt[0])<2.1) or (level==0 and rear and abs(pt[0])<2.1)
    opening=3.1 if door else 1.35;half=min(opening/2,(end-start)/2-.12)
    if half<=0:continue
    bottom=0 if door else .95;top=2.9 if door else 3.35
    for t0,t1,zz,hh in [(start,mid-half,z,H),(mid+half,end,z,H),(mid-half,mid+half,z,bottom),(mid-half,mid+half,z+top,H-top)]:
     if hh>.001 and t1-t0>.001:wallseg('Fachada %d.%d'%(level,index),a+u*t0,a+u*t1,zz,hh)
    p=a+u*mid;normal=np.array([u[1],-u[0]])
    # Apertures remain open; glass mesh is a separate collection object.
    if not door:
     aa=a+u*(mid-half);bb=a+u*(mid+half);o=wallseg('Vidro janela',aa,bb,z+bottom,top-bottom,glass,.025)
     for t in [mid-half,mid,mid+half]:
      q=a+u*t;wallseg('Caixilho vertical',q-u*.055,q+u*.055,z+bottom,top-bottom,wood,.12)
     for zz in [z+bottom,z+2.1,z+top]:wallseg('Caixilho horizontal',aa,bb,zz,.10,wood,.13)
     for t in [mid-half-.13,mid+half+.13]:q=a+u*t+normal*.1;wallseg('Cantaria lateral',q-u*.09,q+u*.09,z+.75,2.9,trim,.24)
     wallseg('Peitoril',aa-normal*.05-u*.24,bb-normal*.05+u*.24,z+.79,.16,trim,.48)
     wallseg('Verga ornamentada',aa+normal*.1-u*.24,bb+normal*.1+u*.24,z+3.5,.20,trim,.32)
     # Small classical pediment on the window head.
     vs=[(*aa+normal*.25,z+3.7),(*bb+normal*.25,z+3.7),(*p+normal*.25,z+4.05)]
     mesh('Frontao janela',vs,[(0,1,2)],trim)
  else:
   p=(a+b)/2;cx= -11.5 if p[0]<0 else 11.5;cy=-8 if p[1]<0 else 8
   angle=math.atan2(p[1]-cy,p[0]-cx)
   win=abs(math.sin(2*angle))<.47
   if win:
    wallseg('Torre base',a,b,z,.95);wallseg('Torre verga',a,b,z+3.35,.85)
    wallseg('Vidro torre',a,b,z+.95,2.4,glass,.02)
    for zz in [z+.9,z+2.15,z+3.35]:wallseg('Moldura torre',a,b,zz,.1,wood,.15)
   else:wallseg('Parede torre',a,b,z,H)
  # Unbroken floor-level stringcourses and cornice.
  wallseg('Cimalha contorno',a,b,z+H-.25,.23,trim,.45)
  wallseg('Friso inferior',a,b,z+.05,.16,trim,.43)

def partition(name,x0,y0,x1,y1,z,door_at=None,width=1.4):
 a=np.array([x0,y0]);b=np.array([x1,y1]);d=b-a;le=np.linalg.norm(d);u=d/le
 if door_at is None:wallseg(name,a,b,z,H-.26,white,.22);return
 p=door_at
 for t0,t1 in [(0,p-width/2),(p+width/2,le)]:
  if t1>t0:wallseg(name,a+u*t0,a+u*t1,z,H-.26,white,.22)
 wallseg(name+' verga',a+u*(p-width/2),a+u*(p+width/2),z+2.7,H-.26-2.7,white,.22)
 # Door leaves are deliberately opened, leaving the measured passage unobstructed.
 direction=-1 if (abs(u[1])>.9 and x0>0) or (abs(u[0])>.9 and y0<0) or 'Conselho' in name else 1
 v=np.array([-u[1],u[0]])*direction
 leaves=[(p-width/2,width/2),(p+width/2,width/2)] if width>2.1 else [(p-width/2,width)]
 for hinge,leafwidth in leaves:
  q=a+u*hinge+v*leafwidth/2
  o=cube(name+' porta aberta',(*q,z+1.35),(leafwidth,.06,2.7),wood);o.rotation_euler[2]=math.atan2(v[1],v[0])

def stairs(z):
 # Two flights, each 12 risers of 17.5 cm; treads 30 cm; 1.8 m clear width.
 for i in range(12):
  zz=(i+1)*.175;cube('Escada lance subida',(-1.2,3.4+i*.30,z+zz/2),(1.8,.30,zz),floor)
 cube('Patamar intermediario',(0,7.6,z+2.1-.12),(4.4,1.9,.24),floor)
 for i in range(12):
  zz=2.1+(i+1)*.175;cube('Escada lance retorno',(1.2,6.7-i*.30,z+zz-.12),(1.8,.30,.24),floor)
 for x in [-2.2,-.2,.2,2.2]:
  ys=[3.25,6.85];zs=[z+.175,z+2.1] if x<0 else [z+4.2,z+2.1]
  beam('Corrimao escada',(x,ys[0],zs[0]+1),(x,ys[1],zs[1]+1),.06,.06,iron)
  for t in [0,.2,.4,.6,.8,1]:cube('Montante escada',(x,ys[0]*(1-t)+ys[1]*t,(zs[0]*(1-t)+zs[1]*t)+.5),(.045,.045,1),iron)
 rail('Patamar',(-2.2,8.5),(2.2,8.5),z+2.1)

rooms=[]
def room(name,level,x0,y0,x1,y1):
 rooms.append({'name':name,'floor':level,'bounds_local_m':[x0,y0,x1,y1],'approx_area_m2':round((x1-x0)*(y1-y0),1)})
 old=C
 label(name+'\n'+str(round((x1-x0)*(y1-y0)))+' m²',((x0+x1)/2,(y0+y1)/2,BASES[level]+4.04),.4)

for level,z in enumerate(BASES):
 C=collections[['01_TERREO','02_SUITES','03_REUNIAO'][level]]
 slab('Piso pavimento '+str(level),foot if level==0 else foot.difference(STAIR_HOLE),z,.25,floor)
 facade(level,z)
 if level<2:stairs(z)
 if level>0:
  for a,b in [((-2.65,3.25),(-2.65,9.5)),((2.65,3.25),(2.65,9.5)),((-2.65,9.5),(2.65,9.5))]:rail('Guarda-corpo vazio escada',a,b,z)
 if level==0:
  partition('Salao / foyer',-4.2,-10,-4.2,10,z,8,2.4)
  partition('Cozinha / foyer',4.2,-10,4.2,1.5,z,7,2)
  partition('Apoio / foyer',4.2,1.5,4.2,10,z,2.5,1.5)
  partition('Cozinha / servico',4.2,1.5,14,1.5,z,4,1.5)
  partition('Equipe / apoio',4.2,6.5,14,6.5,z,4,1.4)
  room('SALAO DE FESTAS',0,-13.8,-9.8,-4.4,9.8)
  room('FOYER / RECEPCAO',0,-4.05,-9.8,4.05,3.1)
  room('COZINHA PRINCIPAL',0,4.4,-9.8,13.8,1.3)
  room('APOIO / FUNCIONARIOS',0,4.4,1.7,13.8,6.3)
  room('DESPENSA / SERVICO',0,4.4,6.7,13.8,9.8)
  for x,y in [(-9,-5),(-9,1),(-9,7)]:
   cyl('Mesa banquete',(x,y,z+.78),1.15,.12,wood,24);cyl('Pe mesa banquete',(x,y,z+.37),.16,.74,gold,12)
   for j in range(8):
    a=j*math.tau/8;chair('Cadeira banquete',x+math.cos(a)*1.65,y+math.sin(a)*1.65,z,a-math.pi/2)
  cube('Palco modular fundo',(-9,8.5,z+.18),(7,2.5,.36),wood)
  cube('Cozinha bancada parede',(12.9,-4.5,z+.47),(1.35,9,.94),wood)
  cube('Cozinha bancada pedra',(12.9,-4.5,z+.98),(1.5,9,.10),floor)
  cube('Ilha cozinha',(8.5,-4,z+.46),(2.4,4.5,.92),wood);cube('Tampo ilha',(8.5,-4,z+.98),(2.6,4.7,.10),floor)
  for x in [5.4,8.7,12]:cube('Armario despensa',(x,9.3,z+1.15),(2.8,.7,2.3),wood)
 elif level==1:
  for x in [-4.2,4.2]:
   partition('Suite frontal / corredor',x,-10,x,0,z,8,1.4)
   partition('Suite fundos / corredor',x,0,x,10,z,3,1.4)
  for side in [-1,1]:
   a,b=(-14,-4.2) if side<0 else (4.2,14)
   partition('Divisoria suites',a,0,b,0,z)
   for i,(y0,y1) in enumerate([(-9.8,-.2),(.2,9.8)]):
    name=('SUITE MASTER' if side<0 and i==0 else 'SUITE AMPLA')
    room(name,1,a+.2,y0,b-.2,y1)
    bed(name,(a+b)/2,(y0+y1)/2,z)
    partition('Banheiro suite',a+3.2,y0,a+3.2,y0+3.2,z,1.6,1.2)
    partition('Banheiro suite',a,y0+3.2,a+3.2,y0+3.2,z)
    cube('Banheiro bancada',(a+1.6,y0+.5,z+.43),(2.5,.65,.86),floor)
  partition('Equipe / corredor',-4.2,-3,4.2,-3,z,4.2,1.4)
  room('QUARTO FUNCIONARIOS',1,-4,-9.8,4,-3.2)
  bed('Equipe E',-1.8,-6.4,z);bed('Equipe D',1.8,-6.4,z)
 elif level==2:
  partition('Conselho / antessala',-14,2.5,14,2.5,z,14,2.6)
  room('GRANDE SALA DE REUNIAO',2,-13.8,-9.8,13.8,2.3)
  room('ANTESSALA / ESCOLTA',2,-13.8,2.7,-2.85,9.8)
  room('APOIO / COPA',2,2.85,2.7,13.8,9.8)
  table('Mesa conselho',0,-3.8,z,15,2.25)
  for x in range(-6,7):
   chair('Conselho',x,-5.45,z,math.pi);chair('Conselho',x,-2.15,z,0)
  chair('Presidencia',-8.2,-3.8,z,-math.pi/2);chair('Presidencia',8.2,-3.8,z,math.pi/2)
  cube('Tela reuniao',(0,-9.6,z+2.25),(5,.08,2),iron)
  for x in [-8,8]:table('Mesa apoio reuniao',x,6,z,4,1.2)
 # Ceiling fixtures and restrained fill lights are for Blender visualization.
 old=C;C=collections['07_ILUMINACAO']
 for x,y in [(-9,-4),(-9,5),(0,-5),(0,1),(8,-4),(8,5)]:
  cyl('Luminaria embutida',(x,y,z+3.88),.18,.08,trim,16)
  bpy.ops.object.light_add(type='AREA',location=(x,y,z+3.72));o=link(bpy.context.object,'Iluminacao interior '+str(level));o.data.energy=450;o.data.shape='DISK';o.data.size=5;o.data.color=(1,.97,.91)
 C=old

C=collections['04_COBERTURA'];Z=13.3
slab('Forro ultimo andar',foot,Z,.22,white)
# Sloping mansard ring, actual open roof volume (not a solid pyramid).
vs=[(-14.45,-10.45,Z),(14.45,-10.45,Z),(14.45,10.45,Z),(-14.45,10.45,Z),(-10.4,-6.4,Z+4),(10.4,-6.4,Z+4),(10.4,6.4,Z+4),(-10.4,6.4,Z+4)]
mesh('Cobertura mansarda',vs,[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],roof)
for x in [-11.5,11.5]:
 for y in [-8,8]:
  cyl('Torre cimalha',(x,y,Z),3.35,.30,trim,40)
  cyl('Telhado conico torre',(x,y,Z+2.5),3.4,5,roof,48,r2=.06)
  cyl('Remate bronze torre',(x,y,Z+5.18),.10,.65,gold,12,r2=0)
# Central belvedere and steep crown, matching the reference silhouette.
cube('Torre central cantaria',(0,-.5,19.05),(7,6.8,3.5),stone)
for zz in [17.3,20.1,20.75]:cube('Torre central cornija',(0,-.5,zz),(7.45,7.25,.22),trim)
mesh('Torre central mansarda',[(-3.8,-4.15,20.85),(3.8,-4.15,20.85),(3.8,3.15,20.85),(-3.8,3.15,20.85),(-1.25,-1.8,23.7),(1.25,-1.8,23.7),(1.25,.8,23.7),(-1.25,.8,23.7)],[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],roof)
for x in [-2.6,2.6]:
 cube('Torre central pilastra',(x,-3.96,19.05),(.35,.36,3.5),trim)
arch('Janela central monumental',(0,-4,17.7),2,2.7,.22,trim);cube('Janela central vidro',(0,-3.98,18.8),(2,.03,2.25),glass)
for a,b in [((-10,6.2),(10,6.2)),((-10,6.2),(-10,3.4)),((10,6.2),(10,3.4))]:rail('Terraco decorativo cobertura',a,b,17.3,True)
for x in [-7,7]:
 for y in [-7.5,7.5]:
  cube('Chamine base',(x,y,16.8),(.8,.8,3.0),stone);cube('Chamine capitel',(x,y,18.25),(1.15,1.15,.28),trim)
for x in [-8,-4,4,8]:
 cube('Lucarna fachada',(x,-8.6,14.75),(1.65,1,2.45),trim);cube('Lucarna vidro',(x,-9.15,14.7),(1.2,.025,1.8),glass)
 mesh('Lucarna frontao',[(x-.95,-9.2,16),(x+.95,-9.2,16),(x,-9.2,16.7)],[(0,1,2)],trim)
cyl('Remate torre principal',(0,-.5,24),.12,.7,gold,16,r2=0)

# Grand entrance, balcony and front classical columns.
C=collections['01_TERREO']
arch('Entrada principal',(0,-10.25,.7),3.4,3.45,.42,trim)
for x in [-5.5,5.5]:
 cyl('Coluna entrada',(x,-11.8,2.75),.32,4.0,trim,24,r2=.27)
 for z in [.85,4.7]:cube('Capitel coluna',(x,-11.8,z),(.85,.85,.26),trim)
C=collections['02_SUITES'];slab('Sacada principal',box(-6.1,-12.5,6.1,-9.9),4.9,.28,floor)
rail('Sacada frente',(-6,-12.4),(6,-12.4),4.9,True)
for x in [-6,6]:rail('Sacada lado',(x,-12.4),(x,-10),4.9,True)
C=collections['03_REUNIAO']
arch('Moldura central superior',(0,-10.23,9.4),2.5,3.4,.34,trim)
mesh('Frontao principal',[(-4.0,-10.45,13.1),(4,-10.45,13.1),(0,-10.45,14.25)],[(0,1,2)],trim)
C=collections['05_REFERENCIAS_ESCALA'];human(-2,-13.5,.0);human(10,-6,9.1)
label('Personagem 1,80 m',(-2,-14.3,.08),.3)
C=collections['06_LEGENDAS']
label('ENTRADA / VISITANTES',(17,-22,.12),.65)
label('ESCOLTA / ACESSO PELA ESQUERDA',(-23,0,.12),.60)
label('GARAGEM / FUNDOS',(13.5,26,.12),.65)

# Blueprint custom properties keep geography independent of modeling origin.
s['gta_anchor_xyz']=list(ANCHOR);s['gta_rotation_z_degrees']=60;s['building_floor_levels_m']=BASES;s['human_scale_m']=1.80
s['design_stage']='Modelo arquitetonico editavel; exportacao FiveM/colisoes/LOD pendente'
C=collections['07_ILUMINACAO'];bpy.ops.object.light_add(type='SUN',location=(20,-30,40));o=link(bpy.context.object,'Sol fim de tarde');o.rotation_euler=(math.radians(24),math.radians(-18),math.radians(-24));o.data.energy=2.3;o.data.angle=.09
bpy.ops.object.light_add(type='AREA',location=(5,-30,30));o=link(bpy.context.object,'Fill fachada');o.data.energy=1800;o.data.size=25
def camera(name,loc,target,ortho=None,lens=42):
 bpy.ops.object.camera_add(location=loc);o=link(bpy.context.object,name);o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=lens
 if ortho:o.data.type='ORTHO';o.data.ortho_scale=ortho
 return o
cams={
 'exterior':camera('CAM Fachada',(42,-51,33),(0,0,8),None,46),
 'implantacao':camera('CAM Implantacao',(0,0,70),(0,0,0),72),
 'reuniao':camera('CAM Reuniao',(11.5,1.0,11.5),(-2,-5.4,10.3),None,23),
 'salao':camera('CAM Salao',(-5.0,6.9,2.8),(-10,-4,1.9),None,24),
}
# Labels belong to the floor collection, so hide those only in perspective views.
labels=[o for o in bpy.data.objects if o.type=='FONT']
for o in labels:o.hide_render=True
collections['06_LEGENDAS'].hide_render=True
s.camera=cams['exterior'];s.render.filepath=str(OUT/'castelo_exterior.png')
# Packed source images make the .blend portable.
bpy.context.view_layer.update()
for m in [roof,floor,white]:
 for lk in list(m.node_tree.links):
  if lk.from_node.type=='TEX_COORD' and lk.from_socket.name=='Object':
   node=lk.from_node;target=lk.to_socket;m.node_tree.links.remove(lk);m.node_tree.links.new(node.outputs['UV'],target)
for o in bpy.data.objects:
 if o.type!='MESH':continue
 uv=o.data.uv_layers.active or o.data.uv_layers.new(name='UV metros')
 for p in o.data.polygons:
  normal=o.matrix_world.to_3x3()@p.normal;axis=max(range(3),key=lambda i:abs(normal[i]));axes=(0,1) if axis==2 else ((0,2) if axis==1 else (1,2))
  for j in p.loop_indices:
   v=o.matrix_world@o.data.vertices[o.data.loops[j].vertex_index].co;uv.data[j].uv=(v[axes[0]],v[axes[1]])
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'castelo_rockford.blend'))
print('SAVED_BLEND',flush=True)
if '--interior-only' not in sys.argv:bpy.ops.render.render(write_still=True)
for name in ['reuniao','salao']:
 s.camera=cams[name];s.render.filepath=str(OUT/('castelo_'+name+'.png'));bpy.ops.render.render(write_still=True)
# Floor plates, opening true geometry and interior partitions for inspection.
roofcol=collections['04_COBERTURA'];roofcol.hide_render=True
collections['05_REFERENCIAS_ESCALA'].hide_render=True
for level,name in enumerate(['01_TERREO','02_SUITES','03_REUNIAO']):
 if '--interior-only' in sys.argv and level==1:continue
 for k in ['01_TERREO','02_SUITES','03_REUNIAO']:collections[k].hide_render=k!=name
 for o in labels:o.hide_render=o.users_collection[0].name!=name
 s.camera=camera('CAM Planta '+str(level),(0,0,BASES[level]+20),(0,0,BASES[level]),36)
 s.render.resolution_x=1400;s.render.resolution_y=1100;s.render.filepath=str(OUT/('planta_'+str(level)+'.png'));bpy.ops.render.render(write_still=True)
# Restore complete model as its opening state.
for c in collections.values():c.hide_render=False
collections['06_LEGENDAS'].hide_render=True
for o in labels:o.hide_render=True
s.camera=cams['exterior'];s.render.resolution_x=1400;s.render.resolution_y=1050
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':
  area.spaces.active.region_3d.view_distance=65;area.spaces.active.region_3d.view_location=Vector((0,0,8))
  area.spaces.active.shading.type='MATERIAL'
stats={'objects':len(bpy.data.objects),'mesh_objects':sum(o.type=='MESH' for o in bpy.data.objects),'triangles':sum(len(o.data.loop_triangles) for o in []),'rooms':rooms,'world_anchor':ANCHOR,'world_rotation_z':60,'site_bounds_original':MEAS['lot_model_bounds'],'building_footprint_m2':foot.area,'building_footprint_outside_cleared_m2':worldfoot.difference(cleared).area,'drive_lane_width_m':5,'visitor_stalls':4,'rear_garage_stalls':4,'meeting_seats':28,'stairs':{'width_m':1.8,'riser_m':.175,'tread_m':.30,'floor_to_floor_m':4.2},'floor_texture_source':'casa_vinewood/source_assets/piso_marmore.png','texture_note':'Fonte da mansao e marmore/pedra polida, reutilizada sem substituicao por granito inventado.','fivem_installed':False}
for o in bpy.data.objects:
 if o.type=='MESH':o.data.calc_loop_triangles();stats['triangles']+=len(o.data.loop_triangles)
(OUT/'projeto_medidas.json').write_text(json.dumps(stats,indent=2,ensure_ascii=False),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'castelo_rockford.blend'))
print('FINISHED',json.dumps({k:stats[k] for k in ['objects','mesh_objects','triangles','building_footprint_m2']}),flush=True)
