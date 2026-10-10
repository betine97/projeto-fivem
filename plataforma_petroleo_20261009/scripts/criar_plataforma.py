"""Independent offshore authoring asset. Does not modify the island or server."""
import bpy,math,json,random,sys,time,hashlib,shutil
from pathlib import Path
from mathutils import Vector,Matrix
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
for d in ['previews','dados','referencias','modelos']:(ROOT/d).mkdir(parents=True,exist_ok=True)
REF=Path('C:/Users/erons/AppData/Local/Temp/codex-clipboard-0af8d3be-70ad-4b74-94d6-33c80939f094.png')
if REF.exists():shutil.copy2(REF,ROOT/'referencias/plataforma_aprovada.png')
random.seed(9102026)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.name='Petro Esperanca | plataforma completa';scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='METERS';scene.render.fps=24;scene.frame_start=1;scene.frame_end=216

def log(*msg):print('PLATAFORMA:',*msg,flush=True)
def collection(name):
    c=bpy.data.collections.new(name);scene.collection.children.link(c);return c
C={k:collection(k) for k in ['01_JACKET_E_FUNDACOES','02_CONVESES_E_CIRCULACAO','03_EXTRACAO_E_TORRE','04_TRATAMENTO_E_REFINO','05_TUBULACOES_E_VALVULAS','06_ALOJAMENTO_E_CONTROLE','07_HELIPONTO','08_GUINDASTE_PRINCIPAL','09_GUINDASTE_APOIO','10_CARGA_BARRIS_E_EMBARQUE','11_SEGURANCA_E_SINALIZACAO','12_COLISAO_PREPARADA','13_CONTROLES_ANIMACAO','14_PONTOS_INTERACAO','15_APRESENTACAO']}

def material(name,color,metal=0,rough=.6,rust=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1);n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
    if rust:
        geo=n.new('ShaderNodeNewGeometry');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1.6;noise.inputs['Detail'].default_value=3.8;noise.inputs['Roughness'].default_value=.73;l.new(geo.outputs['Position'],noise.inputs['Vector'])
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.52;ramp.color_ramp.elements[0].color=(*color,1);ramp.color_ramp.elements[1].position=.79;ramp.color_ramp.elements[1].color=(.19,.071,.024,1);l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs['Color'],bs.inputs['Base Color'])
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.027;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal'])
    return m
M={
 'steel':material('Aco galvanizado | desgaste procedural',(.32,.37,.37),.75,.48,1),
 'dark':material('Aco estrutural escuro',(.09,.12,.125),.82,.46,1),
 'yellow':material('Pintura amarela industrial',(.87,.55,.035),.40,.54,1),
 'orange':material('Guindastes laranja desgastado',(.74,.19,.045),.48,.55,1),
 'white':material('Paineis claros e intemperie',(.63,.68,.65),.28,.66,1),
 'deck':material('Chapas antiderrapantes',(.19,.23,.225),.64,.76,1),
 'blue':material('Agua de processo | azul',(.035,.20,.31),.42,.46),
 'green':material('Produto refinado | verde',(.08,.27,.16),.46,.5),
 'red':material('Emergencia e linha de gas',(.58,.045,.02),.38,.55),
 'black':material('Borracha e cabos',(.012,.018,.021),.12,.68),
 'glass':material('Vidros azul escuro',(.035,.13,.17),.48,.26),
 'barril':material('Barril azul | petroleo bruto',(.025,.13,.24),.55,.56,1),
 'wood':material('Madeira de pallets',(.28,.16,.07),0,.86),
 'label':material('Letras claras',(.92,.93,.84),.1,.5)
}
for key,color in [('greenlight',(.05,.85,.13)),('amberlight',(1,.43,.015)),('screen',(.045,.35,.51))]:
    m=material(key,color,.2,.4);b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Emission Color'].default_value=(*color,1);b.inputs['Emission Strength'].default_value=2;M[key]=m

class Geo:
    def __init__(self):self.v=[];self.f=[];self.mid=[]
    def face(self,p,mat):
        k=len(self.v);self.v.extend([tuple(a) for a in p]);self.f.append(tuple(range(k,k+len(p))));self.mid.append(mat)
    def box(self,p,s,mat,rot=None):
        p=Vector(p);a=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],float)*np.array(s)/2
        if rot is not None:a=a@np.array(rot).T
        k=len(self.v);self.v.extend([tuple(p+Vector(t)) for t in a]);self.f.extend([tuple(k+i for i in f) for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]]);self.mid.extend([mat]*6)
    def tube(self,a,b,r,mat,sides=10,r2=None,caps=True):
        a=Vector(a);b=Vector(b);d=(b-a).normalized();u=d.cross(Vector((0,0,1)))
        if u.length<.01:u=d.cross(Vector((0,1,0)))
        u.normalize();w=d.cross(u);k=len(self.v)
        for p,rad in [(a,r),(b,r if r2 is None else r2)]:
            self.v.extend([tuple(p+rad*(u*math.cos(j*math.tau/sides)+w*math.sin(j*math.tau/sides))) for j in range(sides)])
        for j in range(sides):self.f.append((k+j,k+(j+1)%sides,k+sides+(j+1)%sides,k+sides+j));self.mid.append(mat)
        if caps:self.f.extend([tuple(k+j for j in reversed(range(sides))),tuple(k+sides+j for j in range(sides))]);self.mid.extend([mat,mat])
    def beam(self,a,b,w,mat):
        a=Vector(a);b=Vector(b);d=b-a;rot=d.to_track_quat('Z','Y').to_matrix();self.box((a+b)/2,(w,w,d.length),mat,rot)
    def torus(self,center,r,minor,mat,axis='Z',n=20,m=6):
        c=Vector(center);k=len(self.v)
        for i in range(n):
            t=i*math.tau/n
            for j in range(m):
                a=j*math.tau/m;p=Vector(((r+minor*math.cos(a))*math.cos(t),(r+minor*math.cos(a))*math.sin(t),minor*math.sin(a)))
                if axis=='X':p=Vector((p.z,p.x,p.y))
                elif axis=='Y':p=Vector((p.x,p.z,p.y))
                self.v.append(tuple(c+p))
        for i in range(n):
            for j in range(m):self.f.append((k+i*m+j,k+((i+1)%n)*m+j,k+((i+1)%n)*m+(j+1)%m,k+i*m+(j+1)%m));self.mid.append(mat)
    def obj(self,name,c,mats,parent=None):
        me=bpy.data.meshes.new(name);me.from_pydata(self.v,[],self.f);me.update()
        for m in mats:me.materials.append(m)
        me.polygons.foreach_set('material_index',self.mid)
        # Smooth round components, retain flat industrial faces.
        for f in me.polygons:f.use_smooth=len(f.vertices)==4 and f.area<2
        uv=me.uv_layers.new(name='UV_Industrial')
        for f in me.polygons:
            axis=max(range(3),key=lambda k:abs(f.normal[k]))
            for li in f.loop_indices:
                v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v.y*.2,v.z*.2) if axis==0 else (v.x*.2,v.z*.2) if axis==1 else (v.x*.2,v.y*.2)
        o=bpy.data.objects.new(name,me);c.objects.link(o)
        if parent:o.parent=parent
        return o

