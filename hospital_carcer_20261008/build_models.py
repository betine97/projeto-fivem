import bpy,bmesh,sys,json,math
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parent;R=P.parent;T=P/'textures';O=P/'stream'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz']
import numpy as np,addon_utils
bpy.ops.wm.read_factory_settings(use_empty=True);addon_utils.enable('Sollumz',default_set=True)
from Sollumz.sollumz_properties import SollumType
from Sollumz.tools.drawablehelper import convert_obj_to_model
from Sollumz.tools.meshhelper import mesh_add_missing_uv_maps,mesh_add_missing_color_attrs
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.iecontext import ExportContext,ExportSettings,export_context_scope
from Sollumz.ydr.ydrexport import export_ydr
from szio.gta5 import AssetTarget,AssetFormat,AssetVersion
spec=json.loads((P/'spec.json').read_text());spec['rooms']=[];spec['doors']=[];spec['lights']=[];styles={};groups={n:[] for n in spec['models']};collisions={n:[] for n in spec['models']};active=spec['models'][0]
col=bpy.data.collections.new(spec['collection']);bpy.context.scene.collection.children.link(col)
for key in list(spec['colors'])+['signs']:
    preset='emissive.sps' if key=='led' else 'glass.sps' if key=='glass' else 'normal_spec.sps';m=create_shader(preset);m.name='hospital_'+key
    for sampler,name in [('DiffuseSampler','hc_'+key),('BumpSampler','hc_normal'),('SpecSampler','hc_specmetal' if key in ['metal','gold'] else 'hc_spec')]:
        node=m.node_tree.nodes.get(sampler)
        if node:
            im=bpy.data.images.load(str(T/(name+'.dds')),check_existing=True);im.pack();node.image=im;node.texture_properties.embedded=True
            if sampler!='DiffuseSampler':im.colorspace_settings.name='Non-Color'
            m.node_tree.links.new(m.node_tree.nodes['UVMap 0'].outputs['UV'],node.inputs['Vector'])
    for name,val in [('wetnessMultiplier',0),('specularIntensityMult',.25 if key in ['gold','metal'] else .06),('specularFalloffMult',75),('bumpiness',.12),('emissiveMultiplier',1.5)]:
        node=m.node_tree.nodes.get(name)
        if node:node.set(0,val)
    styles[key]=m
def mesh(name,verts,faces,key,solid=False,smooth=False):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.materials.append(styles[key]);uv=me.uv_layers.new(name='UVMap 0')
    for p in me.polygons:
        axes=[i for i in range(3) if i!=int(np.argmax(abs(np.array(p.normal))))]
        for li in p.loop_indices:
            v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v[axes[0]]*.5,v[axes[1]]*.5)
            if key=='__unused__':
                u=-.2138*v.x-4.6396 if abs(p.normal.y)>.5 else -.2138*3.645-4.6396+.2138*(v.y-9.816895)
                uv.data[li].uv=(u,-.25018*v.z-1.05572)
        p.use_smooth=smooth
    mesh_add_missing_uv_maps(me);mesh_add_missing_color_attrs(me)
    for a in me.color_attributes:a.data.foreach_set('color_srgb',np.tile(np.array([1,1,1,1],np.float32),len(a.data)))
    obj=bpy.data.objects.new(name,me);col.objects.link(obj);groups[active].append(obj)
    if solid:
        me.calc_loop_triangles();collisions[active].append({'name':name,'vertices':[list(v.co) for v in me.vertices],'triangles':[list(t.vertices) for t in me.loop_triangles],'material':'GLASS_SHOOT_THROUGH' if key=='glass' else 'CONCRETE' if key not in ['wood','metal','gold','dark'] else 'WOOD_SOLID_MEDIUM' if key=='wood' else 'METAL_SOLID_MEDIUM'})
    return obj
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def box(name,lo,hi,key='stone',solid=False,bevel=.0):
    x,y,z=lo;X,Y,Z=hi;obj=mesh(name,[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)],faces,key,solid)
    if bevel:
        mod=obj.modifiers.new('Chanfro real','BEVEL');mod.width=bevel;mod.segments=2;bpy.context.view_layer.objects.active=obj;obj.select_set(True);bpy.ops.object.modifier_apply(modifier=mod.name);obj.select_set(False)
    return obj
