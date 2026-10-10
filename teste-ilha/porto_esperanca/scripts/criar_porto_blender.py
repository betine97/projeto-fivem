"""Porto Esperanca: terreno, reservas e vegetacao autoral. Executar no Blender."""
import bpy, math, json, random, argparse, sys, time
from pathlib import Path
from mathutils import Vector
import numpy as np

P = Path(__file__).resolve().parents[1]
SEED = 20261009
rng = random.Random(SEED)
args = argparse.ArgumentParser()
args.add_argument('--somente-render', action='store_true')
args.add_argument('--camera', default='')
argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OPT = args.parse_args(argv)

def log(*s): print('PORTO:', *s, flush=True)

def col(name, scene=None):
    c = bpy.data.collections.new(name)
    (scene or bpy.context.scene).collection.children.link(c)
    return c

def basic(name, color, rough=.85):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1)
    b.inputs['Roughness'].default_value=rough
    return m

def noise_material(name, low, high, scale, rough=.85, bump=.1):
    m=basic(name,low,rough);n=m.node_tree.nodes;l=m.node_tree.links;b=n.get('Principled BSDF')
    g=n.new('ShaderNodeNewGeometry');t=n.new('ShaderNodeTexNoise');t.inputs['Scale'].default_value=scale
    t.inputs['Detail'].default_value=3;l.new(g.outputs['Position'],t.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*low,1)
    ramp.color_ramp.elements[1].color=(*high,1);l.new(t.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],b.inputs['Base Color'])
    bn=n.new('ShaderNodeBump');bn.inputs['Strength'].default_value=.35;bn.inputs['Distance'].default_value=bump
    l.new(t.outputs['Fac'],bn.inputs['Height']);l.new(bn.outputs[0],b.inputs['Normal'])
    return m

class Geo:
    def __init__(self): self.v=[];self.f=[];self.mi=[]
    def face(self, points, mat):
        k=len(self.v);self.v.extend([tuple(p) for p in points]);self.f.append(tuple(range(k,k+len(points))));self.mi.append(mat)
    def tube(self, pts, radii, mat=0, sides=7):
        start=len(self.v)
        for i,p in enumerate(pts):
            p=Vector(p);d=Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(0,i-1)])
            d.normalize();u=d.cross(Vector((0,1,0)))
            if u.length<.01:u=d.cross(Vector((1,0,0)))
            u.normalize();w=d.cross(u)
            for j in range(sides):self.v.append(tuple(p+radii[i]*(math.cos(j*math.tau/sides)*u+math.sin(j*math.tau/sides)*w)))
        for i in range(len(pts)-1):
            for j in range(sides):
                self.f.append((start+i*sides+j,start+i*sides+(j+1)%sides,start+(i+1)*sides+(j+1)%sides,start+(i+1)*sides+j));self.mi.append(mat)
        self.f.append(tuple(start+j for j in reversed(range(sides))));self.mi.append(mat)
        self.f.append(tuple(start+(len(pts)-1)*sides+j for j in range(sides)));self.mi.append(mat)
    def leaf(self, center, direction, length, width, mat):
        c=Vector(center);d=Vector(direction).normalized();u=d.cross(Vector((0,0,1)))
        if u.length<.01:u=Vector((1,0,0))
        u.normalize();z=d.cross(u)
        a=c-d*length*.48;b=c+d*length*.52;mid=c+z*width*.16
        self.face([a,c-u*width*.5,mid],mat);self.face([a,mid,c+u*width*.5],mat)
        self.face([b,mid,c-u*width*.5],mat);self.face([b,c+u*width*.5,mid],mat)
    def obj(self,name,collection,mats):
        me=bpy.data.meshes.new(name);me.from_pydata(self.v,[],self.f);me.update()
        for m in mats:me.materials.append(m)
        me.polygons.foreach_set('material_index',self.mi)
        for f in me.polygons:f.use_smooth=True
        o=bpy.data.objects.new(name,me);collection.objects.link(o);return o

def mesh(name,v,f,c,m):
    g=Geo();g.v=v;g.f=f;g.mi=[0]*len(f);return g.obj(name,c,[m])

def cube(name,center,size,c,m):
    x,y,z=center;dx,dy,dz=[t/2 for t in size]
    v=[(x+a*dx,y+b*dy,z+d*dz) for a,b,d in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    return mesh(name,v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],c,m)

def text_obj(body,loc,c,size=3,mat=None,rot=(0,0,0)):
    d=bpy.data.curves.new(body,'FONT');d.body=body;d.size=size;d.align_x='CENTER'
    o=bpy.data.objects.new(body,d);c.objects.link(o);o.location=loc;o.rotation_euler=rot
    if mat:d.materials.append(mat)
    return o

