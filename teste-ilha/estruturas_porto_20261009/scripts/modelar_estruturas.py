"""Biblioteca independente: dez construcoes a partir das referencias do usuario.

Executar com Blender --background --python este_arquivo -- --ids 1,2,...
As imagens originais sao empacotadas sem edicao. As UVs das fachadas amostram
os pixels da referencia; os volumes e interiores sao geometria real editavel.
"""
import bpy, math, random, json, argparse, sys, time
from pathlib import Path
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
random.seed(10092026)
CFG = {
 1: dict(nome='Casa_creme_varanda',w=9,d=8,n=1,c=(.78,.74,.64),esq=False,
   frente=[(125,538),(775,578),(770,1125),(122,1072)],lado=[(775,578),(1193,518),(1180,1080),(770,1125)],
   janelas=[(.20,.48,1.4,1.55)],portas=[(.70,1.1)],porch=True),
 2: dict(nome='Casa_amarela',w=9,d=8,n=1,c=(.77,.44,.09),esq=True,
   frente=[(576,560),(1215,540),(1205,994),(576,1127)],lado=[(77,541),(576,560),(576,1127),(78,1030)],
   janelas=[(.22,.47,1.25,1.65),(.85,.47,1.25,1.65)],portas=[(.54,1.05)]),
 3: dict(nome='Sobrado_azul',w=9,d=8,n=2,c=(.18,.44,.62),esq=False,
   frente=[(91,433),(834,449),(832,1078),(91,1005)],lado=[(834,449),(1215,416),(1202,1018),(832,1078)],
   janelas=[(.22,.29,1.25,1.6),(.78,.29,1.25,1.6),(.23,.77,1.25,1.6),(.74,.77,1.25,1.6)],portas=[(.5,1.1)]),
 4: dict(nome='Predio_verde_varandas',w=10.5,d=8.5,n=3,c=(.34,.55,.51),esq=False,
   frente=[(155,292),(934,327),(934,1200),(150,1185)],lado=[(934,327),(1198,252),(1188,1160),(934,1200)],
   janelas=[(.18,.18,1.2,1.5),(.82,.18,1.2,1.5)],portas=[(.50,1.3)],varandas=True),
 5: dict(nome='Predio_creme_varandas',w=10.5,d=8.5,n=3,c=(.79,.75,.64),esq=False,
   frente=[(158,259),(968,286),(959,1190),(151,1178)],lado=[(968,286),(1188,370),(1180,1118),(959,1190)],
   janelas=[(.19,.17,1.25,1.5),(.81,.17,1.25,1.5)],portas=[(.50,1.3)],varandas=True),
 6: dict(nome='Mercado',w=13,d=8,n=1,c=(.16,.45,.62),esq=True,
   frente=[(400,536),(1215,542),(1210,882),(403,910)],lado=[(69,521),(400,536),(403,910),(72,870)],
   janelas=[],portas=[],loja='mercado'),
 7: dict(nome='Farmacia',w=12,d=8,n=2,c=(.36,.61,.50),esq=True,
   frente=[(367,323),(1190,405),(1190,1064),(367,1080)],lado=[(82,405),(367,323),(367,1080),(84,1040)],
   janelas=[(.16,.77,1.2,1.6),(.39,.77,1.2,1.6),(.63,.77,1.2,1.6),(.86,.77,1.2,1.6)],portas=[],loja='farmacia'),
 8: dict(nome='Mercearia_sobrado',w=10,d=8,n=2,c=(.18,.43,.61),esq=False,
   frente=[(113,387),(908,393),(898,1112),(93,1037)],lado=[(908,393),(1206,394),(1200,1025),(898,1112)],
   janelas=[(.25,.79,1.4,1.65),(.76,.79,1.4,1.65)],portas=[],loja='mercearia'),
 9: dict(nome='Posto_combustivel',w=12,d=7,n=1,c=(.78,.76,.66),esq=True,
   frente=[(755,607),(1213,609),(1213,862),(755,861)],lado=[(1213,609),(1235,597),(1233,845),(1213,862)],
   janelas=[],portas=[],loja='posto'),
 10: dict(nome='Galpao_oficina',w=12,d=16,n=1,c=(.61,.62,.60),esq=False,h=5.2,
   frente=[(73,532),(748,641),(749,995),(67,869)],lado=[(748,641),(1215,533),(1211,812),(749,995)],
   janelas=[],portas=[],galpao=True),
}
C=None; M={}; COL={}; PHOTO=None; P={}; MATCACHE={}; BUILDID=0

def collection(name):
    if name not in COL:
        co=bpy.data.collections.new(name); bpy.context.scene.collection.children.link(co); COL[name]=co
    return COL[name]

def link(o,group):
    collection(group).objects.link(o); return o

def homography(points, dst=None):
    if dst is None: dst=points; points=[(0,1),(1,1),(1,0),(0,0)]
    a=[]; b=[]
    for (x,y),(u,v) in zip(points,dst):
        a.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]])
        b.extend([u,v])
    q=np.linalg.solve(np.asarray(a,float),np.asarray(b,float))
    return np.array([[q[0],q[1],q[2]],[q[3],q[4],q[5]],[q[6],q[7],1.]])

def texpoint(h,u,v):
    a=h@np.array([u,v,1.]); return (float(a[0]/a[2])/1280.,1.-float(a[1]/a[2])/1280.)

def material(name,color,rough=.72,metal=0,noise=0):
    if name in M:return M[name]
    m=bpy.data.materials.new(name); m.use_nodes=True; m.diffuse_color=(*color,1.)
    nt=m.node_tree; bs=nt.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1.); bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
    if noise:
        tx=nt.nodes.new('ShaderNodeTexNoise');tx.inputs['Scale'].default_value=noise;tx.inputs['Detail'].default_value=4
        ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*[x*.65 for x in color],1.)
        ramp.color_ramp.elements[1].color=(*[min(1,x*1.18) for x in color],1.)
        nt.links.new(tx.outputs['Fac'],ramp.inputs[0]);nt.links.new(ramp.outputs[0],bs.inputs['Base Color'])
        bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.19;bump.inputs['Distance'].default_value=.025
        nt.links.new(tx.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs[0],bs.inputs['Normal'])
    M[name]=m;return m