def slab_wedge(name,x0,x1,y0,y1,z00,z10,z01,z11,key,solid=True,depth=.18):
    top=[(x0,y0,z00),(x1,y0,z10),(x1,y1,z11),(x0,y1,z01)];return mesh(name,[(x,y,z-depth) for x,y,z in top]+top,faces,key,solid)

def cyl(name,pos,r,h,key='metal',solid=False,n=16):
    x,y,z=pos;v=[(x+r*math.cos(i*2*math.pi/n),y+r*math.sin(i*2*math.pi/n),z+dz) for dz in [0,h] for i in range(n)];f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)];return mesh(name,v,f,key,solid,True)

def beam(name,a,b,r,key='metal',n=8):
    a=Vector(a);b=Vector(b);obj=cyl(name,(0,0,0),r,(b-a).length,key,n=n);tx=Matrix.Translation(a)@(b-a).to_track_quat('Z','Y').to_matrix().to_4x4();obj.data.transform(tx);return obj

def sign(label,x,y,z,w=2.4,h=.65):
    i=spec['labels'].index(label);row,col=divmod(i,4);box('Placa '+label,(x-w/2-.025,y-.025,z-h/2-.025),(x+w/2+.025,y+.015,z+h/2+.025),'teal');o=mesh('Texto '+label,[(x-w/2,y-.027,z-h/2),(x+w/2,y-.027,z-h/2),(x+w/2,y-.027,z+h/2),(x-w/2,y-.027,z+h/2)],[(0,1,2,3)],'signs');uv=o.data.uv_layers[0];coords=[(col/4,1-(row+1)/8),((col+1)/4,1-(row+1)/8),((col+1)/4,1-row/8),(col/4,1-row/8)]
    for p in o.data.polygons:
        for j,li in enumerate(p.loop_indices):uv.data[li].uv=coords[j]

def door(x,y,z,heading=0,entry=False,label=None):
    model=spec['models'][7 if entry else 6];w=2.4 if entry else 1.4;h=3.0 if entry else 2.65
    spec['doors'].append(dict(id=len(spec['doors'])+1,model=model,pos=[x,y,z],heading=heading,width=w,height=h,travel=w+.05,entry=entry))
    if heading==0:
        for a,b in [(x-.10,x),(x+w,x+w+.10)]:box('Batente clinico',(a,y-.13,z),(b,y+.13,z+h),'metal',True)
        box('Trilho porta',(x-.1,y-.13,z+h),(x+w+.12,y+.13,z+h+.12),'teal',True)
        if label:sign(label,x+w/2,y-.17,z+h+.42)

def room_wall(x0,x1,y,z,label,front=True):
    cx=(x0+x1)/2;start=cx-.7;box('Parede '+label+' esquerda',(x0,y-.1,z),(start,y+.1,z+4.12),'white',True);box('Parede '+label+' direita',(start+1.4,y-.1,z),(x1,y+.1,z+4.12),'white',True);box('Verga '+label,(start,y-.1,z+2.77),(start+1.4,y+.1,z+4.12),'white',True);door(start,y,z,label=label)
    if front: # Ground and upper rooms on the south side also need a north-facing label.
        sign(label,cx,y+.18,z+3.12).rotation_euler if False else None

# A triangulated plaza blends the new entrance level into the actual street edges.
for i,t in enumerate(json.loads((P/'plaza.json').read_text())['triangles']):
    t=np.array(t);mesh('Praca inclinada %02d'%i,np.concatenate([t-np.array([0,0,.2]),t]),[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],'tile',True)
box('Fundacao hospital',(-33,-22,-.28),(33,22,0),'tile',True)