SPECS=[
 ('01_coqueiro','Palmeira de Coco','palm',14,3.6,'coqueiro'),
 ('02_imperial','Palmeira Imperial','palm',13,3.0,'imperial'),
 ('03_caneleira','Árvore de Sombra / Caneleira','broad',13,6.2,'shade'),
 ('04_amendoeira','Amendoeira','broad',9,4.7,'tier'),
 ('05_flamboyant','Flamboyant','broad',9,6.4,'red'),
 ('06_arvore_rua','Árvore de Rua','broad',8,3.6,'round'),
 ('07_reseda','Resedá','broad',6,3.3,'pink'),
 ('08_ipe_amarelo','Ipê Amarelo','broad',9,4.1,'yellow'),
 ('09_oliveira','Oliveira','broad',7,4.0,'silver'),
 ('10_castanhola','Castanhola / Amendoeira da Praia','broad',7,5.1,'beach'),
 ('11_mangueira','Mangueira / Manga','broad',10,4.6,'mango'),
 ('12_bananeira','Bananeira','banana',5,3.0,'banana'),
 ('13_mangue','Mangue','broad',7,4.1,'mangrove'),
 ('14_arbusto_costeiro','Arbusto Costeiro','broad',2.5,2.5,'bush'),
 ('15_palmeira_ana','Palmeira Anã','fan',3.4,2.4,'dwarf'),
 ('16_palma_azul','Palma Azul / Palmeira Azul','fan',7,3.0,'blue'),
 ('17_yucca','Yucca','yucca',4,2.0,'yucca'),
 ('18_cerca_viva','Cerca Viva','broad',1.8,2.1,'hedge'),
 ('19_oiti','Oiti','broad',11,4.5,'oiti'),
 ('20_figueira','Figueira','broad',10,5.7,'fig'),
 ('21_areca','Palmeira Areca','palm',7,2.7,'areca'),
 ('22_palmeira_leque','Palmeira Leque','fan',7,3.0,'fan'),
 ('23_jasmim_manga','Jasmim-Manga','broad',5.5,3.3,'plumeria'),
 ('24_vegetacao_baixa','Vegetação Baixa Tropical','ground',1.2,1.8,'ground')]

def frond(g,root,angle,L,width,mat,fan=False):
    root=Vector(root);d=Vector((math.cos(angle),math.sin(angle),0));side=Vector((-d.y,d.x,0))
    if fan:
        elev=math.radians(-32+92*(.5+.5*math.sin(angle*3.1)))
        outward=d*math.cos(elev)+Vector((0,0,math.sin(elev)))
        tip=root+outward*L*.47
        g.tube([root,tip],[.035,.012],0,5)
        for j in range(25):
            a=(j/24-.5)*2.55;ray=outward*math.cos(a)+side*math.sin(a)
            u=outward.cross(side).normalized()
            edge=side*math.cos(a)-outward*math.sin(a)
            for k in range(5):
                t0=k/5;t1=(k+1)/5;c0=tip+ray*L*.66*t0;c1=tip+ray*L*.66*t1
                w0=.062*math.sin(math.pi*t0);w1=.062*math.sin(math.pi*t1)
                ridge=u*.027*math.sin(math.pi*(t0+t1)/2)
                g.face([c0-edge*w0,c1-edge*w1,c1+ridge,c0+ridge],mat)
                g.face([c0+ridge,c1+ridge,c1+edge*w1,c0+edge*w0],mat)
        return
    pts=[]
    for j in range(13):
        t=j/12;pts.append(root+d*(L*t)+Vector((0,0,L*(.46*math.sin(math.pi*t)-.28*t))))
    g.tube(pts,[.043*(1-j/14) for j in range(13)],mat,5)
    for j in range(1,29):
        t=j/30;base=root+d*L*t+Vector((0,0,L*(.46*math.sin(math.pi*t)-.28*t)))
        leaflen=width*math.sin(math.pi*t)**.65
        for s in [-1,1]:
            end=base+side*s*leaflen+d*leaflen*.25+Vector((0,0,-leaflen*.23))
            g.leaf((base+end)/2,end-base,(end-base).length,.085 if L>3 else .065,mat)