PALETTE=list(M.values());I={k:PALETTE.index(v) for k,v in M.items()};geo={k:Geo() for k in C}
COL=[];STAIRS=[];STATIONS=[]
def collision_box(name,p,s):COL.append(dict(name=name,center=list(p),size=list(s),kind='box'))
def box(group,name,p,s,mat='steel',coll=False):
    geo[group].box(p,s,I[mat])
    if coll:collision_box(name,p,s)
def pipe(group,a,b,r=.12,mat='steel',sides=10):geo[group].tube(a,b,r,I[mat],sides)
def beam(group,a,b,w=.18,mat='dark'):geo[group].beam(a,b,w,I[mat])
def text(body,p,size=.5,mat='label',rot=(math.pi/2,0,0),c='11_SEGURANCA_E_SINALIZACAO'):
    d=bpy.data.curves.new(body,'FONT');d.body=body;d.size=size;d.align_x='CENTER';d.extrude=.006;d.space_character=1.03;d.materials.append(M[mat]);o=bpy.data.objects.new(body,d);C[c].objects.link(o);o.location=p;o.rotation_euler=rot;return o
def rail(a,b,z,group='02_CONVESES_E_CIRCULACAO',gap=None):
    a=np.array(a,float);b=np.array(b,float);length=np.linalg.norm(b-a);count=max(1,math.ceil(length/2.4))
    for i in range(count+1):
        p=a+(b-a)*i/count
        if gap and gap[0]<p[0]<gap[1]:continue
        pipe(group,(*p,z),(*p,z+1.12),.055,'yellow',8)
    for h in [.48,1.12]:pipe(group,(*a,z+h),(*b,z+h),.052,'yellow',8)
    box(group,'Rodape',(*(a+b)/2,z+.065),(abs(b[0]-a[0])+.08,abs(b[1]-a[1])+.08,.13),'yellow')
def railrect(x0,y0,x1,y1,z):
    for a,b in [((x0,y0),(x1,y0)),((x1,y0),(x1,y1)),((x1,y1),(x0,y1)),((x0,y1),(x0,y0))]:rail(a,b,z)
def station(id,label,p,role,step,controls):
    o=bpy.data.objects.new('INTERACAO | '+id,None);C['14_PONTOS_INTERACAO'].objects.link(o);o.location=p;o.empty_display_type='SPHERE';o.empty_display_size=.6;o['interaction_id']=id;o['papel']=role;o['etapa']=step
    STATIONS.append(dict(id=id,label=label,position=list(p),radius=1.8,role=role,step=step,controls=controls))

log('fundacoes e tres conveses')
# Jacket with twelve columns and diagonal bracing. The seabed is visual only.
G='01_JACKET_E_FUNDACOES'
for x in [-26,-9,9,26]:
    for y in [-18,18]:
        pipe(G,(x,y,-32),(x,y,26),1.1,'yellow',14);pipe(G,(x,y,-2),(x,y,3),1.25,'dark',14)
        for z in [-24,-10,4,12,20]:geo[G].torus((x,y,z),1.13,.10,I['steel'])
for z in [-19,-3,12]:
    for y in [-18,18]:
        for a,b in zip([-26,-9,9],[-9,9,26]):
            pipe(G,(a,y,z),(b,y,z),.49,'yellow');pipe(G,(a,y,z),(b,y,z+15),.33,'dark');pipe(G,(b,y,z),(a,y,z+15),.33,'dark')
    for x in [-26,26]:
        pipe(G,(x,-18,z),(x,18,z),.48,'yellow');pipe(G,(x,-18,z),(x,18,z+15),.37,'dark');pipe(G,(x,18,z),(x,-18,z+15),.37,'dark')
for z,s in [(14,(70,48)),(20,(70,48)),(26,(58,39))]:
    if z==26:
        # Cargo well: the hoist must clear the deck above the barrel station.
        for p,ss in [((6,0,z-.18),(46,39,.36)),((-28.5,0,z-.18),(1,39,.36)),((-23,4.75,z-.18),(12,29.5,.36))]:box('02_CONVESES_E_CIRCULACAO','Piso superior com vao de icamento',p,ss,'deck',True)
        for a,b in [((-28,-19.5),(-28,-10)),((-28,-10),(-17,-10)),((-17,-10),(-17,-19.5))]:rail(a,b,z)
    else:box('02_CONVESES_E_CIRCULACAO','Piso do conves '+str(z),(0,0,z-.18),(*s,.36),'deck',True)
    for x in np.arange(-s[0]/2+2,s[0]/2,6):beam(G,(x,-s[1]/2,z-.7),(x,s[1]/2,z-.7),.5,'dark')
    for y in [-s[1]/2,s[1]/2]:beam(G,(-s[0]/2,y,z-.6),(s[0]/2,y,z-.6),.75,'yellow')
    # Rail sides have deliberate openings beside stair landings, cargo and wells.
    for x in [-s[0]/2,s[0]/2]:rail((x,-s[1]/2),(x,s[1]/2),z)
    rail((-s[0]/2,s[1]/2),(s[0]/2,s[1]/2),z)
    front_segments=[((-29,-19.5),(-28,-19.5)),((-17,-19.5),(29,-19.5))] if z==26 else [((-s[0]/2,-s[1]/2),(-29,-s[1]/2)),((-23,-s[1]/2),(s[0]/2,-s[1]/2))]
    for a,b in front_segments:rail(a,b,z)
    for x in np.arange(-s[0]/2+1,s[0]/2,4):
        for y in [-s[1]/2+1,s[1]/2-1]:box('11_SEGURANCA_E_SINALIZACAO','Marca limite piso',(x,y,z+.01),(1,.10,.015),'yellow')