# Outer walls have actual window openings; decorative panels are separate geometry.
for level,z in enumerate([0,4.4]):
    active=spec['models'][level+1]
    if level==1:
        # Stair opening remains empty, including its collision.
        for lo,hi in [((-33,-22,z-.22),(27.8,22,z)),((31.2,-22,z-.22),(33,22,z)),((27.8,-22,z-.22),(31.2,-21.45,z)),((27.8,-13.8,z-.22),(31.2,22,z))]:box('Laje superior',lo,hi,'tile',True)
    box('Teto pavimento',(-33,-22,z+4.12),(33,22,z+4.4),'white',True)
    if level==0:
        # Upper slab already forms the ceiling; do not close the stair void twice.
        o=groups[active].pop();bpy.data.objects.remove(o,do_unlink=True);collisions[active].pop()
    # Side and rear windows, set between real solid piers and parapets.
    for y in [-22,22]:
        for x in np.arange(-33,33,3.3):
            if level==0 and y==-22 and (abs(x+1.65)<3 or abs(x+1.65+23.1)<3):continue
            box('Peitoril',(x,y-.16,z),(x+3.3,y+.16,z+1.0),'stone',True);box('Verga fachada',(x,y-.16,z+3.55),(x+3.3,y+.16,z+4.15),'stone',True);box('Pilar janela',(x,y-.16,z+1),(x+.24,y+.16,z+3.55),'stone',True);box('Vidro janela',(x+.24,y-.015,z+1),(x+3.3,y+.015,z+3.55),'glass',True)
            for xx in [x+.24,x+1.72,x+3.25]:box('Caixilho bronze',(xx,y-.055,z+1),(xx+.04,y+.055,z+3.55),'gold')
    for x in [-33,33]:
        for y in np.arange(-22,22,4):
            box('Peitoril lateral',(x-.16,y,z),(x+.16,y+4,z+1),'stone',True);box('Verga lateral',(x-.16,y,z+3.55),(x+.16,y+4,z+4.15),'stone',True);box('Pilar lateral',(x-.16,y,z+1),(x+.16,y+.28,z+3.55),'stone',True);box('Vidro lateral',(x-.018,y+.28,z+1),(x+.018,y+4,z+3.55),'glass',True)
            for yy in [y+.28,y+2,y+3.94]:box('Caixilho lateral',(x-.045,yy,z+1),(x+.045,yy+.045,z+3.55),'gold')
    # Central north-south spine and broad east-west corridor, connected to the lobby.
    edges=[-33,-25.5,-18,-10.5,-3,3,10.5,18,25.5,33]
    labels0=['TRIAGEM','CONSULTORIO 01','CONSULTORIO 02','ULTRASSONOGRAFIA','RADIOLOGIA','TOMOGRAFIA','LABORATORIO','FARMACIA','OBITOS','SANITARIOS','ADMINISTRACAO','ENFERMARIA','EXAMES','CONSULTORIO 01','CONSULTORIO 02','CONVERSAS MEDICAS']
    labels1=['CIRURGIA 01','CIRURGIA 02','ESTERILIZACAO','RECUPERACAO','UTI','RECUPERACAO','REUNIAO MEDICA','CONVERSAS MEDICAS','DESCANSO','VESTIARIO','SANITARIOS','ENFERMARIA','ENFERMARIA','UTI','ADMINISTRACAO','EQUIPE MEDICA']
    labs=labels0 if level==0 else labels1;idx=0
    for north in [False,True]:
        for side in [0,1]:
            xs=edges[:5] if side==0 else edges[5:]
            for k in range(4):
                x0,x1=xs[k:k+2];y0,y1=(2,22) if north else (-13,-2);label=labs[idx];idx+=1
                room_wall(x0,x1,2 if north else -2,z,label,not north)
                # Each room has its own partition, safely joined to the outer shell.
                if k:
                    box('Divisoria '+label,(x0-.1,y0,z),(x0+.1,y1,z+4.12),'white',True)
                if k==3 and side==0:box('Parede corredor',(x1-.1,y0,z),(x1+.1,y1,z+4.12),'white',True)
                if k==0 and side==1:box('Parede corredor',(x0-.1,y0,z),(x0+.1,y1,z+4.12),'white',True)
                if not north:box('Parede lobby',(x0,-13.1,z),(x1,-12.9,z+4.12),'white',True)
                spec['rooms'].append(dict(label=label,level=level,bounds=[x0+.2,y0+.2,x1-.2,y1-.2],z=z,door=[(x0+x1)/2,2 if north else -2,z],center=[(x0+x1)/2,(y0+y1)/2,z]))
                for yy in ([y0+3,y0+9,y0+15] if north else [y0+3,y0+8]):
                    xx=(x0+x1)/2;box('Painel LED',(xx-.32,yy-.8,z+4.07),(xx+.32,yy+.8,z+4.10),'led');spec['lights'].append(dict(model=active,pos=[xx,yy,z+3.65],color=[246,249,247],intensity=2.2,range=7.2))
    for y in [-19,-15,-10,-5,0,5,10,15,20]:
        box('Painel corredor',(-.30,y-.6,z+4.02),(.30,y+.6,z+4.08),'led');spec['lights'].append(dict(model=active,pos=[0,y,z+3.65],color=[247,248,242],intensity=1.8,range=7))
    for x in [-29,-21,-13,13,21,29]:spec['lights'].append(dict(model=active,pos=[x,0,z+3.65],color=[247,248,242],intensity=1.8,range=7))
    for x in [-24,-12,12,24]:
        box('Luminaria lobby',(x-.6,-17.6,z+4.03),(x+.6,-16.4,z+4.09),'led');spec['lights'].append(dict(model=active,pos=[x,-17,z+3.65],color=[244,246,240],intensity=2.5,range=8))
    # Continuous baseboards and guard rails make the sterile circulation legible.
    for y in [-1.88,1.88]:
        box('Faixa corredor',(-33,y,z+.08),(-3,y+.045,z+.16),'teal');box('Faixa corredor',(3,y,z+.08),(33,y+.045,z+.16),'teal')