def photo_material(name):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree; bs=nt.nodes.get('Principled BSDF')
    tx=nt.nodes.new('ShaderNodeTexImage');tx.image=PHOTO;tx.interpolation='Linear';tx.extension='EXTEND'
    fallback=nt.nodes.new('ShaderNodeMixRGB');fallback.inputs[1].default_value=(*C['c'],1)
    nt.links.new(tx.outputs['Alpha'],fallback.inputs[0]);nt.links.new(tx.outputs['Color'],fallback.inputs[2])
    nt.links.new(fallback.outputs[0],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.8
    nt.links.new(fallback.outputs[0],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=.10
    return m

def sampled_material(name,patch,base,scale=.80):
    """Use a clean region of the original PNG as a repeating material atlas.
    No raster is cropped or altered: sampling happens entirely in Blender nodes.
    World-sized UVs avoid stretching the patch across each wall segment.
    """
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
    uv=nt.nodes.new('ShaderNodeTexCoord');sc=nt.nodes.new('ShaderNodeVectorMath');sc.operation='SCALE';sc.inputs[3].default_value=scale
    nt.links.new(uv.outputs['UV'],sc.inputs[0]);fr=nt.nodes.new('ShaderNodeVectorMath');fr.operation='FRACTION';nt.links.new(sc.outputs[0],fr.inputs[0])
    mul=nt.nodes.new('ShaderNodeVectorMath');mul.operation='MULTIPLY'
    x0,y0,x1,y1=patch;mul.inputs[1].default_value=((x1-x0)/1254,(y1-y0)/1254,0);nt.links.new(fr.outputs[0],mul.inputs[0])
    add=nt.nodes.new('ShaderNodeVectorMath');add.operation='ADD';add.inputs[1].default_value=(x0/1254,1-y1/1254,0);nt.links.new(mul.outputs[0],add.inputs[0])
    tx=nt.nodes.new('ShaderNodeTexImage');tx.image=PHOTO;nt.links.new(add.outputs[0],tx.inputs['Vector'])
    mix=nt.nodes.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(*base,1);nt.links.new(tx.outputs['Alpha'],mix.inputs[0]);nt.links.new(tx.outputs['Color'],mix.inputs[2])
    nt.links.new(mix.outputs[0],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.84
    n=nt.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=80;n.inputs['Detail'].default_value=3
    b=nt.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=.12;b.inputs['Distance'].default_value=.018
    nt.links.new(n.outputs['Fac'],b.inputs['Height']);nt.links.new(b.outputs[0],bs.inputs['Normal'])
    return m

def find_wall_patch():
    """Read-only search for plaster pixels, rejecting transparency and windows.
    Pixels are inspected but the user supplied raster is never changed.
    """
    iw,ih=PHOTO.size;pixels=np.asarray(PHOTO.pixels[:],dtype=np.float32).reshape(ih,iw,4)[::-1]
    target=np.array(C['c']);target=target/max(.001,np.linalg.norm(target));best=None
    for key in ('frente','lado'):
        quad=np.array(C[key]);hinv=np.linalg.inv(P[key]);lo=quad.min(axis=0).astype(int);hi=quad.max(axis=0).astype(int)
        for y in range(max(0,int(lo[1])),min(ih-48,int(hi[1])),12):
            for x in range(max(0,int(lo[0])),min(iw-32,int(hi[0])),12):
                corners=[hinv@np.array([xx,yy,1.]) for xx,yy in [(x,y),(x+32,y),(x+32,y+48),(x,y+48)]]
                if any(not(.03<q[0]/q[2]<.97 and .03<q[1]/q[2]<.97) for q in corners):continue
                a=pixels[y:y+48:2,x:x+32:2]
                if np.min(a[:,:,3])<.90:continue
                rgb=a[:,:,:3];norm=np.linalg.norm(rgb,axis=2);hue=rgb/np.maximum(norm[:,:,None],.0001)
                distance=np.linalg.norm(hue-target,axis=2)
                match=float(np.mean(distance<.25));dark=float(np.mean(norm<.24))
                score=match*3-float(distance.mean())*2-dark*2+min(.15,float(rgb.std()))*.25
                if best is None or score>best[0]:best=(score,(x,y,x+32,y+48))
    patch=best[1] if best else (300,600,360,694)
    print('REGIAO_REBOCO',BUILDID,patch,'score',best[0] if best else -1,flush=True)
    return patch

def roof_material():
    m=M['Telha_foto'];nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
    source=next(n for n in nt.nodes if n.type=='TEX_IMAGE')
    vc=nt.nodes.new('ShaderNodeVertexColor');vc.layer_name='Variacao_telhas'
    mix=nt.nodes.new('ShaderNodeMixRGB');mix.inputs[0].default_value=.07
    nt.links.new(vc.outputs['Color'],mix.inputs[1]);nt.links.new(source.outputs['Color'],mix.inputs[2]);nt.links.new(mix.outputs[0],bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value=.78

def sign(text,face,u,z,w,color='Madeira_verde'):
    fbox('Letreiro_painel','frente',u,z,w,.52,.12,.08,'Esquadrias',False,M['Pedra'] if text=='FARMÁCIA' else M['Toldo_azul'])
    data=bpy.data.curves.new('Letras_'+text,'FONT');data.body=text;data.align_x='CENTER';data.align_y='CENTER';data.size=.36;data.extrude=.006;data.bevel_depth=.001
    try:data.font=bpy.data.fonts.load('C:/Windows/Fonts/georgiab.ttf')
    except Exception:pass
    o=bpy.data.objects.new('Letreiro_'+text,data);link(o,'Esquadrias');o.location=face_pos(face,u,.16,z);o.rotation_euler=(math.pi/2,0,0);data.materials.append(M[color])
    if text=='FARMÁCIA':
        for du in (-w*.41,w*.41):
            fbox('Cruz_farmacia','frente',u+du,z,.37,.12,.04,.16,'Esquadrias',False,M['Madeira_verde'])
            fbox('Cruz_farmacia','frente',u+du,z,.12,.37,.04,.16,'Esquadrias',False,M['Madeira_verde'])

def mesh(name,verts,faces,mat,group,uv=None):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);link(o,group)
    if mat:me.materials.append(mat)
    if uv:
        layer=me.uv_layers.new(name='UV_referencia')
        for po in me.polygons:
            for li in po.loop_indices:layer.data[li].uv=uv[me.loops[li].vertex_index]
    return o

FACES=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def box(name,loc,size,mat,group='Arquitetura',bevel=0):
    # Unit cubes and their UVs are shared across all non-projected modules.
    key=mat.name if mat else 'none'
    if key not in MATCACHE:
        v=[(-.5,-.5,-.5),(.5,-.5,-.5),(.5,.5,-.5),(-.5,.5,-.5),(-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)]
        me=bpy.data.meshes.new('Modulo_cubo_'+key);me.from_pydata(v,[],FACES);me.update()
        if mat:me.materials.append(mat)
        MATCACHE[key]=me
    o=bpy.data.objects.new(name,MATCACHE[key]);o.location=loc;o.scale=size;link(o,group)
    if bevel:
        md=o.modifiers.new('Arestas_arredondadas','BEVEL');md.width=bevel;md.segments=2
    return o

def face_length(face):return C['w'] if face=='frente' else C['d']
def face_pos(face,u,depth,z):
    if face=='frente':return (u-C['w']/2,-C['d']/2-depth,z)
    if face=='lado':
        return (-C['w']/2-depth,C['d']/2-u,z) if C['esq'] else (C['w']/2+depth,u-C['d']/2,z)
    raise ValueError(face)
def map_uv(face,co):
    x,y,z=co
    u=(x+C['w']/2)/C['w'] if face=='frente' else ((C['d']/2-y)/C['d'] if C['esq'] else (y+C['d']/2)/C['d'])
    return texpoint(P[face],u,z/C['H'])
def fbox(name,face,u,z,w,h,thick=.2,depth=0,group='Arquitetura',phot=True,mat=None):
    center=face_pos(face,u,depth,z); size=(w,thick,h) if face=='frente' else (thick,w,h)
    if group=='Esquadrias' and not name.startswith(('Letreiro','Lamina_portao')):
        phot=False
        if mat is None:
            mat=M['Madeira_verde'] if name.startswith(('Veneziana','Lamina_veneziana','Porta_')) else M['Pedra']
    if not phot:return box(name,center,size,mat or M['Reboco'],group)
    x,y,zz=center; sx,sy,sz=[s*.5 for s in size]
    v=[(x-sx,y-sy,zz-sz),(x+sx,y-sy,zz-sz),(x+sx,y+sy,zz-sz),(x-sx,y+sy,zz-sz),
       (x-sx,y-sy,zz+sz),(x+sx,y-sy,zz+sz),(x+sx,y+sy,zz+sz),(x-sx,y+sy,zz+sz)]
    iswall=name.startswith('Parede_')
    o=mesh(name,v,FACES,M['Reboco'],group);o.data.materials.append(M['Reboco_foto'] if iswall else M['Referencia'])
    layer=o.data.uv_layers.new(name='UV_referencia')
    target=2 if face=='frente' else (5 if C['esq'] else 3)
    for po in o.data.polygons:
        po.material_index=1 if po.index==target else 0
        for li in po.loop_indices:
            vv=v[o.data.loops[li].vertex_index]
            if iswall:
                uu=vv[0]+C['w']/2 if face=='frente' else (C['d']/2-vv[1] if C['esq'] else vv[1]+C['d']/2)
                layer.data[li].uv=(uu,vv[2])
            else:layer.data[li].uv=map_uv(face,vv)
    return o

def tube(name,points,radius,mat,group='Esquadrias',sides=8):
    # Rings make meshes instead of curve dependencies, suitable for later export.
    vs=[];fs=[]
    for i,p in enumerate(points):
        p=Vector(p); tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])
        if tangent.length<.0001:tangent=Vector((0,0,1))
        tangent.normalize();axis=tangent.cross(Vector((0,0,1)))
        if axis.length<.01:axis=tangent.cross(Vector((0,1,0)))
        axis.normalize();cross=tangent.cross(axis).normalized()
        for j in range(sides):vs.append(tuple(p+radius*(math.cos(j*2*math.pi/sides)*axis+math.sin(j*2*math.pi/sides)*cross)))
        if i:
            for j in range(sides):a=(i-1)*sides+j;b=(i-1)*sides+(j+1)%sides;fs.append((a,b,b+sides,a+sides))
    fs.extend([tuple(range(sides-1,-1,-1)),tuple(range((len(points)-1)*sides,len(points)*sides))])
    return mesh(name,vs,fs,mat,group)

def sphere(name,loc,size,mat,group='Interior',rings=5,sides=10):
    vs=[];fs=[]
    for i in range(rings+1):
        a=math.pi*i/rings
        for j in range(sides):
            b=2*math.pi*j/sides;vs.append((loc[0]+size[0]*math.sin(a)*math.cos(b),loc[1]+size[1]*math.sin(a)*math.sin(b),loc[2]+size[2]*math.cos(a)))
    for i in range(rings):
        for j in range(sides):a=i*sides+j;b=i*sides+(j+1)%sides;fs.append((a,b,b+sides,a+sides))
    return mesh(name,vs,fs,mat,group)

def cylinder(name,loc,r,h,mat,group='Interior',sides=12):
    return tube(name,[(loc[0],loc[1],loc[2]-h/2),(loc[0],loc[1],loc[2]+h/2)],r,mat,group,sides)

def wall(face,openings):
    length=face_length(face); xs=sorted(set([0,length]+[max(0,min(length,x)) for a,b,c,d in openings for x in (a,b)]))
    zs=sorted(set([0,C['H']]+[max(0,min(C['H'],z)) for a,b,c,d in openings for z in (c,d)]))
    for a,b in zip(xs[:-1],xs[1:]):
        for c,d in zip(zs[:-1],zs[1:]):
            if b-a<.005 or d-c<.005:continue
            if any(lo<=(a+b)/2<=hi and zlo<=(c+d)/2<=zhi for lo,hi,zlo,zhi in openings):continue
            fbox('Parede_'+face,face,(a+b)/2,(c+d)/2,b-a,d-c,.24,-.12,'Arquitetura')

def ornament(name,face,u,z,w,h,thick=.10):
    return fbox(name,face,u,z,w,h,thick,.05,'Esquadrias')

def window(face,u,z,w,h,closed=False,planter=False):
    # u,z denote opening center; wall opening and inner reveal remain real.
    group='Esquadrias'
    for du in (-w/2-.09,w/2+.09):ornament('Ombreira_janela',face,u+du,z,.17,h+.25,.16)
    ornament('Verga_pedra',face,u,z+h/2+.16,w+.55,.24,.24)
    ornament('Peitoril_pedra',face,u,z-h/2-.10,w+.50,.16,.36)
    for du in (-w/2+.035,w/2-.035):fbox('Caixilho_vertical',face,u+du,z,.065,h,.085,.005,group,False,M['Madeira_verde'])
    for dz in (-h/2+.035,h/2-.035,0):fbox('Caixilho_horizontal',face,u,z+dz,w,.07,.085,.008,group,False,M['Madeira_verde'])
    fbox('Montante_vidro',face,u,z,.05,h,.08,.02,group,False,M['Madeira_verde'])
    fbox('Vidro_janela',face,u,z,w-.12,h-.12,.013,-.055,group,False,M['Vidro'])
    # Curtains are interior geometry; closed shutters hide the glazing only where shown.
    if not closed:
        for du in (-w*.35,w*.35):fbox('Cortina_linho',face,u+du,z,w*.22,h*.96,.025,-.25,group,False,M['Linho'])
    sw=w*.49
    for s in (-1,1):
        su=u+s*(w*.25 if closed else w*.77)
        fbox('Folha_veneziana',face,su,z,sw,h,.065,.11,group,False,M['Madeira_verde'])
        for edge in (-sw/2+.04,sw/2-.04):fbox('Veneziana_moldura',face,su+edge,z,.07,h,.075,.16,group)
        for j in range(max(12,int(h/.085))):
            zz=z-h/2+.06+j*(h-.12)/(max(12,int(h/.085))-1)
            fbox('Lamina_veneziana',face,su,zz,sw-.11,.040,.08,.155,group)
        for dz in (-h*.34,h*.34):fbox('Dobradiça',face,su-s*sw*.43,z+dz,.038,.10,.035,.21,group,False,M['Ferro'])
    if planter:planter_box(face,u,z-h/2-.08,w*.86)

def door(face,u,width=1.1,z=0,height=2.25,label='Porta',double=False,glazed=False):
    for du in (-width/2-.10,width/2+.10):ornament('Portal_pedra',face,u+du,z+height/2,.18,height+.20,.20)
    ornament('Portal_verga',face,u,z+height+.12,width+.48,.22,.22)
    count=2 if double else 1; fw=width/count
    for j in range(count):
        center=u-width/2+fw*(j+.5);side=-1 if j==0 else 1
        pivot=face_pos(face,center+side*fw/2,.035,z)
        root=bpy.data.objects.new(label+'_dobradiça_'+str(j+1),None);root.location=pivot;link(root,'Esquadrias')
        root['tipo']='porta_abrir';root['abertura_graus']=90;root['abertura_para_fora']=True;root['passagem_largura']=width
        if glazed:
            leaf=fbox(label+'_montante',face,center-fw/2+.05,z+height/2,.10,height,.075,.04,'Esquadrias',False,M['Madeira_verde'])
        else:leaf=fbox(label+'_folha',face,center,z+height/2,fw-.015,height,.075,.04,'Esquadrias',True,M['Madeira_verde'])
        children=[leaf]
        if glazed:
            children.extend([
                fbox(label+'_montante',face,center+fw/2-.05,z+height/2,.10,height,.075,.04,'Esquadrias',False,M['Madeira_verde']),
                fbox(label+'_travessa',face,center,z+height-.05,fw,.10,.075,.04,'Esquadrias',False,M['Madeira_verde']),
                fbox(label+'_travessa',face,center,z+height*.32,fw,.10,.075,.04,'Esquadrias',False,M['Madeira_verde']),
                fbox(label+'_painel_inferior',face,center,z+height*.16,fw,height*.32,.075,.04,'Esquadrias',False,M['Madeira_verde']),
                fbox('Vidro_porta',face,center,z+height*.66,fw-.18,height*.64-.12,.020,.04,'Esquadrias',False,M['Vidro'])])
        for zz in ((z+height*.16,) if glazed else (z+height*.22,z+height*.71)):
            children.append(fbox('Almofada_porta',face,center,zz,fw-.15,height*.30,.042,.10,'Esquadrias',False,M['Madeira_verde']))
        children.append(fbox('Puxador_latao',face,center-side*fw*.35,z+1.03,.032,.22,.06,.14,'Esquadrias',False,M['Latao']))
        for ob in children:
            ob.parent=root
            ob.location=Vector(ob.location)-Vector(pivot)
            # Locations of projected mesh objects are zero; preserve their mesh world points.
            if ob is leaf and ob.location.length<.00001:
                for vt in ob.data.vertices:vt.co-=Vector(pivot)
                ob.location=(0,0,0)
        root.rotation_euler=(0,0,0);root.keyframe_insert('rotation_euler',frame=1)
        direction=(-side if face=='frente' else side)*math.pi/2
        root.rotation_euler.z=direction;root.keyframe_insert('rotation_euler',frame=40);root.rotation_euler.z=0
    C['aberturas'].append(dict(tipo='porta',face=face,u=u,largura=width,z=z,altura=height))

def leaf_mesh(name,origin,tip,width,mat):
    a=Vector(origin);b=Vector(tip);axis=b-a;cross=axis.cross(Vector((0,0,1)))
    if cross.length<.01:cross=Vector((1,0,0))
    cross.normalize();vs=[]
    for i in range(6):
        t=i/5;cen=a+axis*t+Vector((0,0,math.sin(t*math.pi)*.09));r=width*math.sin(t*math.pi)
        vs.extend([tuple(cen-cross*r),tuple(cen+cross*r)])
    return mesh(name,vs,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(5)],mat,'Vegetacao')