# Stairs are outside deck edges so the upper floors never obstruct the route.
def stairs(id,x,y,z0,z1,width=2.4):
    rise=z1-z0;half=rise/2;n=math.ceil(half/.18);step=half/n;run=.29*n;gap=.5
    G='02_CONVESES_E_CIRCULACAO'
    box(G,'Entrada '+id,(x-width/2-gap/2,y-.30,z0-.12),(width,1.1,.24),'steel',True)
    for f in [0,1]:
        xx=x+(-width/2-gap/2 if f==0 else width/2+gap/2);direction=1 if f==0 else -1;base=y if f==0 else y+run
        for j in range(n):
            yy=base+direction*(j+.5)*.29;zz=z0+f*half+(j+1)*step
            box(G,'Degrau '+id,(xx,yy,zz-.07),(width,.34,.14),'steel',True)
            box('11_SEGURANCA_E_SINALIZACAO','Borda degrau',(xx,yy-direction*.13,zz+.005),(width,.045,.015),'yellow')
        for side in [-1,1]:
            xside=xx+side*(width/2-.07);a=(xside,base,z0+f*half);b=(xside,base+direction*run,z0+(f+1)*half)
            beam(G,a,b,.17,'dark');pipe(G,Vector(a)+Vector((0,0,1.1)),Vector(b)+Vector((0,0,1.1)),.055,'yellow',8)
            for k in range(0,n+1,4):p=Vector(a)+(Vector(b)-Vector(a))*k/n;pipe(G,p,p+Vector((0,0,1.1)),.05,'yellow',8)
    box(G,'Patamar '+id,(x,y+run+.65,z0+half-.12),(width*2+gap,1.6,.24),'steel',True)
    box(G,'Saida '+id,(x+width/2+gap/2,y-.75,z1-.12),(width,1.8,.24),'steel',True)
    rail((x-width-gap/2,y+run+1.4),(x+width+gap/2,y+run+1.4),z0+half)
    # Bridge the outside landing back to the nearest deck.
    if y<-24:box(G,'Passagem '+id,(x+width/2+gap/2,(y+1.1-24)/2,z1-.12),(width,-24-y+1.1,.24),'steel',True)
    STAIRS.append(dict(id=id,from_z=z0,to_z=z1,width=width,step_height=step,step_depth=.29,steps=n*2,position=[x,y,z0],clear_headroom_m=2.3))
box('10_CARGA_BARRIS_E_EMBARQUE','Doca embarque',(27,-36,3.5),(12,11,.45),'steel',True);rail((21,-41.5),(21,-30.5),3.73);rail((33,-41.5),(33,-30.5),3.73)
stairs('EMBARQUE_INFERIOR',26.5,-30.3,3.73,14)
stairs('INFERIOR_PRODUCAO',-26,-30,14,20)
stairs('PRODUCAO_SUPERIOR',23,-29,20,26)
# Add explicit upper deck apron at upper stair exit.
box('02_CONVESES_E_CIRCULACAO','Passarela superior',(24.45,-22,25.88),(2.4,6.5,.24),'steel',True)
station('embarque','Embarque de tripulacao',(27,-35,4.6),'transporte','chegada',['interagir'])

log('torre de extracao e cabeca do poco')
G='03_EXTRACAO_E_TORRE'
# Tapered four leg derrick, internal visible blocks and rail platform.
for i in range(13):
    z=26+i*3.8;span=5.8*(1-i/14)
    if i<12:
        nz=z+3.8;ns=5.8*(1-(i+1)/14)
        for sx in [-1,1]:
            for sy in [-1,1]:beam(G,(sx*span,3+sy*span,z),(sx*ns,3+sy*ns,nz),.32,'dark')
        corners=[(-span,3-span),(span,3-span),(span,3+span),(-span,3+span)]
        for a,b in zip(corners,corners[1:]+corners[:1]):
            beam(G,(*a,z),(*b,z),.22,'steel');beam(G,(*a,z),(b[0]*ns/span,3+(b[1]-3)*ns/span,nz),.16,'yellow')
box(G,'Mesa de perfuracao',(0,3,26.24),(12,12,.48),'steel',True)
for z in [39,54]:
    box(G,'Plataforma tecnica torre',(0,3,z),(10 if z==39 else 7,8,.22),'steel')
    box(G,'Modulo torre',(0,3,z+1.4),(6.5,5,2.8),'white')
    for x in [-2,0,2]:box(G,'Janela torre',(x,.48,z+1.5),(1.3,.03,1),'glass')
pipe(G,(0,3,26.6),(0,3,70),.16,'steel',12)
for yy in [2.7,3.3]:pipe(G,(-.6,yy,70),(-.6,yy,55),.027,'black',6)
box(G,'Bloco viajante',(-.6,3,55),(1.3,1.2,1.7),'orange')
pipe(G,(-.6,3,54),(-.6,3,51),.11,'steel')
for x in [-4.4,4.4]:
    box(G,'Skid manifold',(x,-7,26.4),(3.2,2.2,.8),'dark',True)
    for j in range(3):pipe(G,(x-1+j,-7,26.8),(x-1+j,-7,28.5),.14,'green')
for x in [-4,4]:
    for j in range(4):pipe(G,(x,-1+j*.6,26.8),(x,-1+j*.6,31),.09,'steel')
station('extracao_painel','1. Preparar e acionar a extracao',(7,-2.1,27),'operador','extracao_1',['regular_valvulas','acionar_bomba','parada_emergencia'])
station('extracao_amostra','2. Coletar e separar o lote',(10,-9,21),'operador','extracao_2',['coletar_amostra','regular_separacao','aceitar_lote'])