active=spec['models'][0]
# Real front entrance portals: two pairs of sliding glass doors, no solid window here.
for cx in [0,-23.1]:
    for x0,x1 in [(cx-3.30,cx-2.4),(cx+2.4,cx+3.30)]:box('Entrada ombreira',(x0,-22.18,0),(x1,-21.82,4.12),'stone',True)
    box('Entrada verga',(cx-2.4,-22.18,3.14),(cx+2.4,-21.82,4.12),'stone',True)
    door(cx-2.4,-22,0,entry=True);door(cx,-22,0,entry=True);spec['doors'][-2]['direction']=-1;spec['doors'][-1]['direction']=1
    box('Entrada bandeira',(cx-2.4,-22.02,3),(cx+2.4,-21.98,3.14),'glass',True)
# Stairway: 26 comfortable risers, full collision and a clear hole in the upper slab.
for i in range(26):
    y=-21.4+i*.28;z=(i+1)*4.4/26;box('Escada degrau %02d'%i,(28,y,z-.19),(31,y+.28,z),'tile',True)
for x in [27.9,31.1]:
    for i in range(0,27,3):
        y=-21.4+i*.28;z=i*4.4/26;beam('Montante escada',(x,y,z),(x,y,z+1.03),.026)
    beam('Corrimao escada',(x,-21.4,.97),(x,-14.12,5.37),.034,'gold')
box('Patamar escada',(27.8,-14.12,4.18),(31.2,-12.9,4.4),'tile',True)
# Horizontal Art Deco cornices, pale teal fins and stepped crown.
for z in [.18,4.4,8.8]:
    box('Cornija frontal',(-33.5,-22.65,z),(33.5,-21.9,z+.20),'stone');box('Faixa teal frontal',(-33.4,-22.67,z+.035),(33.4,-22.65,z+.09),'teal')
    for x in [-33.5,33.0]:box('Cornija lateral',(x,-22,z),(x+.5,22.4,z+.2),'stone')
for x in [-33,-26.4,-19.8,-13.2,-6.6,6.6,13.2,19.8,26.4,33]:
    box('Pilastre fachada',(x-.32,-22.55,0),(x+.32,-22.15,9.05),'stone');box('Filete verde agua',(x-.11,-22.565,.45),(x+.11,-22.55,8.82),'teal')
box('Torre central corpo',(-6,-22.15,8.8),(6,-18.6,15.1),'stone',True)
for x,h in [(-6.3,14.8),(-4.8,16),(-3.4,16.8),(-1.9,17.5),(1.9,17.5),(3.4,16.8),(4.8,16),(6.3,14.8)]:
    box('Coroamento escalonado',(x-.28,-22.55,8.9),(x+.28,-20,h),'stone');box('Filete torre',(x-.055,-22.59,9),(x+.055,-22.56,h-.3),'teal')