def plant(loc,scale=1,flower=False):
    cylinder('Vaso_terracota',(loc[0],loc[1],loc[2]+.21*scale),.27*scale,.42*scale,M['Terracota'],'Vegetacao')
    cylinder('Terra_vaso',(loc[0],loc[1],loc[2]+.425*scale),.245*scale,.03*scale,M['Terra'],'Vegetacao')
    origin=(loc[0],loc[1],loc[2]+.45*scale)
    for j in range(14):
        a=j*2.4;tip=(loc[0]+math.cos(a)*.50*scale,loc[1]+math.sin(a)*.50*scale,loc[2]+(.75+random.random()*.5)*scale)
        tube('Haste', [origin,tip],.010*scale,M['Folha'],'Vegetacao',5);leaf_mesh('Folha_tropical',origin,tip,.15*scale,M['Folha'])
        if flower:sphere('Flor',tip,(.055*scale,)*3,M['Flor'],'Vegetacao',3,5)

def planter_box(face,u,z,w):
    loc=face_pos(face,u,.37,z-.11);box('Floreira',loc,(w,.34,.26) if face=='frente' else (.34,w,.26),M['Terracota'],'Vegetacao')
    for j in range(7):
        p=Vector(face_pos(face,u-w*.4+j*w*.8/6,.40,z+.03))
        for k in range(3):
            b=p+Vector((random.uniform(-.16,.16),random.uniform(-.16,.16),random.uniform(.08,.24)))
            sphere('Folhagem_floreira',b,(.15,.13,.12),M['Folha'],'Vegetacao',3,6)
            if k==0:sphere('Flor_floreira',b+Vector((0,0,.09)),(.045,)*3,M['Flor'],'Vegetacao',3,5)
        for k in range(3):
            b=p+Vector((.08*math.sin(k),-.03,k*-.19));sphere('Ramo_pendente',b,(.10,.10,.15),M['Folha'],'Vegetacao',3,6)

def lamp(face,u,z):
    pos=Vector(face_pos(face,u,.22,z));tube('Suporte_luminaria',[face_pos(face,u,.08,z+.13),tuple(pos+Vector((0,0,.20)))],.03,M['Ferro'])
    cylinder('Lanterna_corpo',tuple(pos),.105,.28,M['Ferro'],'Esquadrias',8)
    cylinder('Lanterna_vidro',tuple(pos),.082,.20,M['Vidro_amarelo'],'Esquadrias',8)
    sphere('Lanterna_tampa',tuple(pos+Vector((0,0,.18))),(.16,.16,.07),M['Ferro'],'Esquadrias',3,8)