log('separadores tanques e refino modular')
G='04_TRATAMENTO_E_REFINO'
# Horizontal separation vessels, supported above walkable production deck.
for y in [-7,2,11]:
    for x in [13,25]:box(G,'Suporte separador',(x,y,21.1),(1.4,3.8,2.2),'dark',True)
    pipe(G,(11,y,23.2),(27,y,23.2),1.65,'white',20)
    geo[G].tube((9.9,y,23.2),(11,y,23.2),.38,I['white'],20,r2=1.65);geo[G].tube((27,y,23.2),(28.1,y,23.2),1.65,I['white'],20,r2=.38)
    for xx in [11.3,14.2,24,26.7]:geo[G].torus((xx,y,23.2),1.69,.055,I['steel'],'X',24,6)
    pipe(G,(19,y,24.8),(19,y,26),.2,'red');pipe(G,(14,y,21.8),(14,y,20.6),.24,'blue')
    collision_box('Separador de lote',(19,y,23.2),(18,3.3,3.3))
for x,y,r,h in [(19,7,1.8,17),(25,10,1.35,13),(13,14,2.4,9)]:
    pipe(G,(x,y,26),(x,y,26+h),r,'white',22)
    geo[G].tube((x,y,26+h),(x,y,26+h+.7),r,I['steel'],22,r2=.1)
    for z in np.arange(27,26+h,3):geo[G].torus((x,y,z),r+.03,.06,I['yellow'])
    pipe(G,(x+r+.35,y,26),(x+r+.35,y,26+h),.045,'yellow',6)
    for z in np.arange(26.3,26+h,.32):pipe(G,(x+r+.20,y-.28,z),(x+r+.20,y+.28,z),.028,'yellow',6)
    collision_box('Coluna de processamento',(x,y,26+h/2),(r*2,r*2,h))
for x in [-27,-20,-13]:
    pipe(G,(x,14,14.2),(x,14,19.1),2.15,'white',20);geo[G].tube((x,14,19.1),(x,14,19.7),2.15,I['white'],20,r2=.4)
    for z in [14.4,16.8,19.0]:geo[G].torus((x,14,z),2.19,.06,I['steel'])
    collision_box('Tanque estoque',(x,14,16.65),(4.3,4.3,4.9))
    pipe(G,(x,11.9,15),(x,10.5,15),.2,'green')
# Heat exchanger bank and treatment skid.
for x in [12,16,20,24]:
    pipe(G,(x,-11,27),(x,-11,30.4),.42,'steel',12)
    for z in np.arange(27.2,30.3,.25):geo[G].torus((x,-11,z),.48,.035,I['steel'],n=12,m=4)
box(G,'Skid refino',(18,-11,26.25),(17,4,.5),'dark',True)
station('refino_console','Receita e regulagem do refino',(12,-15,27),'refinador','refino',['escolher_receita','regular_temperatura','balancear_fluxo'])
station('refino_inspecao','Amostra do produto acabado',(26,-14,27),'refinador','controle_qualidade',['testar_pureza','trocar_filtro','aprovar_produto'])

G='05_TUBULACOES_E_VALVULAS'
def valve(p,r=.45,axis='Y',color='red'):
    p=Vector(p);geo[G].torus(p,r,.045,I[color],axis,n=16,m=5)
    for t in np.arange(0,math.tau,math.tau/4):
        d=Vector((math.cos(t),0,math.sin(t))) if axis=='Y' else Vector((math.cos(t),math.sin(t),0));pipe(G,p,p+d*r,.04,color,6)
    pipe(G,p-Vector((0,.55,0)),p,.055,'steel',6)
for y in [-19,-17.8,-16.6]:
    for z in [16,18,21.2]:
        pipe(G,(-30,y,z),(30,y,z),.14,'steel');pipe(G,(30,y,z),(30,y,27),.14,'steel')
        for x in [-25,-5,10,25]:geo[G].torus((x,y,z),.22,.055,I['steel'],'X',12,4)
for y in [-7,2,11]:
    pipe(G,(7,y,21),(9,y,21),.19,'green');pipe(G,(9,y,21),(9,y,23.2),.19,'green');pipe(G,(9,y,23.2),(10.8,y,23.2),.19,'green')
    pipe(G,(28,y,23.2),(30,y,23.2),.13,'red');pipe(G,(30,y,23.2),(30,y,26),.13,'red');valve((29,y-.2,24.2),.42)
for i in range(5):
    x=-8+i*.65;pipe(G,(x,9,14),(x,9,26),.15,'steel');pipe(G,(x,9,26),(x,-6,26),.15,'steel')
for x in [8,12,16,20,24]:
    pipe(G,(x,-11,28),(x,-14,28),.13,'green');valve((x,-14.4,28),.34,'Y','yellow')
# Small pump motors and flange bolts provide close-up work surfaces.
for x,y,z in [(-10,-9,20),(7,-4,26),(12,-9,20),(24,-15,26)]:
    box(G,'Base bomba',(x,y,z+.16),(2.6,1.8,.3),'steel',True)
    pipe(G,(x-.7,y,z+.85),(x+.6,y,z+.85),.45,'blue',14);pipe(G,(x+.6,y,z+.85),(x+1,y,z+.85),.28,'steel',12)
    for xx in np.arange(x-.6,x+.65,.16):geo[G].torus((xx,y,z+.85),.48,.03,I['dark'],'X',12,4)
    pipe(G,(x+1,y,z+.85),(x+1,y,z+1.7),.16,'green')

log('alojamento sala de controle heliponto')
G='06_ALOJAMENTO_E_CONTROLE'
def room(name,x0,y0,x1,y1,z,h=5.7):
    # Hollow room, real front opening and furnishings. Upper deck is its roof.
    box(G,name+' fundo',((x0+x1)/2,y1,z+h/2),(x1-x0,.18,h),'white',True)
    for x in [x0,x1]:box(G,name+' lateral',(x,(y0+y1)/2,z+h/2),(.18,y1-y0,h),'white',True)
    mid=(x0+x1)/2;doorw=1.6
    for a,b in [(x0,mid-doorw/2),(mid+doorw/2,x1)]:box(G,name+' frente',((a+b)/2,y0,z+h/2),(b-a,.18,h),'white',True)
    box(G,name+' verga',(mid,y0,z+4),(doorw,.18,3.4),'white',True)
    for x in np.arange(x0+1.2,x1-1,2.5):box(G,name+' janela',(x,y0-.12,z+3.4),(1.3,.055,1),'glass')
    for x in np.arange(x0+.5,x1,.75):box(G,'Nervura fachada',(x,y0-.14,z+h/2),(.045,.08,h),'steel')
    for y in np.arange(y0+.5,y1,.75):box(G,'Nervura lateral',(x0-.14,y,z+h/2),(.06,.035,h),'steel')