box('Cruz vertical',(-.32,-22.59,11.4),(.32,-22.43,14.65),'teal');box('Cruz horizontal',(-1.20,-22.59,13.35),(1.20,-22.43,13.99),'teal')
sign('PILLBOX',0,-22.69,10.6,5.2,.65);sign('MEDICAL CENTER',0,-22.69,9.75,5.7,.54)
box('Marquise principal',(-8,-27,3.42),(8,-22,3.70),'stone',True,.06);box('Friso marquise',(-8.02,-27.03,3.47),(8.02,-26.99,3.54),'teal')
box('Marquise emergencia',(-30,-28.5,3.5),(-19.5,-22,3.8),'stone',True,.04);sign('EMERGENCIA',-23.1,-28.53,3.64,7,.9)
for x in [-29,-20.5]:box('Coluna emergencia',(x-.18,-27.8,0),(x+.18,-27.44,3.5),'stone',True)
for x in [-7.4,7.4]:cyl('Coluna entrada',(x,-26,0),.23,3.42,'stone',True,24)
for x in [-23.1,-5,0,5]:spec['lights'].append(dict(model=active,pos=[x,-24.7,3.1],color=[249,234,201],intensity=2.4,range=8))
# Rounded glazed tower accents, matching the curved bay language of the reference.
for x in [-30.2,30.2]:
    for z in [.2,4.35,8.8]:cyl('Baia cornija',(x,-22.75,z),2.25,.23,'stone',False,32)
    for z in [1,5.4]:
        cyl('Baia vidro',(x,-22.72,z),1.97,2.70,'glass',False,32)
        for i in range(13):
            ang=math.pi+i*math.pi/12;xx=x+2.02*math.cos(ang);yy=-22.72+2.02*math.sin(ang);beam('Baia montante',(xx,yy,z),(xx,yy,z+2.70),.022,'gold')
    cyl('Baia base',(x,-22.72,0),2.05,1,'stone',True,24)
box('Cobertura tecnica',(-10,4,8.8),(10,17,9.45),'stone',True,.07)
for x in [-6,0,6]:box('Ventilacao cobertura',(x-1,7,9.45),(x+1,10,10.25),'metal')
for x in [-32.7,32.5]:box('Platibanda lateral',(x,-21,8.8),(x+.22,22,9.55),'stone',True)
box('Platibanda fundos',(-33,21.7,8.8),(33,22,9.55),'stone',True)

# Clinical furniture is authored as real meshes, with simplified independent collision.
def chair(x,y,z,key='fabric'):
    box('Cadeira assento',(x-.25,y-.24,z+.40),(x+.25,y+.24,z+.49),key,True,.035);box('Cadeira encosto',(x-.25,y+.20,z+.47),(x+.25,y+.28,z+.99),key,False,.035)
    for xx in [x-.19,x+.19]:
        for yy in [y-.17,y+.18]:beam('Cadeira pe',(xx,yy,z),(xx,yy,z+.42),.02)

def desk(x,y,z,w=2.4):
    box('Bancada',(x-w/2,y-.42,z+.75),(x+w/2,y+.42,z+.82),'white',True,.025)
    for xx in [x-w/2+.1,x+w/2-.5]:box('Gaveteiro',(xx,y-.38,z+.08),(xx+.4,y+.38,z+.75),'teal',True)
    box('Computador base',(x-.2,y+.03,z+.82),(x+.2,y+.25,z+.855),'dark');beam('Computador suporte',(x,y+.14,z+.85),(x,y+.14,z+1.04),.025);box('Computador monitor',(x-.31,y+.09,z+1.03),(x+.31,y+.16,z+1.43),'dark');box('Computador tela',(x-.28,y+.08,z+1.06),(x+.28,y+.086,z+1.40),'screen');box('Teclado',(x-.28,y-.22,z+.82),(x+.28,y-.04,z+.85),'dark');chair(x,y-.95,z)

def bed(x,y,z,surgery=False):
    key='fabric' if not surgery else 'teal';box('Leito estrutura',(x-.49,y-1.08,z+.46),(x+.49,y+1.08,z+.60),'metal',True,.028);box('Leito colchao',(x-.47,y-1.03,z+.6),(x+.47,y+1.03,z+.78),key,True,.05);box('Travesseiro',(x-.40,y+.55,z+.78),(x+.40,y+.97,z+.88),'white',False,.06)
    for xx in [x-.41,x+.41]:
        for yy in [y-.88,y+.88]:
            beam('Leito suporte',(xx,yy,z+.1),(xx,yy,z+.5),.03);cyl('Rodizio leito',(xx,yy,z+.035),.07,.08,'rubber')
    for xx in [x-.52,x+.52]:beam('Grade leito',(xx,y-.82,z+.84),(xx,y+.82,z+.84),.025)
    box('Monitor clinico',(x+.76,y+.60,z+1.12),(x+1.20,y+.77,z+1.48),'white');box('Tela sinais',(x+.79,y+.59,z+1.15),(x+1.17,y+.596,z+1.45),'screen');beam('Monitor haste',(x+.97,y+.68,z+.20),(x+.97,y+.68,z+1.12),.025)
    for i in range(12):
        t=i/11;yy=y+.586;xx=x+.81+t*.33;zz=z+1.29+( .09 if i%4==1 else -.06 if i%4==2 else .0);beam('ECG',(xx,yy,zz),(xx+.02,yy,zz+.005),.003,'leaf',n=4)
    beam('Suporte soro',(x-.78,y+.67,z),(x-.78,y+.67,z+1.93),.018);beam('Gancho soro',(x-.95,y+.67,z+1.90),(x-.61,y+.67,z+1.90),.013);box('Bolsa soro',(x-.74,y+.66,z+1.51),(x-.63,y+.70,z+1.75),'glass');beam('Tubo soro',(x-.685,y+.68,z+1.51),(x-.685,y+.68,z+.7),.006,'white',n=4)
    if surgery:
        beam('Braco cirurgico',(x,y,z+3.8),(x+.45,y,z+2.75),.07,'white');beam('Braco cirurgico',(x+.45,y,z+2.75),(x,y+.25,z+2.5),.055,'white');cyl('Foco cirurgico',(x,y+.25,z+2.35),.40,.13,'white',n=24);cyl('Difusor foco',(x,y+.25,z+2.34),.32,.013,'led',n=24)
        box('Mesa instrumental',(x+1.3,y-.3,z+.7),(x+2.1,y+.3,z+.76),'metal',True);box('Bandeja',(x+1.40,y-.18,z+.76),(x+1.95,y+.18,z+.79),'metal')