def awning(face,u,z,w,depth=1.35,color='Toldo_azul'):
    # Separate canopy with scalloped valance and supporting arms.
    a=face_pos(face,u-w/2,.10,z);b=face_pos(face,u+w/2,.10,z)
    c=face_pos(face,u+w/2,depth,z-.40);d=face_pos(face,u-w/2,depth,z-.40)
    mesh('Toldo_tecido',[a,b,c,d],[(0,1,2,3)],M[color],'Esquadrias')
    vs=[];fs=[];segments=max(8,int(w/.25))
    for j in range(segments+1):
        uu=u-w/2+w*j/segments;dz=.08+.075*(.5+.5*math.sin(j/segments*math.pi*int(w/.38)))
        vs.extend([face_pos(face,uu,depth,z-.39),face_pos(face,uu,depth,z-.39-dz)])
        if j:fs.append((2*j-2,2*j,2*j+1,2*j-1))
    mesh('Babado_toldo',vs,fs,M[color],'Esquadrias')
    tube('Borda_toldo',[d,c],.018,M['Pedra'])
    for du in (-w/2,w/2):tube('Braço_toldo',[face_pos(face,u+du,.08,z-.95),face_pos(face,u+du,depth,z-.42)],.027,M['Ferro'])

def railing(face,u,z,w,depth=.92):
    for height in (.14,1.04):tube('Corrimao_varanda',[face_pos(face,u-w/2,depth,z+height),face_pos(face,u+w/2,depth,z+height)],.025,M['Ferro'])
    for du in (-w/2,w/2):tube('Retorno_guarda_corpo',[face_pos(face,u+du,.04,z+1.04),face_pos(face,u+du,depth,z+1.04)],.025,M['Ferro'])
    for j in range(int(w/.17)+1):
        uu=u-w/2+j*w/int(w/.17);tube('Montante_ferro',[face_pos(face,uu,depth,z+.12),face_pos(face,uu,depth,z+1.04)],.015,M['Ferro'],sides=6)
        if j%2==0:
            pts=[face_pos(face,uu+.065*math.sin(t*2*math.pi),depth,z+.59+.25*math.cos(t*2*math.pi)) for t in np.linspace(0,1,17)]
            tube('Voluta_ferro',pts,.011,M['Ferro'],sides=5)

def balcony(z,w,small=False,u=None):
    u=C['w']/2 if u is None else u;depth=.60 if small else 1.25
    fbox('Laje_varanda','frente',u,z-.10,w,.20,depth,depth/2-.04,'Esquadrias',False,M['Pedra'])
    railing('frente',u,z,w,depth-.10)
    for du in np.linspace(-w*.43,w*.43,3):
        fbox('Mao_francesa','frente',u+float(du),z-.35,.22,.36,.36,.20,'Esquadrias',False,M['Pedra'])
    if small:planter_box('frente',u,z+.38,w*.70)
    else:
        for du in (-w*.42,w*.42):plant(face_pos('frente',u+du,.47,z),.95)
        for du in (-w*.20,w*.20):planter_box('frente',u+du,z+.74,1.1)

def roof():
    w=C['w']+.72;d=C['d']+.72;h=C['H']+.18;r=C.get('roofrise',min(w,d)*.22)
    A=(-w/2,-d/2,h);B=(w/2,-d/2,h);Cc=(w/2,d/2,h);D=(-w/2,d/2,h)
    rr=max(.20,(w-d)*.50);E=(-rr,0,h+r);F=(rr,0,h+r)
    planes=[([A,B,F,E],'frente'),([B,Cc,F],'direita'),([Cc,D,E,F],'tras'),([D,A,E],'esquerda')]
    # Roof patch is sampled from unchanged original image, repeated without cropping.
    patches={1:[(260,430),(700,375),(900,485),(510,515)],2:[(360,397),(765,445),(903,485),(596,479)],
       3:[(319,265),(633,249),(880,288),(555,313)],4:[(398,129),(676,168),(871,229),(608,203)],
       5:[(368,151),(650,145),(888,219),(593,238)],6:[(277,427),(512,430),(719,482),(504,478)],
       7:[(419,260),(667,258),(902,330),(642,313)],8:[(337,239),(600,213),(787,304),(533,319)],
       9:[(471,391),(666,423),(899,460),(656,455)]}
    pat=patches.get(BUILDID,patches[3]);H=homography(pat)
    for verts,label in planes:
        v=[];f=[];uv=[];colors=[];pa,pb=Vector(verts[0]),Vector(verts[1]);pc=Vector(verts[2]);pd=Vector(verts[3]) if len(verts)==4 else pc
        slope=(pd-pa).length;rows=max(6,int(slope/.39));edge=(pb-pa).length
        for row in range(rows):
            t0=row/rows;t1=min(1,(row+1.15)/rows);left=pa.lerp(pd,t0);right=pb.lerp(pc,t0)
            cols=max(1,round((right-left).length/.285))
            for col in range(cols):
                start=len(v)
                factor=random.uniform(.77,1.17);color=(.37*factor,.095*factor,.025*factor,1)
                if random.random()<.10:color=(.075*factor,.095*factor,.036*factor,1)
                for k in range(2):
                    t=t0 if k==0 else t1;le=pa.lerp(pd,t);ri=pb.lerp(pc,t)
                    for j in range(9):
                        s=(col+j/8)/cols;q=le.lerp(ri,s)
                        q.z+=.052*math.sin(j/8*math.pi)+.008+(1-k)*.018
                        v.append(tuple(q));uv.append((s*edge,t*slope));colors.append(color)
                for j in range(8):f.append((start+j,start+j+1,start+j+10,start+j+9))
        ob=mesh('Telhas_ceramicas_'+label,v,f,M['Telha_foto'],'Cobertura',uv)
        attribute=ob.data.color_attributes.new(name='Variacao_telhas',type='FLOAT_COLOR',domain='POINT')
        attribute.data.foreach_set('color',np.asarray(colors,dtype=np.float32).ravel())
        for p in ob.data.polygons:p.use_smooth=True
    for a,b in [(A,E),(B,F),(Cc,F),(D,E),(E,F)]:
        aa,bb=Vector(a),Vector(b);n=max(1,int((bb-aa).length/.35))
        for k in range(n):tube('Cumeeira_telhas',[tuple(aa.lerp(bb,k/n)+Vector((0,0,.07))),tuple(aa.lerp(bb,(k+1)/n)+Vector((0,0,.07)))],.09,M['Terracota'],'Cobertura',8)
    for a,b in [(A,B),(B,Cc),(Cc,D),(D,A)]:tube('Calha_beiral',[a,b],.065,M['Calha'],'Cobertura',8)
    for x in (-C['w']/2-.12,C['w']/2+.12):
        pts=[(x,-C['d']/2-.12,h),(x,-C['d']/2-.12,.14)]
        tube('Tubo_pluvial',pts,.060,M['Calha'],'Esquadrias',8)
    for z in (.15,C['H']-.11):
        fbox('Cornija_frente','frente',C['w']/2,z,C['w']+.20,.20,.30,.10,'Esquadrias',False,M['Pedra'])
        fbox('Cornija_lado','lado',C['d']/2,z,C['d']+.20,.20,.30,.10,'Esquadrias',False,M['Pedra'])
    # Roof underside seals attic; floor walls remain independent.
    box('Forro_ultimo_andar',(0,0,C['H']-.04),(C['w']-.30,C['d']-.30,.08),M['Linho'],'Cobertura')

def slab_with_hole(z,group):
    w=C['w'];d=C['d'];st=C['n']>1 and z>0
    if not st:return box('Piso',(0,0,z-.10),(w-.12,d-.12,.20),M['Piso'],group)
    x0=w/2-1.80;x1=w/2-.24;y0=-2.6;y1=2.65
    rects=[(-w/2+.06,x0,-d/2+.06,d/2-.06),(x1,w/2-.06,-d/2+.06,d/2-.06),(x0,x1,-d/2+.06,y0),(x0,x1,y1,d/2-.06)]
    for a,b,c,d0 in rects:
        if b>a and d0>c:box('Laje_com_abertura_escada',((a+b)/2,(c+d0)/2,z-.10),(b-a,d0-c,.20),M['Piso'],group)
    C['aberturas'].append(dict(tipo='vao_escada',z=z,limites=[x0,x1,y0,y1]))

def stairs(floor):
    z=floor*C['story'];x=C['w']/2-1.05;n=18;run=4.9;rise=C['story']/n;g='Interior_'+str(floor+1)
    for i in range(n):
        y=-2.45+run*(i+.5)/n;h=(i+1)*rise
        box('Degrau_'+str(i+1),(x,y,z+h/2),(1.26,run/n+.012,h),M['Madeira'],g)
    for dx in (-.69,.69):
        pts=[(x+dx,-2.45,z+1.02),(x+dx,2.45,z+C['story']+1.02)]
        tube('Corrimao_escada',pts,.035,M['Ferro'],g)
        for i in range(0,n,3):
            yy=-2.45+run*(i+.5)/n;zz=z+(i+1)*rise
            tube('Balustre_escada',[(x+dx,yy,zz),(x+dx,yy,zz+1.00)],.022,M['Ferro'],g)

