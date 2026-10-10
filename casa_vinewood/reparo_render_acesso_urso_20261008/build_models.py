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
# Thirteen full-depth treads, set back to the measured diagonal street edge.
def edge(x): return 16.235 + .173*x
def street(x): return -2.7435 - (x-3.64)*.1145
def garden_grade(y):return -.75-.41*min(1.,max(0.,(y-15.1)/1.2))
def quad_slab(name,x0,x1,t0,t1,z00,z10,z01,z11,key,solid=True,depth=.18):
    top=[(x0,t0(x0),z00),(x1,t0(x1),z10),(x1,t1(x1),z11),(x0,t1(x0),z01)]
    return mesh(name,[(x,y,z-depth) for x,y,z in top]+top,faces,key,solid)
for i in range(13):
    t=(i+1)/13
    y1=lambda x,i=i:edge(x)-.30-i*.30
    y0=lambda x,i=i:y1(x)-.30
    zl=street(3.64)*(1-t)-.8*t;zr=street(5.85)*(1-t)-.8*t
    quad_slab('Entrada degrau %02d'%(i+1),3.64,5.85,y0,y1,zl,zr,zl,zr,'creme',True,.18)
    quad_slab('LED degrau %02d'%(i+1),3.68,5.81,lambda x:y1(x)-.012,lambda x:y1(x)-.006,zl-.047,zr-.047,zl-.036,zr-.036,'led',False,.002)
quad_slab('Patamar inferior dentro calcada',3.64,5.85,lambda x:edge(x)-.30,edge,street(3.64),street(5.85),street(3.64),street(5.85),'creme',True,.12)
quad_slab('Patamar chegada entrada',3.63,5.86,lambda x:12.39,lambda x:edge(x)-4.20,-.8,-.8,-.8,-.8,'creme',True,.16)
# Closed retaining cheeks follow the same diagonal as the treads. Their tops
# retain the existing garden grade instead of falling below it at the street.
for x0,x1 in [(3.47,3.64),(5.85,6.145)]:
    for j in range(13):
        t=(j+1)/13
        y1=lambda x,j=j:edge(x)-.30-j*.30
        y0=lambda x,j=j:y1(x)-.30
        z0=max(street(x0)*(1-t)-.8*t+.20,garden_grade(y0(x0)))
        z1=max(street(x1)*(1-t)-.8*t+.20,garden_grade(y0(x1)))
        top=[(x0,y0(x0),z0),(x1,y0(x1),z1),(x1,y1(x1),z1),(x0,y1(x0),z0)]
        mesh('Contencao fechada escada %02d'%j,[(x,y,-3.45) for x,y,z in top]+top,faces,'reboco',True)
        quad_slab('Capa contencao escada %02d'%j,x0,x1,y0,y1,z0+.028,z1+.028,z0+.028,z1+.028,'creme',True,.028)
    quad_slab('Fecho chegada contencao escada',x0,x1,lambda x:12.39,lambda x:edge(x)-4.20,-.60,-.60,-.60,-.60,'reboco',True,2.85)
    quad_slab('Capa chegada contencao escada',x0,x1,lambda x:12.39,lambda x:edge(x)-4.20,-.572,-.572,-.572,-.572,'creme',True,.028)
    # Seal the apron side up to the boundary without extending into traffic.
    quad_slab('Fecho inferior contencao escada',x0,x1,lambda x:edge(x)-.30,edge,-1.16,-1.16,-1.16,-1.16,'reboco',True,2.29)
    quad_slab('Capa inferior contencao escada',x0,x1,lambda x:edge(x)-.30,edge,-1.132,-1.132,-1.132,-1.132,'creme',True,.028)
# End faces of the native upper/lower garden walls were exposed by the cuts.
# Thin solid finishes close them without entering the stairs or driveway.
for x,y0,y1,top in [(3.30,14.59,15.10,-.166),(3.47,16.30,16.81,-1.175),(13.08,14.59,15.10,-.166),(13.08,17.98,18.46,-1.175)]:
    box('Fecho extremidade muro jardim',(x-.016,y0,-4.22),(x+.016,y1,top-.070),'reboco',True)
    box('Capa extremidade muro jardim',(x-.016,y0,top-.070),(x+.016,y1,top+.008),'creme',True)
