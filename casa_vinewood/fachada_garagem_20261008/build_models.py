import bpy,bmesh,sys,json,math
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent;T=P/'textures';O=P/'stream'
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
spec=json.loads((P/'spec.json').read_text());styles={};groups={n:[] for n in spec['models']};collisions={n:[] for n in spec['models']};active=spec['models'][0]
col=bpy.data.collections.new(spec['collection']);bpy.context.scene.collection.children.link(col)
for key,diff,norm,sp in [('tijolo','os_ml_idwall_0005_c','os_ml_idwall_0005_n','fach_spec'),('reboco','im_wall32','im_wall32_n','im_wall32_s')]+[(k,'fach_'+k,'fach_normal','fach_spec_metal' if k=='bronze' else 'fach_spec') for k in ['madeira','preto','bronze','vidro_transparente','creme','cimento','sinal','led','led_branco']]:
    preset='emissive.sps' if key.startswith('led') else 'glass.sps' if key=='vidro_transparente' else 'normal_spec.sps';m=create_shader(preset);m.name='entrada_'+key
    for sampler,name in [('DiffuseSampler',diff),('BumpSampler',norm),('SpecSampler',sp)]:
        node=m.node_tree.nodes.get(sampler)
        if node:
            im=bpy.data.images.load(str(T/(name+'.dds')),check_existing=True);im.pack();node.image=im;node.texture_properties.embedded=True
            if sampler!='DiffuseSampler':im.colorspace_settings.name='Non-Color'
            m.node_tree.links.new(m.node_tree.nodes['UVMap 0'].outputs['UV'],node.inputs['Vector'])
    for name,val in [('wetnessMultiplier',0),('specularIntensityMult',.25 if key in ['bronze','preto'] else .08),('specularFalloffMult',80 if key in ['bronze','preto'] else 22),('bumpiness',.22),('emissiveMultiplier',2.0)]:
        node=m.node_tree.nodes.get(name)
        if node:node.set(0,val)
    styles[key]=m
def mesh(name,verts,faces,key,solid=False,smooth=False):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.materials.append(styles[key]);uv=me.uv_layers.new(name='UVMap 0')
    for p in me.polygons:
        axes=[i for i in range(3) if i!=int(np.argmax(abs(np.array(p.normal))))]
        for li in p.loop_indices:
            v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v[axes[0]]*.5,v[axes[1]]*.5)
            if key=='tijolo':
                u=-.2138*v.x-4.6396 if abs(p.normal.y)>.5 else -.2138*3.645-4.6396+.2138*(v.y-9.816895)
                uv.data[li].uv=(u,-.25018*v.z-1.05572)
        p.use_smooth=smooth
    mesh_add_missing_uv_maps(me);mesh_add_missing_color_attrs(me)
    for a in me.color_attributes:a.data.foreach_set('color_srgb',np.tile(np.array([1,1,1,1],np.float32),len(a.data)))
    obj=bpy.data.objects.new(name,me);col.objects.link(obj);groups[active].append(obj)
    if solid:
        me.calc_loop_triangles();collisions[active].append({'name':name,'vertices':[list(v.co) for v in me.vertices],'triangles':[list(t.vertices) for t in me.loop_triangles],'material':'GLASS_SHOOT_THROUGH' if key=='vidro_transparente' else 'CONCRETE' if key not in ['madeira','preto','bronze'] else 'WOOD_SOLID_MEDIUM' if key=='madeira' else 'METAL_SOLID_MEDIUM'})
    return obj
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def box(name,lo,hi,key='reboco',solid=False,bevel=.0):
    x,y,z=lo;X,Y,Z=hi;obj=mesh(name,[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)],faces,key,solid)
    if bevel:
        mod=obj.modifiers.new('Chanfro real','BEVEL');mod.width=bevel;mod.segments=2;bpy.context.view_layer.objects.active=obj;obj.select_set(True);bpy.ops.object.modifier_apply(modifier=mod.name);obj.select_set(False)
    return obj