def partition_with_door(name,x0,x1,y,z,height=2.85,doorx=0,width=1.0,group='Interior_1'):
    for a,b in [(x0,doorx-width/2),(doorx+width/2,x1)]:
        if b>a:box(name,((a+b)/2,y,z+height/2),(b-a,.14,height),M['Interior'],group)
    box(name+'_verga',(doorx,y,z+(height+2.2)/2),(width,.14,height-2.2),M['Interior'],group)

def bed(x,y,z,g):
    box('Cama_estrutura',(x,y,z+.22),(1.65,2.10,.34),M['Madeira'],g)
    box('Colchao',(x,y,z+.47),(1.58,2.0,.24),M['Linho'],g,.015)
    box('Cobertor',(x,y-.20,z+.60),(1.57,1.45,.035),M['Tecido_azul'],g)
    box('Cabeceira',(x,y+1,z+.64),(1.72,.10,1.04),M['Madeira'],g)
    for dx in (-.38,.38):sphere('Travesseiro',(x+dx,y+.70,z+.65),(.32,.23,.085),M['Linho'],g)
    box('Mesa_cabeceira',(x-1.08,y+.66,z+.31),(.40,.45,.62),M['Madeira'],g)

def table(x,y,z,g,width=1.3):
    box('Mesa_tampo',(x,y,z+.77),(width,.80,.075),M['Madeira'],g)
    for dx in (-width*.40,width*.40):
        for dy in (-.30,.30):box('Mesa_pe',(x+dx,y+dy,z+.38),(.07,.07,.76),M['Madeira'],g)
    for dx in (-width*.38,width*.38):
        for dy in (-.68,.68):
            box('Cadeira_assento',(x+dx,y+dy,z+.46),(.40,.42,.075),M['Madeira'],g)
            box('Cadeira_encosto',(x+dx,y+dy+math.copysign(.18,dy),z+.74),(.40,.06,.55),M['Madeira'],g)
            for ax in (-.14,.14):
                for ay in (-.14,.14):box('Cadeira_pe',(x+dx+ax,y+dy+ay,z+.22),(.045,.045,.44),M['Madeira'],g)

def kitchen(x,y,z,g):
    box('Bancada_cozinha',(x,y,z+.47),(2.6,.65,.94),M['Madeira'],g)
    box('Bancada_pedra',(x,y,z+.96),(2.68,.69,.055),M['Pedra'],g)
    box('Cuba_pia',(x-.52,y,z+.992),(.62,.45,.025),M['Aco'],g)
    tube('Torneira',[(x-.52,y+.20,z+1.0),(x-.52,y+.20,z+1.32),(x-.52,y-.02,z+1.32)],.021,M['Aco'],g)
    for dx in (.58,.98):
        for dy in (-.12,.15):cylinder('Boca_fogao',(x+dx,y+dy,z+1.0),.10,.018,M['Ferro'],g,10)
    for j in range(4):box('Armario_cozinha_porta',(x-1+j*.68,y-.34,z+.47),(.60,.028,.82),M['Madeira_verde'],g)
    box('Geladeira',(x-1.75,y,z+.94),(.68,.72,1.88),M['Interior'],g,.015)
    box('Geladeira_puxador',(x-1.49,y-.40,z+1.15),(.028,.055,.47),M['Aco'],g)

def bathroom(x,y,z,g):
    partition_with_door('Parede_banheiro',x-1.15,x+1.15,y-1.05,z,doorx=x,width=.88,group=g)
    box('Divisoria_banheiro',(x-1.15,y,z+1.4),(.14,2.1,2.8),M['Interior'],g)
    sphere('Vaso_sanitario',(x+.58,y+.1,z+.34),(.24,.33,.34),M['Ceramica'],g)
    box('Caixa_descarga',(x+.58,y+.43,z+.71),(.42,.16,.49),M['Ceramica'],g)
    box('Lavatorio',(x-.54,y+.65,z+.83),(.55,.42,.16),M['Ceramica'],g)
    box('Espelho',(x-.54,y+.83,z+1.48),(.54,.025,.65),M['Vidro'],g)
    box('Base_duche',(x-.52,y-.20,z+.07),(.80,.90,.10),M['Ceramica'],g)
    tube('Chuveiro',[(x-1.04,y-.20,z+1.4),(x-1.04,y-.20,z+2.18),(x-.75,y-.20,z+2.18)],.025,M['Aco'],g)

def residential_interior(floor):
    g='Interior_'+str(floor+1);z=floor*C['story'];w=C['w'];d=C['d']
    partition_with_door('Divisao_quartos',-w/2+.24,w/2-(1.9 if C['n']>1 else .24),.35,z,doorx=0,group=g)
    if floor==0:
        kitchen(-w*.20,-d/2+.70,z,g);table(-w*.20,-.8,z,g,1.25)
        sx=w*(.30 if C.get('porch') else .22);sy=-.55 if C.get('porch') else -1.1
        box('Sofa',(sx,sy,z+.34),(1.8,.75,.68),M['Tecido_azul'],g)
        box('Sofa_encosto',(sx,sy+.34,z+.66),(1.8,.15,.65),M['Tecido_azul'],g)
        box('Mesa_sala',(sx,sy-1.0,z+.38),(1.1,.60,.075),M['Madeira'],g)
    else:
        table(-w*.23,-1.4,z,g);box('Armario',(0,-d/2+.49,z+1),(1.3,.60,2.0),M['Madeira_verde'],g)
    bed(-w*.27,d*.26,z,g);bathroom(w*.12,d*.24,z,g)
    C['interiores'].append(dict(pavimento=floor+1,uso='moradia',itens=['cama','cozinha' if floor==0 else 'mesa','banheiro','armario']))

def shelf(x,y,z,g,width=1.4,depth=.42,pharma=False):
    for dx in (-width/2,width/2):box('Estante_montante',(x+dx,y,z+1.1),(.06,depth,2.2),M['Madeira'],g)
    for level in range(5):
        zz=z+.15+level*.43;box('Prateleira',(x,y,zz),(width,depth,.045),M['Madeira'],g)
        for j in range(max(4,int(width/.18))):
            px=x-width*.44+j*width*.88/(max(4,int(width/.18))-1)
            m=M['Embalagem_'+str((j+level)%5)]
            if pharma or j%3==0:box('Produto_caixa',(px,y-.03,zz+.13),(.11,.18,.24),m,g)
            else:cylinder('Produto_frasco',(px,y-.025,zz+.13),.047,.22,m,g,8)

def crate(x,y,z,g='Interior_1',fruit=True):
    box('Caixote_base',(x,y,z+.03),(.85,.65,.06),M['Madeira'],g)
    for side in (-1,1):
        for k in range(3):box('Caixote_ripa',(x,y+side*.32,z+.1+k*.09),(.85,.035,.065),M['Madeira'],g)
        for k in range(3):box('Caixote_ripa',(x+side*.42,y,z+.1+k*.09),(.035,.65,.065),M['Madeira'],g)
    if fruit:
        for j in range(20):sphere('Fruta',(x+random.uniform(-.34,.34),y+random.uniform(-.25,.25),z+.24+random.uniform(0,.10)),(.075,.075,.065),M['Fruta_'+str(j%3)],g,4,7)

def commercial_interior(kind):
    g='Interior_1';w=C['w'];d=C['d'];pharma=kind=='farmacia'
    for x in np.linspace(-w/2+1,w/2-2,5):shelf(float(x),d/2-.55,0,g,1.5,pharma=pharma)
    for x in (-w*.24,w*.08):
        for y in (-.1,1.3):shelf(x,y,0,g,1.5,pharma=pharma)
    box('Balcao_atendimento',(-w*.28,-1.65,.52),(2.40,.70,1.04),M['Madeira'],g)
    box('Balcao_tampo',(-w*.28,-1.65,1.07),(2.48,.76,.08),M['Pedra'],g)
    box('Caixa_registradora',(-w*.30,-1.65,1.24),(.40,.32,.25),M['Ferro'],g)
    box('Tela_caixa',(-w*.30,-1.57,1.43),(.30,.06,.23),M['Tecido_azul'],g)
    if not pharma:
        for x in (-w*.30,-w*.07,w*.28):crate(x,-d/2-.22,0,'Esquadrias')
    else:
        box('Cadeira_consulta',(w*.23,2,.35),(1.0,1.65,.70),M['Tecido_azul'],g)
    C['interiores'].append(dict(pavimento=1,uso=kind,itens=['balcao','caixa','estantes','produtos','estoque']))
    if C['n']>1:residential_interior(1)