def plant(spec,library,mats):
    key,label,kind,h,r,style=spec;pr=random.Random(SEED+sum(ord(x) for x in key));g=Geo()
    if kind in ['palm','fan']:
        stems=5 if style=='areca' else (3 if style=='dwarf' else 1)
        for stem in range(stems):
            ang=stem*2.399;ox=math.cos(ang)*.38 if stems>1 else 0;oy=math.sin(ang)*.38 if stems>1 else 0
            H=h*pr.uniform(.8,1.0);bend=.75 if style=='coqueiro' else .15
            points=[(ox+bend*(j/9)**2,oy,H*j/9) for j in range(10)]
            rad=.17 if stems>1 else (.28 if style=='imperial' else .23)
            g.tube(points,[rad*(1-.28*j/9) for j in range(10)],0,10)
            if stems==1:
                for j in range(2,int(H*3)):
                    z=j/3;g.tube([(ox+bend*(z/H)**2,oy,z),(ox+bend*(z/H)**2,oy,z+.028)],[rad*(1-.28*z/H)*1.03]*2,1,10)
            root=Vector(points[-1]);count=24 if kind=='fan' else 16
            for j in range(count):
                frond(g,root+Vector((0,0,pr.uniform(-.22,.25))),j*math.tau/count+pr.uniform(-.15,.15),r*pr.uniform(.85,1.16),r*.42,8 if style=='blue' else pr.choice([2,3,4]),kind=='fan')
            if style=='coqueiro':
                for j in range(7):
                    a=j*2.399;center=root+Vector((.35*math.cos(a),.35*math.sin(a),-.32))
                    for q in range(6):
                        b=q*math.tau/6;g.face([center+Vector((0,0,.18)),center+Vector((.15*math.cos(b),.15*math.sin(b),0)),center+Vector((.15*math.cos(b+.9),.15*math.sin(b+.9),0))],9)
    elif kind=='banana':
        for k in range(5):
            a=k*2.399;x=math.cos(a)*.48;y=math.sin(a)*.48;H=h*pr.uniform(.5,1)
            g.tube([(x,y,0),(x,y,H*.65),(x+.15,y,H)],[.15,.12,.045],3,8)
            for j in range(7):
                ang=j*2.399+k;base=Vector((x,y,H));d=Vector((math.cos(ang),math.sin(ang),0));u=Vector((-d.y,d.x,0));L=r*pr.uniform(.7,1.1)
                for t in range(9):
                    t0=t/9;t1=(t+1)/9
                    c0=base+d*L*t0+Vector((0,0,L*(.35*math.sin(math.pi*t0)-.23*t0)))
                    c1=base+d*L*t1+Vector((0,0,L*(.35*math.sin(math.pi*t1)-.23*t1)))
                    w0=.42*math.sin(math.pi*t0);w1=.42*math.sin(math.pi*t1)
                    for s in [-1,1]:g.face([c0,c0+u*s*w0,c1+u*s*w1,c1],pr.choice([2,3,4]))
    elif kind=='yucca':
        for k in range(4):
            a=k*2.399;H=h*pr.uniform(.45,1);base=(.4*math.cos(a),.4*math.sin(a),H)
            g.tube([(base[0],base[1],0),base],[.13,.09],0,8)
            for j in range(40):
                ang=j*2.399;d=(math.cos(ang),math.sin(ang),pr.uniform(-.5,1.2));g.leaf(Vector(base)+Vector(d)*.55,d,1.1,.10,pr.choice([2,3,4]))
    elif kind=='ground':
        for k in range(9):
            a=k*2.399;center=Vector((r*.65*math.cos(a),r*.65*math.sin(a),.35))
            for j in range(6):
                ang=j*2.399+k;d=Vector((math.cos(ang),math.sin(ang),pr.uniform(.3,1.0)))
                g.leaf(center+d*.35,d,.9,.33,pr.choice([2,3,4]))
    else:
        isb=style in ['bush','hedge'];trunkh=h*.43;rad=h*.034 if not isb else .06
        g.tube([(0,0,0),(.08,.02,trunkh*.55),(0,0,trunkh)],[rad*1.25,rad*.8,rad*.54],0,10)
        if style=='mangrove':
            for j in range(12):
                a=j*math.tau/12;rr=pr.uniform(1.1,2.2)
                g.tube([(0,0,2),(.5*math.cos(a),.5*math.sin(a),1.1),(rr*math.cos(a),rr*math.sin(a),0)],[.13,.095,.04],0,6)
        elif not isb:
            for j in range(6):
                a=j*math.tau/6;g.tube([(0,0,.55),(rad*2*math.cos(a),rad*2*math.sin(a),.12),(rad*4*math.cos(a),rad*4*math.sin(a),0)],[rad*.45,rad*.4,.04],0,6)
        centers=[];n=12 if not isb else 7
        for i in range(n):
            a=i*2.399;ring=.35 if i<3 else (.62 if i<7 else .87)
            zz=h*(.84 if i<3 else (.72 if i<7 else .60))
            if style=='tier':zz=h*(.52+.30*(i%3)/2)
            c=Vector((math.cos(a)*r*ring,math.sin(a)*r*ring,zz+pr.uniform(-.25,.25)))
            base=Vector((0,0,trunkh*pr.uniform(.6,1)))
            mid=(c+base)*.5+Vector((0,0,.4))
            g.tube([base,mid,c],[rad*.48,rad*.23,.025],0,6)
            centers.append(c)
            for j in range(3):
                end=c+Vector((pr.uniform(-1,1)*r*.22,pr.uniform(-1,1)*r*.22,pr.uniform(-.1,.6)))
                g.tube([c,end],[.04,.012],0,5)
        leafmat=[2,3,4] if style!='silver' else [8,10]
        leafN=850 if not isb else 480
        for c in centers:
            for j in range(leafN):
                az=pr.uniform(0,math.tau);cosv=pr.uniform(-1,1);rv=pr.random()**.33
                rx=r*(.42 if style in ['shade','red','fig','beach'] else .35)
                offset=Vector((math.cos(az)*math.sqrt(1-cosv*cosv)*rx*rv,math.sin(az)*math.sqrt(1-cosv*cosv)*rx*rv,cosv*h*.15*rv))
                L=.52 if style not in ['beach','plumeria','mango'] else .72
                if style=='silver':L=.36
                g.leaf(c+offset,(pr.uniform(-1,1),pr.uniform(-1,1),pr.uniform(-.35,.6)),L*pr.uniform(.8,1.2),L*(.23 if style=='silver' else .5),pr.choice(leafmat))
                if style in ['red','pink','yellow','plumeria'] and j%7==0:
                    fm={'red':5,'pink':6,'yellow':7,'plumeria':11}[style]
                    center=c+offset+Vector((0,0,.1))
                    for petal in range(4):
                        a=petal*math.pi/2;g.leaf(center+Vector((.10*math.cos(a),.10*math.sin(a),0)),(math.cos(a),math.sin(a),.2),.19,.12,fm)
                if style=='mango' and j%90==0:
                    g.leaf(c+offset,(0,0,-1),.22,.16,9)
    o=g.obj(key,library,mats);o['nome_referencia']=label;o['tipo']=kind;o['estilo']=style
    o['origem']='Modelagem procedural autoral com geometria 3D, orientada pelas pranchas aprovadas'
    o['altura_referencia_m']=h;o['colisao_futura']='tronco simplificado; folhagem sem colisao'
    return o

def shore(x):return -40+75*np.exp(-(np.asarray(x)/210)**2)+15*np.sin(np.asarray(x)/93)
def riverx(y):return -285+32*np.sin((np.asarray(y)+50)/125)

LOTS=[];ROUTES=[]

def route(name,points,width,kind='asfalto'):
    ROUTES.append(dict(name=name,points=points,width=width,kind=kind))

def dist_route(x,y,r):
    x=np.asarray(x);y=np.asarray(y);best=np.full(np.broadcast(x,y).shape,1e8)
    for a,b in zip(r['points'][:-1],r['points'][1:]):
        vx=b[0]-a[0];vy=b[1]-a[1];t=np.clip(((x-a[0])*vx+(y-a[1])*vy)/(vx*vx+vy*vy),0,1)
        best=np.minimum(best,np.sqrt((x-a[0]-t*vx)**2+(y-a[1]-t*vy)**2))
    return best