def slab_wedge(name,x0,x1,y0,y1,z00,z10,z01,z11,key,solid=True,depth=.18):
    top=[(x0,y0,z00),(x1,y0,z10),(x1,y1,z11),(x0,y1,z01)];return mesh(name,[(x,y,z-depth) for x,y,z in top]+top,faces,key,solid)
# Complete the marked brick return, stopping beyond the existing stair landing.
box('Extensao tijolo no recuo',*spec['brick_extension'],'tijolo',True)
box('Capa fina muro ampliado',(1.04,5.92,2.80762),(3.66,9.832,2.835),'creme',True)
for lo,hi in [((3.865,7.26,-.80),(3.98,7.66,2.265)),((5.31,7.26,-.80),(5.455,7.66,2.265)),((3.98,7.26,2.20),(5.31,7.66,2.265))]:box('Portal entrada pedra',lo,hi,'creme',True,.008)
box('Soleira entrada',(3.865,7.10,-.82),(5.455,7.83,-.795),'creme',True)
for x in [3.84,5.485]:
    box('Arandela entrada corpo',(x-.045,7.635,.62),(x+.045,7.72,1.08),'preto',False,.005)
    box('Arandela entrada difusor',(x-.025,7.724,.665),(x+.025,7.729,1.035),'led')
# A street-matched apron and thirteen separate treads keep the stairs traversable.
def street(x):return -2.942-(x-4.5)*.1205
for i in range(13):
    t=(i+1)/13;y1=18.50-i*.30;y0=y1-.30
    zl=street(3.64)*(1-t)+(-.8)*t;zr=street(5.85)*(1-t)+(-.8)*t
    slab_wedge('Entrada degrau %02d'%(i+1),3.64,5.85,y0,y1,zl,zr,zl,zr,'creme',True,.18)
    slab_wedge('LED degrau %02d'%(i+1),3.68,5.81,y1-.012,y1-.006,zl-.047,zr-.047,zl-.036,zr-.036,'led',False,.002)
slab_wedge('Patamar inferior encaixado rua',3.64,5.85,18.50,19.22,street(3.64),street(5.85),street(3.64),street(5.85),'creme',True,.12)
box('Patamar chegada entrada',(3.63,13.95,-.96),(5.86,14.60,-.8),'creme',True)
# Small low side guards finish the cut edges; the original landscape remains outside.
for x in [3.62,5.85]:
    for j in range(6):
        y0=14.55+j*.66;y1=min(18.5,y0+.66);t=(18.5-y0)/3.9;zt=street(x)*(1-t)-.8*t
        box('Mureta escada externa',(x-.075,y0,-3.33),(x+.025,y1,zt+.25),'reboco',True)
# The garage has actual room, ceiling, ramp and vehicle collision, below the floor slab.
active=spec['models'][1]
box('Garagem piso',(6.13,-1.96,-4.42),(13.06,9.57,-4.20),'cimento',True)
box('Garagem teto',(6.13,-1.96,-1.28),(13.06,9.57,-1.095),'reboco',True)
box('Garagem parede esquerda',(6.13,-1.96,-4.22),(6.40,9.58,-1.095),'reboco',True)
box('Garagem parede direita',(12.80,-1.96,-4.22),(13.06,9.58,-1.095),'reboco',True)
box('Garagem fundo',(6.13,-1.96,-4.22),(13.06,-1.70,-1.095),'reboco',True)
box('Portao viga superior',(6.13,9.35,-1.43),(13.06,9.58,-1.095),'reboco',True)
for x in [6.14,12.8]:box('Portao batente',(x,9.35,-4.20),(x+.26,9.58,-1.43),'preto',True)
# Grade changes flatten at the door and blend into the real cross-fall of the street.
def endroad(x):return -3.159-(x-6.4)*.1205
def rampz(x,y):
    t=max(0,min(1,(y-9.55)/(19.22-9.55)));s=t*t*(3-2*t);return -4.20+(endroad(x)+4.20)*s