def inside_lighting():
    for floor in range(C['n']):
        z=floor*C['story'];g='Iluminacao'
        for x in (-C['w']*.23,C['w']*.20):
            dat=bpy.data.lights.new('Luz_interior','AREA');dat.energy=110 if C.get('loja') else 55;dat.shape='DISK';dat.size=1.4;dat.color=(1,.80,.58)
            o=bpy.data.objects.new('Luz_interior',dat);o.location=(x,-.60,z+C['story']-.28);link(o,g)
            cylinder('Plafon',(x,-.60,z+C['story']-.25),.18,.06,M['Vidro_amarelo'],'Interior_'+str(floor+1))

def facade():
    w=C['w'];h=C['H'];L=C['d'];op=[];sideop=[];windows=[];doors=[]
    kind=C.get('loja')
    for u,v,ww,hh in C['janelas']:
        z=v*h;uu=u*w;windows.append(('frente',uu,z,ww,hh,False,BUILDID in (2,3)))
        op.append((uu-ww/2,uu+ww/2,z-hh/2,z+hh/2))
    for u,ww in C['portas']:
        uu=u*w;doors.append(('frente',uu,ww,0,2.28,BUILDID in (4,5),False));op.append((uu-ww/2,uu+ww/2,0,2.28))
    if C.get('varandas'):
        for floor in (1,2):
            z=floor*C['story']
            for u in (.19,.50,.81):
                uu=u*w;ww=1.18;doors.append(('frente',uu,ww,z,2.35,True,True));op.append((uu-ww/2,uu+ww/2,z,z+2.35))
    if kind in ('mercado','mercearia'):
        shopwidth=2.1 if kind=='mercado' else 2.25
        for i,u in enumerate((.19,.50,.81)):
            uu=u*w;op.append((uu-shopwidth/2,uu+shopwidth/2,0,2.45))
            if i==1 and kind=='mercearia':doors.append(('frente',uu,shopwidth,0,2.4,True,True))
            else:
                ornament('Pilar_loja','frente',uu-shopwidth/2-.10,1.3,.20,2.6,.22)
                ornament('Pilar_loja','frente',uu+shopwidth/2+.10,1.3,.20,2.6,.22)
            if kind=='mercado' and i!=1:awning('frente',uu,2.65,shopwidth+.40,1.20,'Toldo_azul' if i==0 else 'Toldo_laranja')
        if kind=='mercearia':awning('frente',w/2,2.85,w-.30,1.60)
        if kind=='mercado':sign('MERCADO','frente',w/2,2.89,3.15,'Linho')
    elif kind=='farmacia':
        for u in (.28,.76):
            uu=u*w;ww=3.5;op.append((uu-ww/2,uu+ww/2,0,2.54))
            if u==.28:doors.append(('frente',uu,2.2,0,2.45,True,True))
            else:fbox('Vitrine_farmacia','frente',uu,1.45,ww,2.1,.02,-.06,'Esquadrias',False,M['Vidro'])
            awning('frente',uu,2.83,ww+.25,1.5,'Toldo_verde')
        sign('FARMÁCIA','frente',w/2,3.28,w-.60)
    elif kind=='posto':
        uu=w*.48;ww=w*.73;op.append((uu-ww/2,uu+ww/2,.15,2.62))
        for j in range(4):fbox('Montante_vitrine','frente',uu-ww/2+j*ww/3,1.39,.08,2.55,.10,.04,'Esquadrias',False,M['Azul_posto'])
        fbox('Vidro_conveniencia','frente',uu,1.39,ww,2.48,.02,-.06,'Esquadrias',False,M['Vidro'])
        doors.append(('frente',uu,1.35,0,2.45,False,True))
        fbox('Faixa_amarela','frente',w/2,2.96,w,.35,.04,.02,'Esquadrias',False,M['Amarelo_posto'])
        fbox('Faixa_azul','frente',w/2,.53,w,1.06,.04,.02,'Esquadrias',False,M['Azul_posto'])
    if C.get('porch'):
        # Actual recessed vestibule: front wall removed across entire porch opening.
        uu=w*.69;op=[r for r in op if r[1]<w*.44 or r[0]>w*.89]
        op.append((w*.44,w*.89,0,2.70));doors=[('frente',uu,1.10,0,2.27,False,False)]
        fbox('Parede_varanda_recuada','frente',uu,1.50,w*.45,3.0,.20,-1.65,'Arquitetura',False,M['Reboco'])
        # Leave an opening in the recessed wall for entrance.
        rec=COL['Arquitetura'].objects.get('Parede_varanda_recuada')
        if rec:bpy.data.objects.remove(rec,do_unlink=True)
        for a,b in ((w*.44,uu-.55),(uu+.55,w*.89)):
            fbox('Parede_varanda_recuada','frente',(a+b)/2,1.50,b-a,3.0,.20,-1.65,'Arquitetura',False,M['Reboco'])
        fbox('Verga_varanda_recuada','frente',uu,2.63,1.1,.74,.20,-1.65,'Arquitetura',False,M['Reboco'])
        fbox('Mureta_varanda','frente',w*.60,.42,w*.32,.84,.25,.04,'Esquadrias',False,M['Pedra'])
        for du in (w*.42,w*.90):fbox('Coluna_varanda','frente',du,1.47,.26,2.94,.30,0,'Esquadrias',False,M['Pedra'])
        plant(face_pos('frente',w*.58,-.65,0),1.0)
    # Side windows on every floor, independently cut through side wall.
    for floor in range(C['n']):
        for u in (.28,.74):
            uu=L*u;z=floor*C['story']+1.70;ww=1.1;hh=1.45
            sideop.append((uu-ww/2,uu+ww/2,z-hh/2,z+hh/2));windows.append(('lado',uu,z,ww,hh,False,BUILDID==7))
    wall('frente',op);wall('lado',sideop)
    for args in windows:window(*args)
    for fa,u,ww,z,hh,dbl,gla in doors:
        before=set(bpy.data.objects.keys())
        door(fa,u,ww,z,hh,double=dbl,glazed=gla)
        if C.get('porch'):
            for ob in bpy.data.objects:
                if ob.name not in before and ob.type=='EMPTY':ob.location.y+=1.65
        lamp(fa,u+(ww/2+.32 if kind else 0),z+hh+.23)
    if C.get('varandas'):
        for floor in (1,2):balcony(floor*C['story'],w-.55)
    if BUILDID==8:
        for u,v,ww,hh in C['janelas']:balcony(v*h-hh/2-.06,ww+.52,True,u*w)
    # Quoins, friezes and roof edge are independent geometry.
    for floor in range(1,C['n']):
        z=floor*C['story'];fbox('Friso_pavimento','frente',w/2,z,w+.08,.16,.21,.09,'Esquadrias',False,M['Pedra'])
        fbox('Friso_pavimento','lado',L/2,z,L+.08,.16,.21,.09,'Esquadrias',False,M['Pedra'])
    for u in (.18,w-.18):
        for k in range(int(h/.40)):
            ornament('Cantaria_canto','frente',u,.20+k*.40,.36,.38,.16)
    if BUILDID in (6,7,8):
        for u in (.045,.94):plant(face_pos('frente',u*w,.55,0),1.3,BUILDID==7)

def back_walls():
    w=C['w'];d=C['d'];h=C['H']
    box('Parede_traseira',(0,d/2-.12,h/2),(w,.24,h),M['Reboco'])
    x=w/2-.12 if C['esq'] else -w/2+.12
    box('Parede_lateral_oculta',(x,0,h/2),(.24,d,h),M['Reboco'])