def setup_plan():
    LOTS.extend([
        dict(id='P01',use='Terminal futuro',center=[-10,65],size=[55,32],level=4.4),
        dict(id='P02',use='Praca de chegada',center=[-8,112],size=[90,55],level=5.0),
        dict(id='P03',use='Pesca e apoio naval',center=[-160,40],size=[75,55],level=4.0),
        dict(id='P04',use='Patio e armazens futuros',center=[280,55],size=[125,88],level=4.6),
        dict(id='P05',use='Alfandega futura',center=[195,124],size=[46,36],level=5.2),
        dict(id='P06',use='Oficina futura',center=[382,237],size=[55,46],level=7.0),
        dict(id='P07',use='Posto de combustivel futuro',center=[380,302],size=[58,50],level=8.0)])
    uses=['Mercado','Padaria','Farmacia','Posto de saude','Escritorio de fretes','Contratos','Comercio','Residencial']
    j=0
    for y in [228,302,392]:
        for x in [-160,-108,0,52,160,215]:
            j+=1;LOTS.append(dict(id=f'U{j:02}',use=uses[(j-1)%len(uses)]+' futuro',center=[x,y],size=[34,43],level=6.2+(y-228)*.026))
    route('Avenida costeira',[[-470,130],[-350,158],[-255,172],[-165,174],[0,174],[220,174],[430,165]],12)
    route('Rua oeste',[[-65,174],[-65,470]],10)
    route('Rua central',[[105,174],[105,470]],10)
    route('Rua comercial',[[ -190,264],[265,264]],10)
    route('Rua residencial',[[-190,350],[265,350]],9)
    route('Rua alta',[[-190,438],[265,438]],9)
    route('Acesso de cargas',[[320,55],[355,125],[350,174]],12)
    route('Ligacao ao interior',[[105,438],[125,490],[210,530],[280,575],[245,655],[170,720]],11)
    route('Trilha do rio',[[-390,210],[-400,315],[-365,430],[-380,510]],3.5,'terra')
    route('Passeio orla',[[-200,3],[-140,0],[-65,35],[0,39],[90,14],[145,-10]],3.4,'passeio')
    for s in LOTS:s['level']=4.6+max(s['center'][1]-120,0)*.035

def height(x,y):
    x=np.asarray(x);y=np.asarray(y);d=y-shore(x)
    z=np.where(d<0,np.maximum(-20,d*.18),2+np.maximum(d,0)*.027)
    z+=25*np.exp(-((x+405)/105)**2-((y-440)/180)**2)
    z+=80*np.exp(-((x+175)/180)**2-((y-655)/190)**2)
    z+=95*np.exp(-((x-385)/140)**2-((y-670)/160)**2)
    z+=42*np.exp(-((x-35)/100)**2-((y-520)/130)**2)
    z+=np.maximum(d,0)/np.maximum(d+90,1)*(1.0*np.sin(x/33)*np.sin(y/47)+.4*np.sin(x/11+y/19))
    # Grade the urban district as a connected gentle slope before preparing lots.
    dx=np.maximum(np.maximum(-215-x,x-425),0);dy=np.maximum(np.maximum(125-y,y-475),0)
    urban=np.clip(1-np.hypot(dx,dy)/180,0,1);urban=urban*urban*(3-2*urban)
    target=4.6+np.maximum(y-120,0)*.035;z=z*(1-urban)+target*urban
    for r in ROUTES:
        if r['kind']=='passeio':continue
        dd=dist_route(x,y,r);w=np.clip(1-dd/(r['width']/2+8),0,1)
        if 'interior' not in r['name'] and r['kind']=='asfalto':
            target=4.6+np.maximum(y-120,0)*.035;z=z*(1-w)+target*w
    for s in LOTS:
        cx,cy=s['center'];sx,sy=s['size'];dx=np.maximum(np.abs(x-cx)-sx/2,0);dy=np.maximum(np.abs(y-cy)-sy/2,0)
        dd=np.sqrt(dx*dx+dy*dy);w=np.clip(1-dd/7,0,1);z=z*(1-w)+s['level']*w
    rr=np.abs(x-riverx(y));half=10+8*np.exp(-((y-55)/150)**2)
    w=np.clip(1-rr/(half+10),0,1);water=np.maximum(0,(y-185)*.035)
    z=z*(1-w)+(water-2.2)*w
    return z

def clear_of_sites(x,y,margin=0):
    for s in LOTS:
        if abs(x-s['center'][0])<s['size'][0]/2+margin and abs(y-s['center'][1])<s['size'][1]/2+margin:return False
    for r in ROUTES:
        if float(dist_route(x,y,r))<r['width']/2+margin:return False
    return True

def camera(name,pos,target,c,ortho=None,lens=46):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);c.objects.link(o);o.location=pos
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=15000;d.clip_start=.2
    if ortho:d.type='ORTHO';d.ortho_scale=ortho
    return o

def lighting(scene,c):
    w=bpy.data.worlds.new('Ceu tropical '+scene.name);w.use_nodes=True;n=w.node_tree.nodes;l=w.node_tree.links
    sky=n.new('ShaderNodeTexSky');sky.sky_type='MULTIPLE_SCATTERING';sky.sun_elevation=math.radians(40);sky.sun_rotation=math.radians(135);sky.sun_disc=False
    n.get('Background').inputs['Strength'].default_value=.10;l.new(sky.outputs[0],n.get('Background').inputs[0]);scene.world=w
    d=bpy.data.lights.new('Sol','SUN');d.energy=2.6;d.angle=.08;o=bpy.data.objects.new('Sol',d);c.objects.link(o);o.rotation_euler=(.48,-.44,-.6)
    scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
    try:
        p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
        for dev in p.devices:dev.use=dev.type=='OPTIX'
        if any(dev.use for dev in p.devices):scene.cycles.device='GPU';log('GPU',[(d.name,d.type) for d in p.devices if d.use])
    except Exception as exc:log('GPU indisponivel',str(exc))
    scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'