def scanner(x,y,z,mri=False):
    # Ring has an actual clear central opening rather than a solid cylinder.
    n=32;v=[]
    for yy in [-.55,.55]:
        for rr in [1.12,.67]:
            v.extend((x+rr*math.cos(a),y+yy,z+1.24+rr*math.sin(a)) for a in np.arange(n)*2*math.pi/n)
    fs=[]
    for i in range(n):
        j=(i+1)%n;fs.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
    mesh('Scanner anel',v,fs,'white',True,True);box('Scanner base',(x-1.08,y-.5,z),(x+1.08,y+.5,z+.45),'teal',True,.08);box('Scanner mesa',(x-.3,y-2.7,z+.63),(x+.3,y+.6,z+.76),'white',True,.04);box('Scanner suporte',(x-.20,y-2.1,z),(x+.20,y-1.65,z+.63),'metal',True);box('Scanner painel',(x+.80,y-.57,z+1.3),(x+1.04,y-.55,z+1.65),'screen')

for r in spec['rooms']:
    active=spec['models'][3+r['level']];x,y,z=r['center'];label=r['label'];x0,y0,x1,y1=r['bounds']
    if label.startswith('CIRURGIA'):bed(x,y,z,True);desk(x,y1-1.5,z,2)
    elif label in ['UTI','RECUPERACAO','ENFERMARIA']:
        for yy in np.arange(y0+2,y1-1,4):bed(x-.7,yy,z)
        desk(x,y1-1,z,2)
    elif label in ['TOMOGRAFIA','RADIOLOGIA']:scanner(x,y-1,z,label=='RADIOLOGIA');desk(x,y1-1.5,z,2)
    elif label=='OBITOS':
        for xx in [x-1.25,x+1.25]:
            box('Camara mortuaria',(xx-1.12,y1-2.3,z),(xx+1.12,y1-.2,z+2.8),'metal',True,.04)
            for zz in [.15,1.08,2.01]:box('Gaveta mortuaria',(xx-1.02,y1-2.35,z+zz),(xx+1.02,y1-2.31,z+zz+.72),'dark');beam('Puxador gaveta',(xx-.18,y1-2.42,z+zz+.35),(xx+.18,y1-2.42,z+zz+.35),.02)
        bed(x,y0+3,z);desk(x,y1-4,z,2)
    elif label in ['REUNIAO MEDICA','CONVERSAS MEDICAS','ADMINISTRACAO']:
        box('Mesa reuniao',(x-1.05,y-1.65,z+.72),(x+1.05,y+1.65,z+.80),'wood',True,.04)
        for yy in [-1,0,1]:chair(x-1.65,y+yy,z);chair(x+1.65,y+yy,z)
        sign('EQUIPE MEDICA',x,y1-.15,z+2.65,3.8,1)
    elif label in ['DESCANSO','EQUIPE MEDICA']:
        for yy in [y0+2,y0+6,y0+10]:
            if yy+2<y1:bed(x-1,yy,z)
        box('Sofa equipe',(x-1.35,y1-2,z+.10),(x+1.35,y1-1,z+.50),'fabric',True,.08);desk(x,y1-3.5,z,2)
    elif label in ['SANITARIOS','VESTIARIO']:
        for xx in [x-1.8,x,x+1.8]:
            if label=='VESTIARIO':box('Armario vestiario',(xx-.6,y1-1,z),(xx+.6,y1-.3,z+2.0),'teal',True,.018)
            else:
                cyl('Vaso sanitario',(xx,y+2,z),.28,.42,'white',True);box('Caixa sanitaria',(xx-.30,y+2.12,z+.2),(xx+.30,y+2.32,z+.8),'white',True);box('Lavatorio',(xx-.5,y0+.5,z+.78),(xx+.5,y0+1.1,z+.91),'white',True);box('Espelho lavabo',(xx-.45,y0+.22,z+1.1),(xx+.45,y0+.24,z+1.85),'glass')
    elif label in ['LABORATORIO','FARMACIA','ESTERILIZACAO']:
        desk(x,y0+2,z,3.7)
        for yy in np.arange(y0+5,y1-1,3):
            box('Armario clinico',(x-2.8,yy,z),(x-2.3,yy+2,z+2.2),'white',True)
            for zz in [.7,1.2,1.7]:
                box('Prateleira clinica',(x-2.81,yy,z+zz),(x-2.29,yy+2,z+zz+.05),'teal')
                for k in range(6):cyl('Frasco clinico',(x-2.55,yy+.18+k*.28,z+zz+.05),.065,.18,'white',n=8)
    else:desk(x,y1-1.5,z,3);bed(x-.7,y0+3,z);chair(x+1.5,y0+2,z)
    # Storage and wall clock visible in every occupied room.
    box('Armario suprimentos',(x0+.15,y1-1.4,z),(x0+.75,y1-.2,z+1.6),'white',True);cyl('Relogio',(x,y1-.20,z+2.8),.16,.04,'white',n=20)