def gas_station():
    w=18;d=11.5;z=4.3;cy=-8.2
    box('Plataforma_posto',(0,-4.9,-.17),(19.2,19.0,.30),M['Concreto'],'Arquitetura')
    for x in (-5,5):
        box('Ilha_bombas',(x,cy,.13),(3.6,1.65,.25),M['Pedra'],'Esquadrias')
        box('Coluna_cobertura',(x,cy,2.15),(.52,.52,4.3),M['Interior'],'Arquitetura')
        box('Coluna_faixa_azul',(x,cy,.67),(.54,.54,1.15),M['Azul_posto'],'Esquadrias')
        box('Coluna_faixa_amarela',(x,cy,1.34),(.55,.55,.20),M['Amarelo_posto'],'Esquadrias')
        pumpx=x-1.0
        box('Bomba_base',(pumpx,cy,.77),(.74,.66,1.30),M['Interior'],'Esquadrias')
        box('Bomba_gabinete',(pumpx,cy,1.96),(.94,.68,1.18),M['Interior'],'Esquadrias')
        box('Bomba_faixa',(pumpx,cy-.35,2.31),(.86,.03,.31),M['Amarelo_posto'],'Esquadrias')
        box('Bomba_visor',(pumpx,cy-.36,1.91),(.63,.03,.23),M['Ferro'],'Esquadrias')
        for j in range(3):
            px=pumpx-.25+j*.25
            tube('Mangueira_bomba',[(px,cy-.43,1.48),(px-.20,cy-.50,.45),(px+.06,cy-.50,.30),(px+.20,cy-.44,1.35)],.032,M['Ferro'],'Esquadrias',8)
            box('Bico_combustivel',(px,cy-.43,1.48),(.075,.12,.21),M['Embalagem_'+str(j)],'Esquadrias')
        for dx in (-1.58,1.58):
            cylinder('Bolardo_amarelo',(x+dx,cy,.65),.095,1.0,M['Amarelo_posto'],'Esquadrias')
        cylinder('Extintor',(x+.30,cy-.40,1.35),.11,.43,M['Vermelho'],'Esquadrias')
    box('Cobertura_forro',(0,cy,z-.07),(w,d,.14),M['Interior'],'Cobertura')
    for y in (cy-d/2,cy+d/2):
        box('Fascia_amarela',(0,y,z+.10),(w,.14,.50),M['Amarelo_posto'],'Cobertura')
        box('Fascia_azul',(0,y-.075,z-.05),(w,.035,.13),M['Azul_posto'],'Cobertura')
    # Terracotta canopy shares the residential roof generator, while preserving shop config.
    original=dict(C);C.update(w=w,d=d,H=z+.30,roofrise=2.0)
    before=set(bpy.data.objects.keys());roof()
    for o in bpy.data.objects:
        if o.name not in before:o.location.y+=cy
    C.clear();C.update(original)
    for x in (-5,0,5):
        box('Luz_cobertura',(x,cy,z-.17),(.70,.40,.05),M['Vidro_amarelo'],'Esquadrias')
    box('Ar_condicionado',(C['w']/2-1,1.2,C['H']+.35),(1.5,.70,.70),M['Interior'],'Esquadrias')
    for j in range(8):box('Grade_ar_condicionado',(C['w']/2-1, .83,C['H']+.10+j*.055),(1.25,.025,.018),M['Ferro'],'Esquadrias')

def warehouse():
    w=C['w'];d=C['d'];h=C['H'];gate=6.1
    wall('frente',[(w/2-gate/2,w/2+gate/2,0,4.4)])
    ops=[]
    for u in (.30,.77):ops.append((d*u-1.3,d*u+1.3,2.8,3.8))
    wall('lado',ops);back_walls()
    for u in (.30,.77):
        uu=d*u;fbox('Vidro_galpao','lado',uu,3.3,2.58,.98,.018,-.06,'Esquadrias',False,M['Vidro'])
        for j in range(6):fbox('Grade_janela','lado',uu-1.29+j*2.58/5,3.3,.032,1.05,.03,.09,'Esquadrias',False,M['Aco'])
        fbox('Janela_travessa','lado',uu,3.3,2.64,.038,.032,.09,'Esquadrias',False,M['Aco'])
    # Individual shutter slats, animate vertically as one independent mechanism.
    gate_root=bpy.data.objects.new('Portao_enrolar_controle',None);link(gate_root,'Esquadrias');gate_root['tipo']='portao_enrolar';gate_root['curso_m']=4.6
    for j in range(34):
        o=fbox('Lamina_portao','frente',w/2,(j+.5)*4.4/34,gate,4.4/34,.085,.02,'Esquadrias');o.parent=gate_root
    gate_root.keyframe_insert('location',frame=1);gate_root.location.z=4.55;gate_root.keyframe_insert('location',frame=40);gate_root.location.z=0
    # Side corrugation and concrete sill.
    for j in range(int(d/.18)):
        u=(j+.5)*d/int(d/.18)
        if any(a<u<b for a,b,c,dd in ops):continue
        fbox('Onda_chapa','lado',u,(h+1.05)/2,.035,h-1.05,.045,.033,'Esquadrias')
    rise=2.2
    A=(-w/2-.35,-d/2-.35,h);B=(w/2+.35,-d/2-.35,h);D=(-w/2-.35,d/2+.35,h);Cc=(w/2+.35,d/2+.35,h)
    E=(0,-d/2-.35,h+rise);F=(0,d/2+.35,h+rise)
    # Gable shares reference front UV below and separately samples its triangular top.
    gv=[(-w/2,-d/2,h),(w/2,-d/2,h),(0,-d/2,h+rise)]
    guv=[(73/1280,1-532/1280),(748/1280,1-641/1280),(387/1280,1-424/1280)]
    mesh('Frontao_chapa',gv,[(0,1,2)],M['Reboco_foto'],'Arquitetura',[(0,h),(w,h),(w/2,h+rise)])
    mesh('Frontao_tras',[(-w/2,d/2,h),(0,d/2,h+rise),(w/2,d/2,h)],[(0,1,2)],M['Reboco'],'Arquitetura')
    patches=[[(409,420),(905,281),(1225,486),(759,624)],[(409,420),(905,281),(1225,486),(759,624)]]
    for face,patch in zip(([B,Cc,F,E],[D,A,E,F]),patches):
        pa,pb,pc,pd=[Vector(q) for q in face];hv=homography(patch);v=[];uv=[];fs=[];rows=60;cols=100
        for i in range(rows+1):
            t=i/rows
            for j in range(cols+1):
                s=j/cols;q=pa.lerp(pd,t).lerp(pb.lerp(pc,t),s);q.z+=.035*math.cos(q.y*2*math.pi/.15);v.append(tuple(q));uv.append(texpoint(hv,s,t))
        for i in range(rows):
            for j in range(cols):a=i*(cols+1)+j;fs.append((a,a+1,a+cols+2,a+cols+1))
        mesh('Telhado_chapa_corrugada',v,fs,M['Referencia'],'Cobertura',uv)
    tube('Cumeeira_galpao',[E,F],.095,M['Aco'],'Cobertura')
    for a,b in [(A,E),(E,B),(B,Cc),(Cc,F),(F,D),(D,A)]:tube('Rufo_galpao',[a,b],.065,M['Aco'],'Cobertura')
    lamp('frente',w/2,h+.30)
    slab_with_hole(0,'Interior_1');g='Interior_1'
    for x in (-w/2+.6,w/2-.6):
        for y in (-d*.25,d*.25):box('Pilar_aco',(x,y,h/2),(.18,.18,h),M['Aco'],'Arquitetura')
    x0=-w/2+.30;x1=-w/2+1.64;y0=d/2-3.70;y1=d/2-1.30
    for a,b,c,dd in [(x1,w/2-.25,y0,d/2-.30),(x0,x1,y1,d/2-.30)]:
        box('Mezanino',((a+b)/2,(c+dd)/2,2.75),(b-a,dd-c,.18),M['Madeira'],g)
    C['aberturas'].append(dict(tipo='vao_escada_mezanino',z=2.84,limites=[x0,x1,y0,y1]))
    for i in range(16):box('Escada_mezanino',(-w/2+.95,d/2-5.5+i*.27,(i+1)*2.84/32),(1.2,.29,(i+1)*2.84/16),M['Madeira'],g)
    for x in (-w*.28,0,w*.28):shelf(x,d/2-.55,2.85,g,2.1)
    box('Bancada_oficina',(-w/2+1.0,0,.51),(1.4,3.1,1.02),M['Madeira'],g)
    box('Tampo_oficina',(-w/2+1.0,0,1.05),(1.45,3.15,.06),M['Aco'],g)
    for i in range(8):box('Ferramenta',(-w/2+1.0,random.uniform(-1.1,1.1),1.105),(.34,.055,.04),M['Aco'],g)
    for x in (-1.5,1.5):
        for y in (1.0,3.0):crate(x,y,0,g,False)
    for face in ('frente','lado'):
        fbox('Rodape_concreto_galpao',face,face_length(face)/2,.52,face_length(face),1.04,.05,.05,'Esquadrias',False,M['Concreto'])
    C['interiores'].append(dict(pavimento=1,uso='oficina_armazem',itens=['bancada','ferramentas','caixotes','mezanino','escada','estantes']))