def render_outputs():
    scene=bpy.data.scenes['Porto Esperanca'];bpy.context.window.scene=scene
    for name,file in [('VISTA_GERAL','porto_vegetacao.png'),('VISTA_PRACA','praca_reservada.png'),('VISTA_NATUREZA','foz_vegetacao.png'),('PLANTA','implantacao_areas.png')]:
        if OPT.camera and OPT.camera!=name:continue
        scene.camera=bpy.data.objects[name]
        markers=bpy.data.collections['05_RESERVAS_E_IDENTIFICACAO'];markers.hide_render=(name!='PLANTA')
        scene.render.filepath=str(P/'previews'/file);log('RENDER',file)
        bpy.ops.render.render(write_still=True)
    bpy.data.collections['05_RESERVAS_E_IDENTIFICACAO'].hide_render=True
    if not OPT.camera:
        for sn,fn in [('Catalogo 01','catalogo_01.png'),('Catalogo 02','catalogo_02.png')]:
            s=bpy.data.scenes[sn];bpy.context.window.scene=s;s.render.filepath=str(P/'previews'/fn)
            log('RENDER',fn);bpy.ops.render.render(write_still=True)
    bpy.context.window.scene=scene;scene.camera=bpy.data.objects['VISTA_GERAL']

if OPT.somente_render:
    bpy.ops.wm.open_mainfile(filepath=str(P/'porto_esperanca.blend'));render_outputs();log('RENDER_CONCLUIDO');sys.exit(0)

bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.name='Porto Esperanca';scene.unit_settings.system='METRIC'
C={n:col(n) for n in ['01_TERRENO','02_AGUA_VISUAL','03_CIRCULACAO','04_VEGETACAO','05_RESERVAS_E_IDENTIFICACAO','06_PEDRAS','07_COLISAO_REFERENCIA','08_CAMERAS_LUZES','09_BIBLIOTECA_VEGETACAO']}
setup_plan()
bark=noise_material('Casca tropical',(.12,.075,.035),(.35,.24,.12),3,bump=.055)
ringmat=basic('Aneis das palmeiras',(.24,.18,.10))
mats=[bark,ringmat,basic('Folha verde escura',(.045,.105,.018)),basic('Folha verde media',(.10,.20,.028)),basic('Folha nova',(.22,.32,.055)),basic('Flor flamboyant',(.72,.065,.016)),basic('Flor reseda',(.68,.15,.33)),basic('Flor ipe',(.90,.58,.025)),basic('Folha prata azul',(.24,.36,.30)),basic('Fruto',(.35,.29,.045)),basic('Folha oliveira',(.30,.37,.23)),basic('Flor jasmim',(.85,.83,.64))]
for m in mats[2:]:
    b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Subsurface Weight'].default_value=.055;b.inputs['Roughness'].default_value=.72
prototypes={};cat=[]
for spec in SPECS:
    o=plant(spec,C['09_BIBLIOTECA_VEGETACAO'],mats);prototypes[spec[0]]=o
    bpy.data.libraries.write(str(P/'modelos'/(spec[0]+'.blend')),{o},fake_user=True,compress=True)
    cat.append(dict(id=spec[0],nome=spec[1],categoria=spec[2],altura_referencia_m=spec[3],raio_referencia_m=spec[4],vertices=len(o.data.vertices),poligonos=len(o.data.polygons),arquivo='modelos/'+spec[0]+'.blend'))
    log('MODELO',spec[0],len(o.data.polygons))
C['09_BIBLIOTECA_VEGETACAO'].hide_render=True;C['09_BIBLIOTECA_VEGETACAO'].hide_viewport=True

# Grids share identical heights at sector edges.
terrainmat=basic('Solo | areia terra grama rocha',(.22,.29,.08))
nt=terrainmat.node_tree;n=nt.nodes;l=nt.links;b=n.get('Principled BSDF')
a=n.new('ShaderNodeVertexColor');a.layer_name='Bioma';noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2.8;noise.inputs['Detail'].default_value=3
geo=n.new('ShaderNodeNewGeometry');l.new(geo.outputs['Position'],noise.inputs['Vector'])
mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.20;l.new(a.outputs[0],mix.inputs[1]);l.new(noise.outputs['Fac'],mix.inputs[2]);l.new(mix.outputs[0],b.inputs['Base Color'])
bum=n.new('ShaderNodeBump');bum.inputs['Strength'].default_value=.28;bum.inputs['Distance'].default_value=.065;l.new(noise.outputs['Fac'],bum.inputs['Height']);l.new(bum.outputs[0],b.inputs['Normal'])
xs=np.linspace(-520,520,261);ys=np.linspace(-235,795,259);X,Y=np.meshgrid(xs,ys);Z=height(X,Y)
gy,gx=np.gradient(Z,ys[1]-ys[0],xs[1]-xs[0]);slope=np.sqrt(gx*gx+gy*gy)
landnoise=.5+.5*np.sin(X/21)*np.sin(Y/27)
colors=np.zeros((*X.shape,4));colors[:,:,3]=1
grass=np.array([.095,.145,.025]);dirt=np.array([.24,.17,.085]);sand=np.array([.52,.40,.23]);rockcol=np.array([.25,.23,.19])
colors[:,:,:3]=grass[None,None,:]*(.82+.18*landnoise[:,:,None])
beach=np.clip(1-(Y-shore(X))/23,0,1);colors[:,:,:3]=colors[:,:,:3]*(1-beach[:,:,None])+sand*beach[:,:,None]
rockw=np.clip((slope-.85)/.65,0,1);colors[:,:,:3]=colors[:,:,:3]*(1-rockw[:,:,None])+rockcol*rockw[:,:,None]
for s in LOTS:
    mask=(np.abs(X-s['center'][0])<s['size'][0]/2+2)&(np.abs(Y-s['center'][1])<s['size'][1]/2+2);colors[mask,:3]=dirt