room('Sala de controle',-29,-7,-13,6,20)
room('Alojamento',-29,7,-13,18,20)
room('Manutencao e filtros',-25,-5,-8,9,14)
room('Modulo de energia',-15,11,-6,18,26,h=4)
# Technical volumes and louvers on the upper deck make the silhouette closer to the reference.
room('Sala de bombas superior',-12,-7,-5,5,26,h=4.1)
for y in [0,2,4]:
    box(G,'Duto ventilacao modulo',(-12.1,y,28),(.08,1.4,1.6),'dark')
    for z in np.arange(27.3,28.8,.14):box(G,'Veneziana metalica',(-12.18,y,z),(.10,1.4,.035),'steel')
for x in [-12,-8]:
    pipe(G,(x,14,30),(x,14,35),.31,'dark',12);geo[G].torus((x,14,34.8),.35,.06,I['steel'])
for x in [-25,-21,-17]:
    box(G,'Mesa console',(x,3,20.55),(3,1.5,1.1),'dark',True);box(G,'Painel vertical',(x,3.55,21.45),(2.6,.20,1.5),'steel')
    box(G,'Tela de processo',(x,3.42,21.65),(1.25,.035,.72),'screen')
    for bx in [-.9,-.5,0,.5,.9]:box(G,'Botao console',(x+bx,3.37,21.10),(.10,.055,.10),'greenlight' if bx>0 else 'amberlight')
    box(G,'Assento operador',(x,1.3,20.55),(.75,.7,.16),'black');box(G,'Encosto operador',(x,1.58,21),(.75,.13,.9),'black');pipe(G,(x,1.3,20),(x,1.3,20.55),.08,'steel',8)
for x in [-26,-20]:
    for z in [20.5,22.0]:box(G,'Beliche',(x,13,z),(2.1,4,.24),'steel');box(G,'Colchao',(x,13,z+.20),(1.9,3.8,.25),'white')
    for yy in [11,15]:pipe(G,(x-1,yy,20),(x-1,yy,23.2),.04,'steel',6)
text('PETRO ESPERANCA',(-21,-7.2,24.65),.84)
text('CONTROLE',(-21,-7.22,22.6),.50)
station('controle_contrato','Contratos e visao geral da operacao',(-21,-3,21),'supervisor','gestao',['aceitar_contrato','designar_equipe','consultar_lotes'])
station('manutencao','Filtros, energia e reparos leves',(-16,-1,15),'tecnico','manutencao',['trocar_filtro','repor_energia','consertar_bomba'])

G='07_HELIPONTO';center=(-50,5,28.7);r=16
geo[G].tube((-50,5,28.35),center,r,I['deck'],64)
collision_box('Heliponto',(-50,5,28.52),(30,30,.36))
geo[G].torus((-50,5,28.74),13,.105,I['yellow'],n=96,m=5)
for p,s in [((-53,5,28.76),(.45,9,.035)),((-47,5,28.76),(.45,9,.035)),((-50,5,28.76),(6,.45,.035))]:box(G,'H heliponto',p,s,'label')
box(G,'Passarela heliponto',(-32.9,5,28.55),(6,3.5,.3),'steel',True)
for yy in [3.25,6.75]:rail((-36,yy),(-30,yy),28.7,group=G)
for a in np.linspace(0,math.tau,32,endpoint=False):
    x=-50+15.6*math.cos(a);y=5+15.6*math.sin(a);pipe(G,(x,y,27.6),(x,y,28.5),.045,'steel',6);box('11_SEGURANCA_E_SINALIZACAO','Baliza heliponto',(x,y,28.85),(.16,.16,.15),'greenlight')
for y in [-7,17]:
    for x in [-62,-50,-38]:beam(G,(x,y,28.35),(-29,y*.7,20),.38,'dark')
for x in [-60,-50,-40]:beam(G,(x,-8,27.8),(x,18,27.8),.35,'steel')
# Ramp with 2.7 m rise, 16 m run, giving direct access from upper deck.
g=Geo();g.face([(-30,3.5,28.7),(-14,3.5,26),(-14,6.5,26),(-30,6.5,28.7)],I['steel']);g.obj('Rampa heliponto',C[G],PALETTE)
for yy in [3.5,6.5]:pipe(G,(-30,yy,29.8),(-14,yy,27.1),.055,'yellow',8)
COL.append(dict(name='Rampa heliponto',kind='ramp',vertices=[[-30,3.5,28.7],[-14,3.5,26],[-14,6.5,26],[-30,6.5,28.7]]))
station('heliponto','Chegada por helicoptero',(-50,5,29.7),'transporte','chegada',['interagir'])

log('guindastes articulados e carga suspensa')
def empty(name,c,parent=None,p=(0,0,0)):
    o=bpy.data.objects.new(name,None);c.objects.link(o);o.empty_display_type='ARROWS';o.empty_display_size=1.5;o.parent=parent;o.location=p;return o