def setup(id):
    global C,M,COL,PHOTO,P,MATCACHE,BUILDID
    BUILDID=id;C=dict(CFG[id]);C['story']=3.20;C['H']=C.get('h',C['n']*C['story']);C['aberturas']=[];C['interiores']=[]
    M={};COL={};MATCACHE={};bpy.ops.wm.read_factory_settings(use_empty=True)
    PHOTO=bpy.data.images.load(str(ROOT/'referencias'/f'{id:02}.png'));PHOTO.pack();PHOTO.name=f'Referencia_original_{id:02}'
    P={key:homography(C[key]) for key in ('frente','lado')}
    material('Reboco',C['c'],noise=85);M['Referencia']=photo_material('Pixels_referencia_'+str(id))
    M['Reboco_foto']=sampled_material('Reboco_extraido_da_referencia',find_wall_patch(),C['c'])
    rp={1:(498,376,553,397),2:(792,394,833,414),3:(694,241,736,266),4:(562,105,602,125),5:(721,122,765,145),
      6:(615,428,659,450),7:(614,233,657,254),8:(638,250,680,273),9:(798,407,842,427),10:(695,399,743,430)}
    M['Telha_foto']=sampled_material('Telhas_pixels_da_referencia',rp[id],(.62,.22,.075),2.5)
    roof_material()
    for name,color,metal,noise in [
        ('Pedra',(.71,.66,.52),0,65),('Concreto',(.38,.39,.37),0,90),('Piso',(.50,.40,.27),0,45),
        ('Interior',(.77,.74,.66),0,65),('Madeira',(.23,.105,.037),0,12),('Madeira_verde',(.035,.135,.112),0,34),
        ('Ferro',(.028,.035,.033),.75,0),('Aco',(.38,.42,.42),.65,0),('Latao',(.50,.34,.12),.80,0),
        ('Calha',(.12,.17,.16),.65,0),('Linho',(.73,.73,.66),0,110),('Ceramica',(.82,.85,.81),0,0),
        ('Terracota',(.60,.19,.065),0,45),('Terra',(.11,.066,.027),0,80),('Folha',(.075,.24,.028),0,0),('Flor',(.70,.065,.20),0,0),
        ('Tecido_azul',(.09,.24,.32),0,100),('Toldo_azul',(.075,.29,.44),0,120),('Toldo_verde',(.07,.28,.19),0,100),('Toldo_laranja',(.88,.25,.035),0,100),
        ('Azul_posto',(.025,.25,.47),0,0),('Amarelo_posto',(.93,.55,.02),0,0),('Vermelho',(.60,.018,.008),0,0),
        ('Embalagem_0',(.16,.36,.16),0,0),('Embalagem_1',(.70,.11,.035),0,0),('Embalagem_2',(.075,.25,.57),0,0),
        ('Embalagem_3',(.84,.66,.12),0,0),('Embalagem_4',(.68,.70,.63),0,0),('Fruta_0',(.89,.18,.02),0,0),
        ('Fruta_1',(.90,.61,.03),0,0),('Fruta_2',(.16,.40,.028),0,0)]:material(name,color,metal=metal,noise=noise)
    glass=material('Vidro',(.24,.34,.32),rough=.13);bs=glass.node_tree.nodes.get('Principled BSDF');bs.inputs['Transmission Weight'].default_value=.93;bs.inputs['IOR'].default_value=1.45
    m=material('Vidro_amarelo',(.95,.73,.31),rough=.3);bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=(1,.70,.28,1);bs.inputs['Emission Strength'].default_value=2
    world=bpy.data.worlds.new('Ceu_apresentacao');world.use_nodes=True;bpy.context.scene.world=world
    bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.65,.72,.82,1);bg.inputs['Strength'].default_value=.60
    light=bpy.data.lights.new('Sol','SUN');light.energy=2.6;light.angle=.20;o=bpy.data.objects.new('Sol',light);o.rotation_euler=(.45,-.65,-.45);link(o,'Apresentacao')
    area=bpy.data.lights.new('Preenchimento','AREA');area.energy=800;area.shape='DISK';area.size=12;o=bpy.data.objects.new('Preenchimento',area);o.location=(0,-8,12);o.rotation_euler=(.35,0,0);link(o,'Apresentacao')
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=True
    try:
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
        for dev in prefs.devices:dev.use=dev.type=='OPTIX'
        scene.cycles.device='GPU'
    except Exception:scene.cycles.device='CPU'
    scene.render.resolution_x=1200;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False;scene.view_settings.view_transform='AgX'
    scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='METERS';scene.frame_set(1)
    scene['biblioteca']='estruturas_porto_20261009';scene['referencia']=str(ROOT/'referencias'/f'{id:02}.png')
    scene['nota_fidelidade']='UVs derivadas da unica perspectiva fornecida; faces ocultas e interiores reconstruidos.'

def camera(cutaway=False):
    scene=bpy.context.scene
    if 'Camera' not in bpy.data.objects:
        dat=bpy.data.cameras.new('Camera');o=bpy.data.objects.new('Camera',dat);link(o,'Apresentacao');scene.camera=o
    else:o=bpy.data.objects['Camera']
    w=C['w'];d=C['d'];h=C['H'];cx=0;cy=0
    if BUILDID==9:w=19;d=21;cy=-4.4;h=7
    target=Vector((cx,cy,h*.45));side=-1 if C['esq'] else 1
    # Orthographic rays must originate above ground even at the bottom of frame.
    o.location=target+Vector((side*.95*w,-1.55*d,1.0*max(w,d) if cutaway else .40*max(w,d)))*2
    o.rotation_euler=(target-Vector(o.location)).to_track_quat('-Z','Y').to_euler();o.data.type='ORTHO';o.data.clip_end=1000;o.data.ortho_scale=max(w*1.63,h*1.65,d*1.35)
    if BUILDID==9:o.data.ortho_scale=28
    if cutaway:o.data.ortho_scale*=1.0
    # Ground is presentation-only, tagged to omit during future game export.
    if 'Chao_apresentacao' not in bpy.data.objects:
        box('Chao_apresentacao',(0,cy,-.27),(200,200,.08),M['Concreto'],'Apresentacao')

def collision():
    co=collection('Colisao_preparada');co.hide_render=True;co.hide_viewport=True
    for group in ('Arquitetura',)+tuple('Interior_'+str(i+1) for i in range(C['n'])):
        if group not in COL:continue
        for ob in list(COL[group].objects):
            if any(ob.name.startswith(p) for p in ('Parede','Piso','Laje','Degrau','Mezanino','Escada','Divis')):
                du=ob.copy();du.data=ob.data;du.name='COL_'+ob.name;co.objects.link(du);du['exportar_como']='colisao';du['native_ybn']=False

def render(path,cutaway=False):
    scene=bpy.context.scene;camera(cutaway);hidden=[]
    if cutaway:
        for group in ('Cobertura','Esquadrias','Vegetacao'):
            if group in COL:
                for o in COL[group].objects:
                    if not o.hide_render:hidden.append(o);o.hide_render=True
        for o in COL.get('Arquitetura',[]).objects if 'Arquitetura' in COL else []:
            if o.name.startswith(('Parede_frente','Parede_lado','Frontao','Coluna')):
                hidden.append(o);o.hide_render=True
        for floor in range(1,C['n']):
            for o in COL.get('Interior_'+str(floor+1),[]).objects if 'Interior_'+str(floor+1) in COL else []:
                hidden.append(o);o.hide_render=True
    scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    for o in hidden:o.hide_render=False
    camera(False)

def generate(id,do_render=True):
    setup(id);print('INICIO_MODELO',id,flush=True)
    if C.get('galpao'):warehouse()
    else:
        facade();back_walls();roof()
        for i in range(C['n']):
            slab_with_hole(i*C['story'],'Interior_'+str(i+1))
            if i<C['n']-1:stairs(i)
        if C.get('loja'):commercial_interior(C['loja'])
        else:
            for i in range(C['n']):residential_interior(i)
        if id==9:gas_station()
    inside_lighting()
    collision();camera()
    root=bpy.data.objects.new('Estrutura_'+f'{id:02}'+'_'+C['nome'],None);link(root,'Metadados');root['id_referencia']=id;root['dimensoes_m']=[C['w'],C['d'],C['H']]
    root['interiores']=json.dumps(C['interiores'],ensure_ascii=False);root['instalado_no_fivem']=False
    # Apply supplied flat PNGs and the same refinement used by existing assets.
    import importlib.util
    spec=importlib.util.spec_from_file_location('texturas',ROOT/'scripts'/'aplicar_texturas_fornecidas.py');tex=importlib.util.module_from_spec(spec);spec.loader.exec_module(tex)
    assigned=tex.apply_textures(id,C)
    spec=importlib.util.spec_from_file_location('refinamento',ROOT/'scripts'/'refinar_modelo.py');ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref);ref.apply_polish(sys.modules[__name__])
    path=ROOT/'modelos'/f'{id:02}_{C["nome"]}.blend'
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
    if do_render:
        render(ROOT/'previews'/f'{id:02}_exterior.png');render(ROOT/'previews'/f'{id:02}_interior.png',True)
    data=dict(id=id,nome=C['nome'],arquivo=path.name,dimensoes=[C['w'],C['d'],C['H']],interiores=C['interiores'],aberturas=C['aberturas'],
       objetos=sum(o.type=='MESH' for o in bpy.data.objects),vertices=sum(len(o.data.vertices) for o in bpy.data.objects if o.type=='MESH'),texturas_empacotadas=[i.name for i in bpy.data.images if i.packed_file],texturas_fornecidas=assigned)
    (ROOT/'dados'/f'{id:02}_modelo.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print('MODELO_CONCLUIDO',id,json.dumps(data,ensure_ascii=False),flush=True)

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    ap=argparse.ArgumentParser();ap.add_argument('--ids',default='1,2,3,4,5,6,7,8,9,10');ap.add_argument('--sem-render',action='store_true');opts=ap.parse_args(args)
    for id in map(int,opts.ids.split(',')):generate(id,not opts.sem_render)
    print('BIBLIOTECA_CONCLUIDA',flush=True)