for level in [0,1]:
    active=spec['models'][3+level];z=4.4*level
    # Reception, waiting and family areas leave a broad central path to the cross corridor.
    for xx in [-29,-27.7,-26.4,-25.1,-23.8,-22.5,-21.2,-19.9,-18.6,-17.3]:
        for yy in [-20,-17.3]:chair(xx,yy,z)
    for xx in [11,12.3,13.6,14.9,16.2,17.5,18.8,20.1,21.4,22.7]:chair(xx,-19.5,z)
    box('Balcao recepcao',(-12,-17.3,z),( -4,-16.1,z+1.10),'teal',True,.06);box('Tampo recepcao',(-12.08,-17.4,z+1.1),(-3.92,-16,z+1.17),'stone',True,.025)
    for xx in [-10,-6]:desk(xx,-14.8,z,2)
    sign('RECEPCAO',-8,-17.43,z+.6,4.5,.75)
    for xx in [5,24]:box('Mesa apoio',(xx-.45,-16.5,z+.55),(xx+.45,-15.6,z+.62),'wood',True,.03)

active=spec['models'][5]
def palm(x,y,z,h=5):
    cyl('Vaso jardim',(x,y,z),.65,.60,'stone',True,16);cyl('Terra vaso',(x,y,z+.6),.61,.015,'soil');beam('Palmeira tronco',(x,y,z+.61),(x+.12,y,z+h),.14,'wood',n=10)
    for i in range(10):
        a=i*2*math.pi/10;d=np.array([math.cos(a),math.sin(a),0]);c=np.array([x+.12,y,z+h]);side=np.array([-d[1],d[0],0])*.28;v=[c,c+d*.8+side+np.array([0,0,.15]),c+d*2.7+np.array([0,0,-.95]),c+d*.8-side+np.array([0,0,.15])];mesh('Palmeira folha',v,[(0,1,2),(0,2,3),(2,1,0),(3,2,0)],'leaf',False)
def hedge(x,y,z,length):
    box('Jardineira',(x-length/2,y-.45,z),(x+length/2,y+.45,z+.5),'stone',True,.035)
    for xx in np.arange(x-length/2+.35,x+length/2,.55):cyl('Arbusto jardim',(xx,y,z+.5),.44,.62,'leaf',n=10)
for x in [-29,-18,18,29]:palm(x,-29.5,0,5.8)
for x in [-28,-17,17,28]:palm(x,18.7,8.8,3.8)
for x in [-20,20]:hedge(x,-29.4,0,11);hedge(x,20,8.8,11)
for x in [-36,36]:
    for y in [-15,0,15]:palm(x,y,-.1,5)