def crane(name,rootpos,length,angle,azimuth,c,animated=False):
    root=empty(name+' | BASE',C['13_CONTROLES_ANIMACAO'],p=rootpos);root['controle']='azimute em graus';root['limites_giro']=[-150,35]
    base=Geo();base.tube((0,0,-3),(0,0,0),1.5,I['yellow'],18);base.torus((0,0,0),1.55,.18,I['steel']);base.obj(name+' pedestal',c,PALETTE,root)
    yaw=empty(name+' | GIRO',C['13_CONTROLES_ANIMACAO'],root);yaw.rotation_euler[2]=math.radians(azimuth)
    cab=Geo();cab.box((-.7,-1,1),(4.7,3.6,2),I['orange']);cab.box((.6,-2.82,1.1),(2.3,.06,1.25),I['glass']);cab.box((-3.4,0,1.4),(2.2,3.2,2.5),I['dark']);cab.obj(name+' cabine e contrapeso',c,PALETTE,yaw)
    boom=empty(name+' | LANCA',C['13_CONTROLES_ANIMACAO'],yaw,p=(0,0,1.4));boom.rotation_euler[1]=-math.radians(angle);boom['limites_inclinacao']=[30,75]
    lattice=Geo();step=2
    for y,z in [(-.75,-.65),(.75,-.65),(-.75,.65),(.75,.65)]:lattice.beam((0,y,z),(length,y*.35,z*.35),.11,I['orange'])
    for i in range(math.ceil(length/step)):
        x0=i*step;x1=min(length,(i+1)*step);s0=1-.65*x0/length;s1=1-.65*x1/length
        for y in [-1,1]:lattice.beam((x0,y*.75*s0,-.65*s0),(x1,y*.75*s1,.65*s1),.07,I['steel'])
        for z in [-1,1]:lattice.beam((x0,-.75*s0,z*.65*s0),(x1,.75*s1,z*.65*s1),.07,I['steel'])
        for y,z in [(-.75,-.65),(.75,-.65)]:lattice.beam((x0,y*s0,z*s0),(x0,-y*s0,z*s0),.07,I['orange'])
    lattice.obj(name+' lanca trelicada',c,PALETTE,boom)
    # Separate mast cables and drums are genuine geometry, never a painted backdrop.
    stays=Geo()
    for yy in [-.85,.85]:stays.tube((-1,yy,4),(length*math.cos(math.radians(angle)),yy*.3,1.4+length*math.sin(math.radians(angle))),.027,I['black'],6)
    stays.beam((-1,0,0),(-1,0,4),.16,I['dark']);stays.obj(name+' tirantes',c,PALETTE,yaw)
    tip=Vector((length*math.cos(math.radians(angle)),0,1.4+length*math.sin(math.radians(angle))))
    hook=empty(name+' | GANCHO',C['13_CONTROLES_ANIMACAO'],yaw,p=(tip.x,0,-(rootpos[2]-22.25)))
    hook['controle']='altura local do gancho';hook['limites_altura_m']=[4.2,32]
    hg=Geo();hg.box((0,0,0),(.75,.50,1),I['yellow']);hg.torus((0,0,-.6),.32,.09,I['steel'],'Y',18,6);hg.obj(name+' bloco e gancho',c,PALETTE,hook)
    # Cable mesh extends from tip; scale is driven by hook height, keeping attachment.
    cable=Geo();cable.tube((0,0,0),(0,0,-1),.045,I['black'],8);co=cable.obj(name+' cabo vertical',c,PALETTE,yaw);co.location=tip
    fc=co.driver_add('scale',2);dr=fc.driver;dr.type='SCRIPTED';v=dr.variables.new();v.name='gancho';v.type='TRANSFORMS';v.targets[0].id=hook;v.targets[0].transform_type='LOC_Z';v.targets[0].transform_space='LOCAL_SPACE';dr.expression=f'{tip.z:.8f}-gancho'
    if animated:
        basez=-(rootpos[2]-22.25)
        for frame,dz,aa in [(1,0,azimuth),(36,8.5,azimuth),(80,8.5,azimuth-35),(120,0,azimuth-35),(156,8.5,azimuth-35),(180,8.5,azimuth),(216,0,azimuth)]:
            hook.location.z=basez+dz;hook.keyframe_insert('location',frame=frame);yaw.rotation_euler[2]=math.radians(aa);yaw.keyframe_insert('rotation_euler',frame=frame)
    return root,yaw,boom,hook
root,yaw,boom,hook=crane('Guindaste principal',(-22,4,28.7),32,50,-90,C['08_GUINDASTE_PRINCIPAL'],True)
crane('Guindaste apoio',(26,-3,28.7),21,48,70,C['09_GUINDASTE_APOIO'])
station('guindaste','3. Icar e carregar os pallets',(-26,-4,27),'guindasteiro','extracao_3',['girar_lanca','subir_descer_gancho','engatar_sling','estabilizar_carga','soltar_carga'])
station('envase','Envasar, lacrar e etiquetar barris',(-14,-17,21),'operador','envase',['posicionar_barril','encher','lacrar','montar_pallet'])

# Barrel and pallet libraries are separate reusable mesh assets, with origin at base.
def barrel(name,p,parent=None,mat='barril',fill='bruto'):
    g=Geo();g.tube((0,0,.035),(0,0,.88),.29,I[mat],20);g.torus((0,0,.07),.293,.021,I['steel']);g.torus((0,0,.82),.293,.022,I['steel'])
    for z in [.26,.60]:g.torus((0,0,z),.295,.018,I[mat])
    g.tube((.10,.08,.88),(.10,.08,.91),.045,I['steel'],10);g.box((0,-.294,.50),(.24,.015,.26),I['label']);o=g.obj(name,C['10_CARGA_BARRIS_E_EMBARQUE'],PALETTE,parent);o.location=p;o['item']='barril_'+fill;o['capacidade_unidades_jogo']=25;o.asset_mark();return o
def pallet(name,p,parent=None):
    g=Geo()
    for y in [-.45,0,.45]:g.box((0,y,.08),(1.4,.16,.16),I['wood'])
    for x in [-.55,-.28,0,.28,.55]:g.box((x,0,.19),(.22,1.15,.08),I['wood'])
    o=g.obj(name,C['10_CARGA_BARRIS_E_EMBARQUE'],PALETTE,parent);o.location=p;o.asset_mark();return o
cargo=empty('CARGA | pallet articulado',C['13_CONTROLES_ANIMACAO'],hook,p=(0,0,-2.1));cargo['massa_virtual_kg']=240;cargo['balanceio_max_graus']=8
pallet('Pallet suspenso',(0,0,0),cargo)
for x in [-.33,.33]:
    for y in [-.31,.31]:barrel('Barril suspenso',(x,y,.23),cargo)
sl=Geo()
for x in [-.64,.64]:
    for y in [-.5,.5]:sl.tube((x,y,.22),(0,0,1.65),.025,I['black'],6)