for j in range(20):
    y0=9.55+j*(19.22-9.55)/20;y1=9.55+(j+1)*(19.22-9.55)/20
    slab_wedge('Rampa transicao %02d'%j,6.40,12.80,y0,y1,rampz(6.4,y0),rampz(12.8,y0),rampz(6.4,y1),rampz(12.8,y1),'cimento',True,.16)
    for x0,x1 in [(6.145,6.40),(12.80,13.055)]:
        def top(x,y):
            t=max(0,min(1,(y-9.55)/(18.6-9.55)));return -.47*(1-t)+(endroad(x)+.75)*t
        mesh('Muro contencao rampa %02d'%j,[(x0,y0,rampz(x0,y0)-.3),(x1,y0,rampz(x1,y0)-.3),(x1,y1,rampz(x1,y1)-.3),(x0,y1,rampz(x0,y1)-.3),(x0,y0,top(x0,y0)),(x1,y0,top(x1,y0)),(x1,y1,top(x1,y1)),(x0,y1,top(x0,y1))],faces,'reboco',True)
for y in [9.72,18.85]:
    slab_wedge('Grelha drenagem',6.41,12.79,y,y+.11,rampz(6.41,y)+.006,rampz(12.79,y)+.006,rampz(6.41,y+.11)+.006,rampz(12.79,y+.11)+.006,'preto',False,.012)
    for x in np.arange(6.45,12.75,.15):slab_wedge('Rasgo grelha',x,x+.045,y+.009,y+.102,rampz(x,y)+.009,rampz(x+.045,y)+.009,rampz(x,y+.102)+.009,rampz(x+.045,y+.102)+.009,'cimento',False,.001)
for y in [11,13.6,16.2,18.1]:
    for x in [6.414,12.781]:
        z=rampz(x,y)+.65;box('Balizador rampa corpo',(x-.012,y-.12,z-.075),(x+.012,y+.12,z+.075),'preto')
        box('Balizador rampa emissor',(x-.017,y-.09,z-.045),(x+.017,y+.09,z+.045),'led')
for x in [6.70,9.58,12.49]:box('Demarcacao vaga',(x,-1.22,-4.194),(x+.065,4.65,-4.189),'sinal')
for x in [6.70,9.64]:box('Limite traseiro vaga',(x,-1.22,-4.194),(x+2.78,-1.15,-4.189),'sinal')
for x in [8.12,11.00]:
    box('Batente roda',(x-.6,-.82,-4.20),(x+.6,-.66,-4.07),'preto',True,.025)
for x in [7.9,11.2]:
    for y in [.2,3.5,6.8]:
        box('Luminaria garagem perfil',(x-.035,y-.65,-1.315),(x+.035,y+.65,-1.281),'preto')
        box('Luminaria garagem LED',(x-.025,y-.63,-1.318),(x+.025,y+.63,-1.312),'led_branco')
for x in [6.45,12.745]:
    box('Rodape garagem',(x,-1.62,-4.19),(x+.055,9.24,-4.035),'preto')
# Door pivots inside the vestibule; glass is a true separate transparent surface.
active=spec['models'][2];h=np.array(spec['door_hinge']);x,y,z=h;w=spec['door_width'];height=spec['door_height'];g0=x+.86;g1=x+1.085
for lo,hi in [((x,y-.029,z),(g0,y+.029,z+height)),((g1,y-.029,z),(x+w,y+.029,z+height)),((g0,y-.029,z),(g1,y+.029,z+.15)),((g0,y-.029,z+height-.15),(g1,y+.029,z+height))]:box('Porta principal madeira',lo,hi,'madeira',True,.003)
box('Porta principal visor',(g0,y-.006,z+.15),(g1,y+.006,z+height-.15),'vidro_transparente',True)
for xx in [g0-.012,g1]:box('Visor perfil preto',(xx,y-.031,z+.136),(xx+.012,y+.031,z+height-.136),'preto')
for zz in [z+.14,z+height-.14]:box('Visor perfil horizontal',(g0,y-.031,zz),(g1,y+.031,zz+.012),'preto')
for yy in [y-.063,y+.063]:box('Puxador entrada',(x+1.20,yy-.014,z+.78),(x+1.222,yy+.014,z+1.48),'preto',False,.003)
for zz in [z+.20,z+1.46,z+2.70]:box('Dobradica entrada',(x-.009,y-.034,zz),(x+.014,y+.034,zz+.07),'preto')
# Up-and-over leaf opens inward, under the garage ceiling rather than through the house.
active=spec['models'][3];h=np.array(spec['gate_hinge']);x,y,z=h;half=spec['gate_width']/2;gh=spec['gate_height']
box('Portao painel estrutural',(x-half,y-.036,z-gh),(x+half,y+.036,z),'preto',True,.012)
for i in range(8):
    zz=z-gh+i*gh/8
    box('Portao friso horizontal',(x-half+.025,y+.038,zz+.006),(x+half-.025,y+.044,zz+.017),'cimento')