for r in ROUTES:
    if r['kind']=='terra':colors[dist_route(X,Y,r)<r['width']/2+1,:3]=dirt
for iy in range(4):
    for ix in range(4):
        x0=ix*65;x1=(ix+1)*65;y0=iy*64;y1=258 if iy==3 else (iy+1)*64
        xx=X[y0:y1+1,x0:x1+1];yy=Y[y0:y1+1,x0:x1+1];zz=Z[y0:y1+1,x0:x1+1];ny,nx=xx.shape
        v=np.stack([xx,yy,zz],-1).reshape(-1,3).tolist();faces=[]
        for j in range(ny-1):
            for i in range(nx-1):k=j*nx+i;faces.extend([(k,k+1,k+nx+1),(k,k+nx+1,k+nx)])
        o=mesh(f'PE_TERRENO_{iy}_{ix}',v,faces,C['01_TERRENO'],terrainmat)
        ca=o.data.color_attributes.new(name='Bioma',type='FLOAT_COLOR',domain='POINT');ca.data.foreach_set('color',colors[y0:y1+1,x0:x1+1].astype(np.float32).ravel())
        o['setor']=[ix,iy];o['colisao']='Malha de referencia separada; exportacao FiveM posterior'
        cp=bpy.data.objects.new('COL_'+o.name,o.data);C['07_COLISAO_REFERENCIA'].objects.link(cp);cp.display_type='WIRE'
C['07_COLISAO_REFERENCIA'].hide_render=True;C['07_COLISAO_REFERENCIA'].hide_viewport=True
log('TERRENO_CONCLUIDO')

water=noise_material('Oceano | agua de apresentacao',(.018,.11,.16),(.025,.25,.27),.65,.22,.13)
bs=water.node_tree.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=.25;bs.inputs['IOR'].default_value=1.333
mesh('MAR_VISUAL', [(-4500,-4500,0),(4500,-4500,0),(4500,4500,0),(-4500,4500,0)],[(0,1,2,3)],C['02_AGUA_VISUAL'],water)
rv=[];rf=[]
for j,y in enumerate(np.linspace(-90,650,149)):
    x=float(riverx(y));w=9+5*math.exp(-((y-55)/150)**2);z=max(0,(y-185)*.035)+.035;rv.extend([(x-w,y,z),(x+w,y,z)])
    if j:rf.append((2*j-2,2*j-1,2*j+1,2*j))
mesh('RIO_VISUAL',rv,rf,C['02_AGUA_VISUAL'],water)

roadmat=noise_material('Asfalto',(.075,.078,.071),(.13,.14,.13),6,bump=.018)
sidewalk=basic('Passeio claro',(.49,.43,.32));linemat=basic('Sinalizacao provisoria',(.85,.74,.42))
def ribbon(name,r,w,mat):
    pts=[]
    for a,b in zip(r['points'][:-1],r['points'][1:]):
        count=max(2,int(math.dist(a,b)/3));pts.extend([((1-t)*a[0]+t*b[0],(1-t)*a[1]+t*b[1]) for t in np.linspace(0,1,count,endpoint=False)])
    pts.append(tuple(r['points'][-1]));v=[];f=[]
    for i,p in enumerate(pts):
        a=pts[max(0,i-1)];b=pts[min(len(pts)-1,i+1)];d=Vector((b[0]-a[0],b[1]-a[1]));d.normalize();n=Vector((-d.y,d.x))
        for s in [-1,1]:
            x=p[0]+n.x*w*.5*s;y=p[1]+n.y*w*.5*s;lift=.16 if mat==roadmat else .10;z=float(height(x,y))+lift
            # Single traversable bridge reference surface above the river.
            if r['name']=='Avenida costeira' and abs(x-float(riverx(y)))<33:z=6.0+lift
            v.append((x,y,z))
        if i:f.append((2*i-2,2*i-1,2*i+1,2*i))
    return mesh(name,v,f,C['03_CIRCULACAO'],mat)
for r in ROUTES:
    if r['kind']=='asfalto':ribbon(r['name']+' | calcada',r,r['width']+4,sidewalk);ribbon(r['name'],r,r['width'],roadmat)
    elif r['kind']=='passeio':ribbon(r['name'],r,r['width'],sidewalk)
    r['bridge_reference']=r['name']=='Avenida costeira'

zoneMats=[basic('Reserva urbana',(.62,.46,.25)),basic('Reserva porto',(.20,.42,.50)),basic('Reserva praca',(.33,.52,.24))]
for s in LOTS:
    x,y=s['center'];sx,sy=s['size'];kind=2 if 'Praca' in s['use'] else (1 if s['id'].startswith('P') else 0)
    o=cube('RESERVA_'+s['id']+'_'+s['use'],(x,y,s['level']+.15),(sx,sy,.18),C['05_RESERVAS_E_IDENTIFICACAO'],zoneMats[kind]);o['uso_futuro']=s['use'];o['id_lote']=s['id'];o['nao_edificado']=True
    text_obj(s['id'],(x,y,s['level']+.3),C['05_RESERVAS_E_IDENTIFICACAO'],7,linemat)