sl.obj('Sling de quatro pontos',C['10_CARGA_BARRIS_E_EMBARQUE'],PALETTE,cargo)
for frame,angle in [(1,0),(36,4),(60,-3),(80,2),(120,0),(156,-3),(180,2),(216,0)]:cargo.rotation_euler[1]=math.radians(angle);cargo.keyframe_insert('rotation_euler',frame=frame)
for x in [-18,-15,-12]:
    pallet('Pallet aguardando embarque',(x,-20,20.04))
    for xx in [-.33,.33]:
        for yy in [-.31,.31]:barrel('Barril de lote',(x+xx,-20+yy,20.27))
for x in [7,8,9,10]:barrel('Barril refinado',(x,-18,26.04),mat='green',fill='refinado')
box('10_CARGA_BARRIS_E_EMBARQUE','Recepcao do guindaste',(-33.4,-12.8,20.01),(2.3,3.3,.02),'yellow')
station('carga_conferencia','Conferir lacres e manifesto',(-14,-19,21),'logistica','transporte_1',['verificar_lote','prender_carga','emitir_manifesto'])
station('expedicao','Despachar embarcacao e destino',(23,-20,21),'logistica','transporte_2',['selecionar_destino','confirmar_transferencia'])

# Simple cargo transfer cradle below the crane; boat gameplay is an external system.
box('10_CARGA_BARRIS_E_EMBARQUE','Area de transferencia',(0,-21,19.99),(10,5,.025),'yellow')
text('CARGA / ZONA DE ICAMENTO',(-12,-24.08,19.0),.64)

log('flare balizas e equipamentos de seguranca')
G='11_SEGURANCA_E_SINALIZACAO'
# Flare boom points away from playable decks; decorative flame geometry is kept separate.
for y in [9,11]:beam(G,(29,y,26),(60,y,38),.20,'dark')
for i in range(12):
    x=29+i*31/12;z=26+i
    beam(G,(x,9,z),(x+31/12,11,z+1),.12,'steel');beam(G,(x,11,z),(x+31/12,9,z+1),.12,'steel')
pipe(G,(29,10,26.4),(60,10,38.4),.14,'red');pipe(G,(60,10,38.4),(60,10,42),.16,'dark')
fire=material('Chama decorativa',(1,.28,.015),0,.4);bs=fire.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=(1,.21,.012,1);bs.inputs['Emission Strength'].default_value=4
fg=Geo();fg.tube((60,10,42),(61.1,10,43.5),.20,0,7,r2=.52);fg.tube((61.1,10,43.5),(62.6,10.2,44.2),.52,0,7,r2=.04);fg.obj('Chama flare decorativa',C[G],[fire])
for x,y,z in [(-31,-15,20),(31,-16,20),(4,-6,26),(-28,9,20)]:
    pipe(G,(x,y,z+.12),(x,y,z+.93),.16,'red',12);box(G,'Extintor suporte',(x,y+.13,z+.53),(.45,.2,1.1),'yellow');pipe(G,(x,y,z+.93),(x,y,z+1.06),.055,'black',8)
for x,y in [(-31,-20),(31,-20),(-31,20),(31,20)]:
    pipe(G,(x,y,20),(x,y,22.7),.065,'steel',8);box(G,'Luminaria',(x,y,22.7),(.32,.28,.18),'amberlight')
for x in [-28,-19]:
    # Enclosed survival capsules mounted outboard.
    pipe(G,(x,-25,14.8),(x+6,-25,14.8),.90,'orange',18);geo[G].tube((x-1,-25,14.8),(x,-25,14.8),.1,I['orange'],18,r2=.9);geo[G].tube((x+6,-25,14.8),(x+7,-25,14.8),.9,I['orange'],18,r2=.1)
    for xx in [x+1,x+3,x+5]:box(G,'Janela bote',(xx,-25.84,15.1),(.65,.045,.42),'glass')
    beam(G,(x,-23,16.5),(x,-25,16.5),.15,'steel');beam(G,(x+6,-23,16.5),(x+6,-25,16.5),.15,'steel')
# Dense, accessible pipe racks, services and instrument cabinets.
for y in [16.8,18.0]:
    for z in [27.6,28.25,28.9]:
        pipe('05_TUBULACOES_E_VALVULAS',(-3,y,z),(27,y,z),.13,'steel')
        for x in [0,6,12,18,24]:geo['05_TUBULACOES_E_VALVULAS'].torus((x,y,z),.20,.045,I['dark'],'X',12,4)
for x in [0,6,12,18,24]:
    for yy in [16,18.7]:beam('05_TUBULACOES_E_VALVULAS',(x,yy,26),(x,yy,29.6),.14,'dark')
    beam('05_TUBULACOES_E_VALVULAS',(x,16,29.6),(x,18.7,29.6),.16,'steel')
for x,y in [(-2,-13),(3,-13),(8,12),(28,-13),(-28,12)]:
    box('04_TRATAMENTO_E_REFINO','Gabinete de instrumentos',(x,y,27.2),(1.4,1.2,2.4),'white',True)
    for xx in [-.3,.3]:box(G,'Tela de instrumentos',(x+xx,y-.62,27.7),(.38,.04,.34),'screen')
    for xx in [-.3,0,.3]:box(G,'Seletor',(x+xx,y-.64,27.1),(.10,.05,.10),'amberlight')
for x,y,h in [(6,8,6),(10,8,6),(8,13,5),(-2,15,5)]:
    pipe('04_TRATAMENTO_E_REFINO',(x,y,26),(x,y,26+h),.66,'steel',14)
    for z in [26.3,26+h-.3]:geo['04_TRATAMENTO_E_REFINO'].torus((x,y,z),.71,.055,I['yellow'])
    pipe('05_TUBULACOES_E_VALVULAS',(x,y,26+h),(x,15,26+h),.12,'green')
for label,p in [('EXTRACAO',(0,-3.05,28.1)),('TRATAMENTO DE LOTE',(19,-8.7,23.3)),('REFINO MODULAR',(18,-13.1,27.0)),('ENVASE',(-14,-18.2,22.1)),('ACESSO RESTRITO',(30,-19.0,21.1))]:text(label,p,.45)