# The garage has actual room, ceiling, ramp and vehicle collision, below the floor slab.
active=spec['models'][1]
box('Garagem piso',(6.13,-1.96,-4.42),(13.06,9.57,-4.20),'cimento',True)
box('Garagem teto',(6.13,-1.96,-1.28),(13.06,9.57,-1.095),'reboco',True)
box('Garagem parede esquerda',(6.13,-1.96,-4.22),(6.40,9.58,-1.095),'reboco',True)
box('Garagem parede direita',(12.80,-1.96,-4.22),(13.06,9.58,-1.095),'reboco',True)
box('Garagem fundo',(6.13,-1.96,-4.22),(13.06,-1.70,-1.095),'reboco',True)
box('Portao viga superior',(6.13,9.35,-1.43),(13.06,9.58,-1.095),'reboco',True)
box('Fecho laje superior portao',(6.13,9.35,-1.10),(13.08,9.58,-.78),'reboco',True)
for x in [6.14,12.8]:box('Portao batente',(x,9.35,-4.20),(x+.26,9.58,-1.43),'preto',True)
# A diagonal, flush approach; ease the slope without a tall lip in traffic.
def endroad(x):return -3.0606-(x-6.4)*.1126
def rampz(x,t):
    a=.12
    s=t*t/(2*a*(1-a)) if t<a else 1-(1-t)**2/(2*a*(1-a)) if t>1-a else (t-a/2)/(1-a)
    return -4.20+(endroad(x)+4.20)*s
def ry(x,t):return 9.55+(edge(x)-9.55)*t
for j in range(24):
    t0=j/24;t1=(j+1)/24
    quad_slab('Rampa transicao %02d'%j,6.4,12.8,lambda x:ry(x,t0),lambda x:ry(x,t1),rampz(6.4,t0),rampz(12.8,t0),rampz(6.4,t1),rampz(12.8,t1),'cimento',True,.16)
    for x0,x1 in [(6.13,6.40),(12.80,13.08)]:
        def top(x,t):return max(-.47-.775*t,garden_grade(ry(x,t)))
        verts=[(x0,ry(x0,t0),rampz(x0,t0)-.30),(x1,ry(x1,t0),rampz(x1,t0)-.30),(x1,ry(x1,t1),rampz(x1,t1)-.30),(x0,ry(x0,t1),rampz(x0,t1)-.30),(x0,ry(x0,t0),top(x0,t0)),(x1,ry(x1,t0),top(x1,t0)),(x1,ry(x1,t1),top(x1,t1)),(x0,ry(x0,t1),top(x0,t1))]
        mesh('Muro contencao rampa %02d'%j,verts,faces,'reboco',True)
        quad_slab('Capa contencao rampa %02d'%j,x0,x1,lambda x:ry(x,t0),lambda x:ry(x,t1),top(x0,t0)+.035,top(x1,t0)+.035,top(x0,t1)+.035,top(x1,t1)+.035,'creme',True,.035)
for t in [.023,.975]:
    quad_slab('Grelha drenagem',6.41,12.79,lambda x:ry(x,t),lambda x:ry(x,t+.012),rampz(6.41,t)+.004,rampz(12.79,t)+.004,rampz(6.41,t+.012)+.004,rampz(12.79,t+.012)+.004,'preto',False,.01)
for t in [.18,.42,.66]:
    for x in [6.414,12.781]:
        y=ry(x,t);z=rampz(x,t)+.45
        box('Balizador rampa corpo',(x-.012,y-.12,z-.075),(x+.012,y+.12,z+.075),'preto')
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
    if name not in spec['models'][:2]: continue
    off=spec['door_hinge'] if name==spec['models'][2] else spec['gate_hinge'] if name==spec['models'][3] else [0,0,0]
    spec['bounds'][name]=export_group(objects,name,Matrix.Translation(-Vector(off)))
(P/'spec.json').write_text(json.dumps(spec,indent=2))
print('FACADE_GARAGE_MODELS_READY',spec['parts'],flush=True)