C['05_RESERVAS_E_IDENTIFICACAO'].hide_render=True

placed=[];occupied=[];counts={k:0 for k in prototypes}
def instance(key,x,y,z,scale=1,angle=None,category='vegetacao'):
    src=prototypes[key];o=bpy.data.objects.new(key+'_inst',src.data);C['04_VEGETACAO'].objects.link(o)
    o.location=(x,y,z);o.scale=(scale,scale,scale);o.rotation_euler[2]=rng.uniform(0,math.tau) if angle is None else angle
    o['modelo']=key;o['vinculado']=True;counts[key]+=1
    placed.append(dict(modelo=key,x=x,y=y,z=z,escala=scale,categoria=category));return o

treeKeys=[s[0] for s in SPECS if s[2] in ['broad','palm','fan','banana','yucca'] and s[5] not in ['bush','hedge']]
for attempt in range(48000):
    if len(occupied)>=2300:break
    x=rng.uniform(-490,490);y=rng.uniform(-15,755);z=float(height(x,y))
    if z<2.2 or y<float(shore(x))+8 or not clear_of_sites(x,y,8):continue
    if abs(x-float(riverx(y)))<22:continue
    grad=math.hypot(float(height(x+2,y)-height(x-2,y))/4,float(height(x,y+2)-height(x,y-2))/4)
    if grad>.9:continue
    clustered=.5+.5*math.sin(x/55)*math.sin(y/43)
    if rng.random()> .40+.42*clustered:continue
    if any((x-a)**2+(y-b)**2<(rr+2.5)**2 for a,b,rr in occupied):continue
    coastal=y<float(shore(x))+80
    if coastal:key=rng.choice(['01_coqueiro','01_coqueiro','02_imperial','10_castanhola','22_palmeira_leque','14_arbusto_costeiro'])
    elif y<460:key=rng.choice(treeKeys)
    else:key=rng.choice(['03_caneleira','04_amendoeira','11_mangueira','19_oiti','20_figueira','03_caneleira','06_arvore_rua'])
    sc=rng.uniform(.72,1.2);instance(key,x,y,z-.035,sc);occupied.append((x,y,3.0*sc))

# Deliberate shade at plaza boundary, maintaining roots outside all building pads.
for x,y,key in [(-68,95,'03_caneleira'),(55,99,'03_caneleira'),(-68,131,'05_flamboyant'),(55,133,'08_ipe_amarelo'),(-67,59,'01_coqueiro'),(53,55,'02_imperial')]:
    if clear_of_sites(x,y,2):instance(key,x,y,float(height(x,y))-.025,.9)
for j in range(95):
    y=rng.uniform(5,545);side=rng.choice([-1,1]);x=float(riverx(y))+side*rng.uniform(18,35);z=float(height(x,y))
    if z>.8 and clear_of_sites(x,y,4):instance('13_mangue',x,y,z-.03,rng.uniform(.65,1.0))
for attempt in range(18000):
    if sum(counts[k] for k in ['14_arbusto_costeiro','18_cerca_viva','24_vegetacao_baixa'])>1750:break
    x=rng.uniform(-500,500);y=rng.uniform(-30,760);z=float(height(x,y))
    if z<1.0 or not clear_of_sites(x,y,2.4) or abs(x-float(riverx(y)))<18:continue
    key=rng.choice(['14_arbusto_costeiro','18_cerca_viva','24_vegetacao_baixa','24_vegetacao_baixa'])
    if rng.random()>.5+.3*math.sin(x/35)*math.sin(y/45):continue
    instance(key,x,y,z-.02,rng.uniform(.45,.9),category='sub_bosque')

grassmat=basic('Capim verde seco',(.24,.31,.055));gm=Geo()
for j in range(24):
    a=rng.uniform(0,math.tau);rad=rng.uniform(0,.65);x=math.cos(a)*rad;y=math.sin(a)*rad;h=rng.uniform(.18,.55);ang=rng.uniform(0,math.tau)
    gm.face([(x-.028,y,0),(x+.028,y,0),(x+.12*math.cos(ang),y+.12*math.sin(ang),h)],0)
grass=gm.obj('Tufos_de_grama',C['09_BIBLIOTECA_VEGETACAO'],[grassmat]);grasscount=0
for _ in range(12000):
    if grasscount>=4200:break
    x=rng.uniform(-500,500);y=rng.uniform(-20,765);z=float(height(x,y))
    if z<2 or not clear_of_sites(x,y,1.5) or abs(x-float(riverx(y)))<17:continue
    o=bpy.data.objects.new('CAPIM',grass.data);C['04_VEGETACAO'].objects.link(o);o.location=(x,y,z-.015);sc=rng.uniform(.7,1.6);o.scale=(sc,sc,sc);o.rotation_euler[2]=rng.uniform(0,math.tau);grasscount+=1
    placed.append(dict(modelo='capim',x=x,y=y,z=z-.015,escala=sc,categoria='rasteira'))
log('VEGETACAO_CONCLUIDA',sum(counts.values()),grasscount)

rockmat=noise_material('Rocha costeira',(.16,.15,.12),(.43,.40,.31),2.4,bump=.09)
rockprotos=[]
for k in range(7):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1)
    o=bpy.context.object;o.name='ROCHA_MODELO_'+str(k)
    for cc in list(o.users_collection):cc.objects.unlink(o)
    C['09_BIBLIOTECA_VEGETACAO'].objects.link(o)
    for v in o.data.vertices:
        v.co*=rng.uniform(.79,1.15);v.co.x*=1.15;v.co.y*=.88;v.co.z*=.72
    o.data.materials.append(rockmat)
    for f in o.data.polygons:f.use_smooth=True
    rockprotos.append(o)