for group,g in geo.items():
    if g.f:
        o=g.obj(group+' | geometria',C[group],PALETTE);o['escala_metros']=True
        if group not in ['12_COLISAO_PREPARADA','13_CONTROLES_ANIMACAO','14_PONTOS_INTERACAO','15_APRESENTACAO']:C[group].asset_mark()

# Closed collision volumes are reference assets, independently switchable.
for idx,row in enumerate(COL):
    g=Geo()
    if row['kind']=='box':g.box(row['center'],row['size'],0)
    else:
        v=[Vector(a) for a in row['vertices']]
        g.v=[tuple(a) for a in v]+[tuple(a-Vector((0,0,.16))) for a in v]
        g.f=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
        g.mid=[0]*6
    o=g.obj('COL_'+f'{idx:03}_'+row['name'],C['12_COLISAO_PREPARADA'],[M['dark']]);o.display_type='WIRE';o.hide_render=True;o['native_export_pending']=True
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.rigidbody.object_add();o.rigid_body.type='PASSIVE';o.rigid_body.collision_shape='MESH';o.rigid_body.use_margin=True;o.rigid_body.collision_margin=.003;o.rigid_body.friction=.8
C['12_COLISAO_PREPARADA'].hide_render=True;C['12_COLISAO_PREPARADA'].hide_viewport=True;C['14_PONTOS_INTERACAO'].hide_render=True

log('apresentacao e arquivos')
ocean=material('Oceano | ondas de apresentacao',(.008,.045,.082),.25,.26)
nt=ocean.node_tree;bs=nt.nodes.get('Principled BSDF');geoN=nt.nodes.new('ShaderNodeNewGeometry');noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=.7;noise.inputs['Detail'].default_value=4;nt.links.new(geoN.outputs['Position'],noise.inputs['Vector']);bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.65;bump.inputs['Distance'].default_value=.32;nt.links.new(noise.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
og=Geo();og.box((0,0,-.5),(6000,6000,.8),0);og.obj('Mar | somente apresentacao',C['15_APRESENTACAO'],[ocean])
world=bpy.data.worlds.new('Ceu maritimo');world.use_nodes=True;scene.world=world;n=world.node_tree.nodes;l=world.node_tree.links;sky=n.new('ShaderNodeTexSky');sky.sky_type='MULTIPLE_SCATTERING';sky.sun_elevation=math.radians(32);sky.sun_rotation=math.radians(135);sky.sun_disc=False;l.new(sky.outputs['Color'],n.get('Background').inputs['Color']);n.get('Background').inputs['Strength'].default_value=.24
sun=bpy.data.lights.new('Sol maritimo','SUN');sun.energy=2.8;sun.angle=.055;obj=bpy.data.objects.new('Sol maritimo',sun);C['15_APRESENTACAO'].objects.link(obj);obj.rotation_euler=(math.radians(32),math.radians(-28),math.radians(-36))
def camera(name,p,target,lens=50,ortho=None):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);C['15_APRESENTACAO'].objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=12000;d.clip_start=.1
    if ortho:d.type='ORTHO';d.ortho_scale=ortho
    return o
cameras=[('01_Plataforma_geral',camera('Vista referencia',(-135,-180,83),(0,0,28),55)),('02_Processo_e_carga',camera('Vista producao',(-73,-90,47),(-8,-5,23),50)),('03_Refino_e_tubulacoes',camera('Vista refino',(65,-74,60),(17,1,29),53)),('04_Implantacao',camera('Planta mecanicas',(0,0,220),(0,0,0),ortho=150))]
scene.camera=cameras[0][1];scene.frame_set(1);scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.render.threads_mode='FIXED';scene.render.threads=6;scene.cycles.samples=20;scene.cycles.use_denoising=True;scene.render.resolution_x=1440;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene['estado']='modelo Blender pronto; recursos FiveM ainda nao exportados ou instalados';scene['mecanicas']='3 extracao + refino + transporte cooperativo';scene['colisao']='volumes passivos Blender, separados, ainda precisam de YBN';scene['refino']='modulo de jogo simplificado com receitas abstratas';scene['original_referencia']=str(REF)
# Set editable viewport to the same framing.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
if (ROOT/'texturas/01_chapa_branca.png').exists():
    # Apply the supplied images when reconstructing this authored asset.
    (ROOT/'dados/colisoes.json').write_text(json.dumps(COL,ensure_ascii=False,indent=2),encoding='utf8')
    sys.path.insert(0,str(ROOT/'scripts'))
    from texturizar_plataforma import apply_textures
    apply_textures()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'plataforma_petroleo.blend'),compress=True)
(ROOT/'dados/interacoes.json').write_text(json.dumps(dict(coordinate_system='local Blender, metres, Z up; transform on installation',stations=STATIONS),ensure_ascii=False,indent=2),encoding='utf8')
(ROOT/'dados/colisoes.json').write_text(json.dumps(COL,ensure_ascii=False,indent=2),encoding='utf8')
(ROOT/'dados/escadas.json').write_text(json.dumps(STAIRS,indent=2),encoding='utf8')
stats=dict(objects=len(bpy.data.objects),mesh_objects=sum(o.type=='MESH' for o in bpy.data.objects),vertices=sum(len(o.data.vertices) for o in bpy.data.objects if o.type=='MESH'),polygons=sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),collision_volumes=len(COL),interaction_points=len(STATIONS),animated_controls=['Guindaste principal | GIRO','Guindaste principal | GANCHO','CARGA | pallet articulado'],source_sha256=hashlib.sha256(REF.read_bytes()).hexdigest() if REF.exists() else None,in_game_verified=False,installed=False)
(ROOT/'dados/modelo.json').write_text(json.dumps(stats,indent=2),encoding='utf8')
if '--sem-render' not in sys.argv:
    for file,cam in cameras[:3]:
        scene.camera=cam;scene.render.filepath=str(ROOT/'previews'/(file+'.png'));bpy.ops.render.render(write_still=True);log('RENDER',file)
    scene.camera=cameras[0][1]
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'plataforma_petroleo.blend'),compress=True)
log('MODELO_CONCLUIDO',stats)