hedge(0,25,-.1,16)
for x in [-35,35]:
    for y in [-10,5]:box('Banco praca',(x-.35,y-1,-.03),(x+.35,y+1,.5),'stone',True,.03)
box('Totem hospital',(12,-30,0),(23,-29.5,1.85),'stone',True,.08);sign('PILLBOX',17.5,-30.035,1.15,7,.65);sign('MEDICAL CENTER',17.5,-30.035,.48,7,.50)
for x in [-36,36]:
    for y in [-25,10]:beam('Balizador haste',(x,y,0),(x,y,2.1),.045,'dark');cyl('Balizador LED',(x,y,2.05),.09,.10,'led');spec['lights'].append(dict(model=active,pos=[x,y,1.9],color=[253,234,206],intensity=1.5,range=8))

# Door leaf prototypes live at their own model origin; actual instances are script owned.
for index,w,h in [(6,1.4,2.65),(7,2.4,3.0)]:
    active=spec['models'][index]
    for lo,hi in [((0,-.05,0),(.06,.05,h)),((w-.06,-.05,0),(w,.05,h)),((.06,-.05,0),(w-.06,.05,.12)),((.06,-.05,h-.12),(w-.06,.05,h))]:box('Porta perfil',lo,hi,'teal',True)
    box('Porta visor',(.06,-.012,.12),(w-.06,.012,h-.12),'glass',True)
    for yy in [-.10,.10]:beam('Porta puxador',(w-.18,yy,.86),(w-.18,yy,1.4),.015,'metal')
    if index==6:box('Faixa privacidade',(.065,-.015,.55),(w-.065,.015,1.10),'white')

spec['collision_meshes']=collisions;spec['parts']={k:len(v) for k,v in groups.items()};spec['bounds']={}
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene['origem_gta']=spec['origin'];scene['projeto']='Hospital Carcer Way: 32 salas, dois pavimentos, escada fisica, portas deslizantes, colisao embutida e fachada Art Deco.'
for k in spec['models'][6:]:
    for o in groups[k]:o.hide_render=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'hospital_carcer_editavel.blend'),compress=True)

def export_group(objects,model):
    root=bpy.data.objects.new(model,None);scene.collection.objects.link(root);root.sollum_type=SollumType.DRAWABLE;out=[];buckets={}
    for obj in objects:buckets.setdefault(obj.data.materials[0].name,[]).append(obj)
    for batch in buckets.values():
        bpy.ops.object.select_all(action='DESELECT');copies=[]
        for src in batch:
            obj=bpy.data.objects.new(src.name+'_export',src.data.copy());scene.collection.objects.link(obj);obj.select_set(True);copies.append(obj)
        bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();obj=bpy.context.object;obj.parent=root;convert_obj_to_model(obj);out.append(obj)
    pts=np.array([v.co for obj in out for v in obj.data.vertices]);bounds={'lo':pts.min(0).tolist(),'hi':pts.max(0).tolist()};targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
    with export_context_scope(ExportContext(model,ExportSettings(targets=targets))):export_ydr(root).save(O,targets)
    if model.startswith('hc_mobiliario') or model=='hc_jardins':
        for ratio,suffix in [(.6,'medium'),(.30,'low'),(.12,'verylow')]:
            lr=bpy.data.objects.new(model+'_'+suffix,None);scene.collection.objects.link(lr);lr.sollum_type=SollumType.DRAWABLE;copies=[]
            for src in out:
                obj=src.copy();obj.data=src.data.copy();scene.collection.objects.link(obj);obj.parent=lr;copies.append(obj);bpy.context.view_layer.objects.active=obj
                dec=obj.modifiers.new('LOD','DECIMATE');dec.ratio=ratio;dec.use_collapse_triangulate=True;obj.select_set(True);bpy.ops.object.modifier_apply(modifier=dec.name);obj.select_set(False)
            with export_context_scope(ExportContext(lr.name,ExportSettings(targets=targets))):export_ydr(lr).save(O,targets)
            for obj in copies:bpy.data.objects.remove(obj,do_unlink=True)
            bpy.data.objects.remove(lr,do_unlink=True)
    for obj in out:bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.objects.remove(root,do_unlink=True);return bounds
for name,objects in groups.items():spec['bounds'][name]=export_group(objects,name)
(P/'spec.json').write_text(json.dumps(spec,indent=2));print('HOSPITAL_MODELS_READY',spec['parts'],flush=True)