box('Portao puxador',(x-.16,y+.048,z-gh+.82),(x+.16,y+.067,z-gh+.844),'preto',False,.004)
spec['collision_meshes']=collisions;spec['parts']={k:len(v) for k,v in groups.items()}
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene['origem_gta']=spec['origin'];scene['projeto']='Entrada no X, muro ampliado e garagem subterranea; escala em metros.'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'fachada_garagem_editavel.blend'),compress=True)
def export_group(objects,model,transform):
    root=bpy.data.objects.new(model,None);scene.collection.objects.link(root);root.sollum_type=SollumType.DRAWABLE;out=[]
    # Join by material before export: architecture stays in a small number of draw calls.
    buckets={}
    for obj in objects:buckets.setdefault(obj.data.materials[0].name,[]).append(obj)
    for batch in buckets.values():
        bpy.ops.object.select_all(action='DESELECT');copies=[]
        for src in batch:
            me=src.data.copy();me.transform(transform);obj=bpy.data.objects.new(src.name+'_export',me);scene.collection.objects.link(obj);obj.select_set(True);copies.append(obj)
        bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();obj=bpy.context.object;obj.parent=root;convert_obj_to_model(obj);out.append(obj)
    pts=np.array([v.co for obj in out for v in obj.data.vertices]);bounds={'lo':pts.min(0).tolist(),'hi':pts.max(0).tolist()}
    targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
    with export_context_scope(ExportContext(model,ExportSettings(targets=targets))):export_ydr(root).save(O,targets)
    for ratio,suffix in [(.65,'medium'),(.35,'low'),(.20,'verylow')]:
        lr=bpy.data.objects.new(model+'_'+suffix,None);scene.collection.objects.link(lr);lr.sollum_type=SollumType.DRAWABLE;copies=[]
        for src in out:
            obj=src.copy();obj.data=src.data.copy();scene.collection.objects.link(obj);obj.parent=lr;copies.append(obj);bpy.context.view_layer.objects.active=obj
            dec=obj.modifiers.new('LOD','DECIMATE');dec.ratio=ratio;dec.use_collapse_triangulate=True;obj.select_set(True);bpy.ops.object.modifier_apply(modifier=dec.name);obj.select_set(False)
        with export_context_scope(ExportContext(lr.name,ExportSettings(targets=targets))):export_ydr(lr).save(O,targets)
        for obj in copies:bpy.data.objects.remove(obj,do_unlink=True)
        bpy.data.objects.remove(lr,do_unlink=True)
    for obj in out:bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.objects.remove(root,do_unlink=True);return bounds
spec['bounds']={}
for name,objects in groups.items():
    off=spec['door_hinge'] if name==spec['models'][2] else spec['gate_hinge'] if name==spec['models'][3] else [0,0,0]
    spec['bounds'][name]=export_group(objects,name,Matrix.Translation(-Vector(off)))
(P/'spec.json').write_text(json.dumps(spec,indent=2))
print('FACADE_GARAGE_MODELS_READY',spec['parts'],flush=True)