rocks=[]
for j in range(13000):
    if len(rocks)>=430:break
    x=rng.uniform(-505,505);y=rng.uniform(-60,765);z=float(height(x,y))
    coastdist=y-float(shore(x));sl=math.hypot(float(height(x+2,y)-height(x-2,y))/4,float(height(x,y+2)-height(x,y-2))/4)
    if z<-.7 or not clear_of_sites(x,y,6):continue
    if coastdist>45 and sl<.3 and rng.random()>.12:continue
    if abs(x-float(riverx(y)))<14:continue
    size=rng.uniform(.6,3.0) if coastdist<40 else rng.uniform(1,4.5)
    src=rng.choice(rockprotos);o=bpy.data.objects.new('ROCHA',src.data);C['06_PEDRAS'].objects.link(o);o.location=(x,y,z+size*.24);o.scale=(size,size*rng.uniform(.7,1.3),size);o.rotation_euler=(rng.uniform(-.2,.2),rng.uniform(-.2,.2),rng.uniform(0,math.tau))
    rocks.append(dict(x=x,y=y,z=o.location.z,raio=size))

camc=C['08_CAMERAS_LUZES'];lighting(scene,camc)
camera('VISTA_GERAL',(770,-940,630),(0,230,30),camc,lens=43)
camera('VISTA_PRACA',(-45,-120,70),(0,170,7),camc,lens=40)
camera('VISTA_NATUREZA',(-465,-120,160),(-255,245,16),camc,lens=43)
camera('PLANTA',(0,255,1500),(0,255,0),camc,ortho=1100)
scene.camera=bpy.data.objects['VISTA_GERAL'];scene['fase']='Terreno e vegetacao; edificios e estruturas portuarias reservados'
scene['origem_coordenadas']='Local de projeto; implantacao na ilha atual ainda nao realizada'
scene['referencias']='referencias/01_porto_aprovado.png e pranchas 02/03'
scene['exportacao_fivem']=False;scene['agua']='Superficies visuais Blender, sem configuracao de agua nativa'
for a in bpy.context.screen.areas if bpy.context.screen else []:
    if a.type=='VIEW_3D':a.spaces.active.clip_end=15000;a.spaces.active.region_3d.view_location=(0,230,25);a.spaces.active.region_3d.view_distance=1000

# Two catalogue scenes expose every model separately without hiding the library instances.
catalogbackground=basic('Fundo catalogo',(.065,.085,.10));labelmat=basic('Rotulo catalogo',(.80,.85,.82))
for page in range(2):
    s=bpy.data.scenes.new(f'Catalogo {page+1:02}');s.unit_settings.system='METRIC';cc=col('CATALOGO_'+str(page+1),s)
    for i,spec in enumerate(SPECS[page*12:(page+1)*12]):
        key,label,kind,h,r,sty=spec;x=(i%4-1.5)*18;z=(2-i//4)*19
        src=prototypes[key];o=bpy.data.objects.new('CAT_'+key,src.data);cc.objects.link(o);o.location=(x,0,z+1.8)
        sc=min(1,13/(h+r*.3));o.scale=(sc,sc,sc)
        cube('Base_'+key,(x,0,z+1.35),(13,8,.15),cc,sidewalk)
        title=label.replace(' / ','\n');text_obj(title,(x,-5,z-.15),cc,.68,labelmat,(math.pi/2,0,0))
    cube('Fundo',(0,8,29),(80,.1,64),cc,catalogbackground)
    camera(f'CAT_CAM_{page}',(0,-125,45),(0,0,28),cc,ortho=76)
    s.camera=bpy.data.objects[f'CAT_CAM_{page}'];lighting(s,cc);s.render.resolution_x=1800;s.render.resolution_y=1450;s.cycles.samples=24
    s.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.32

# Record actual placement exclusions and model provenance rather than declaring FiveM physics.
violations=[]
for p in placed:
    if not clear_of_sites(p['x'],p['y'],0):violations.append(p)
for p in rocks:
    if not clear_of_sites(p['x'],p['y'],0):violations.append(p)
report=dict(revisao='porto-20261009-terreno-vegetacao-1',seed=SEED,unidade='metros',terreno_extensao_m=[1040,1030],terreno_setores=16,
    modelos=cat,contagens_vegetacao=counts,tufos_grama=grasscount,pedras=len(rocks),lotes=LOTS,rotas=ROUTES,
    edificios_gerados=0,agua_apenas_visual=True,colisao_blender_referencia=True,instalado_fivem=False,
    exclusoes_validas=len(violations)==0,violacoes=violations,
    observacao='Modelos autorais procedurais, nao extracao 3D das imagens; catalogos com repeticoes consolidadas. Requer LOD e conversao para arquivos nativos antes do FiveM.')
(P/'dados'/'implantacao.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
(P/'dados'/'vegetacao_posicoes.json').write_text(json.dumps(placed,ensure_ascii=False,indent=2),encoding='utf8')
(P/'dados'/'pedras_posicoes.json').write_text(json.dumps(rocks,indent=2),encoding='utf8')
if violations:raise RuntimeError('Vegetacao ou pedras ocupam reservas/rotas')
bpy.context.window.scene=scene;scene.camera=bpy.data.objects['VISTA_GERAL']
bpy.ops.wm.save_as_mainfile(filepath=str(P/'porto_esperanca.blend'),compress=True)
log('BLEND_SALVO',len(cat),sum(counts.values()),grasscount,len(rocks))
render_outputs();log('PORTO_CONCLUIDO')
