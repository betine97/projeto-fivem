"""Editable, physically modelled reference bar; no furniture photo billboards."""
import bpy,bmesh,sys,json,math
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parent; W=P.parent; R=W.parent; T=P/'textures'; O=P/'stream';O.mkdir(exist_ok=True)
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
spec=json.loads((P/'spec.json').read_text());styles={};parts=[];solids=[]
col=bpy.data.collections.new(spec['collection']);bpy.context.scene.collection.children.link(col)
for key in ['madeira','arte1','arte2','preto','bronze','creme','ceramica','folha','led','vidro_transparente']:
 preset='emissive.sps' if key=='led' else 'glass.sps' if key=='vidro_transparente' else 'normal_spec.sps'
 m=create_shader(preset);m.name='apar_'+key
 for sampler,txname in [('DiffuseSampler','apar_'+key),('BumpSampler','apar_madeira_n' if key=='madeira' else 'apar_normal'),('SpecSampler','apar_spec_fosco' if key in ['arte1','arte2','folha','creme','ceramica'] else 'apar_spec_metal' if key=='bronze' else 'apar_spec')]:
  node=m.node_tree.nodes.get(sampler)
  if node is None:continue
  im=bpy.data.images.load(str(T/(txname+'.dds')),check_existing=True);im.pack();node.image=im;node.texture_properties.embedded=True
  if sampler!='DiffuseSampler':im.colorspace_settings.name='Non-Color'
  m.node_tree.links.new(m.node_tree.nodes['UVMap 0'].outputs['UV'],node.inputs['Vector'])
 for param,value in [('specularIntensityMult',.5 if key in ['marmore','bronze','vidro'] else .18),('specularFalloffMult',100 if key in ['marmore','bronze','vidro'] else 28),('specularFresnel',.3),('wetnessMultiplier',0),('bumpiness',.15),('emissiveMultiplier',4.0)]:
  if (node:=m.node_tree.nodes.get(param)) is not None:node.set(0,value)
 bsdf=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if bsdf:
  for field,value in [('Roughness',.25 if key in ['marmore','vidro','bronze'] else .60),('Metallic',.65 if key=='bronze' else 0)]:
   for link in list(bsdf.inputs[field].links):m.node_tree.links.remove(link)
   bsdf.inputs[field].default_value=value
  if key=='vidro_transparente':
   for field,value in [('Alpha',1.0),('Transmission Weight',1.0),('Roughness',.055),('IOR',1.45)]:
    if field in bsdf.inputs:
     for link in list(bsdf.inputs[field].links):m.node_tree.links.remove(link)
     bsdf.inputs[field].default_value=value
 em=next((n for n in m.node_tree.nodes if n.type=='EMISSION'),None)
 if em:
  if 'Weight' in em.inputs:
   for link in list(em.inputs['Weight'].links):m.node_tree.links.remove(link)
   em.inputs['Weight'].default_value=1
  m.node_tree.links.new(m.node_tree.nodes['DiffuseSampler'].outputs['Color'],em.inputs['Color'])
 styles[key]=m
def mesh(name,verts,faces,family,uv=None,smooth=False):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 me.materials.append(styles[family]);layer=me.uv_layers.new(name='UVMap 0')
 for poly in me.polygons:
  axes=[i for i in range(3) if i!=int(np.argmax(abs(np.array(poly.normal))))]
  for li in poly.loop_indices:
   idx=me.loops[li].vertex_index;v=me.vertices[idx].co;layer.data[li].uv=uv[idx] if uv else (v[axes[0]],v[axes[1]])
  poly.use_smooth=smooth
 mesh_add_missing_uv_maps(me);mesh_add_missing_color_attrs(me)
 for a in me.color_attributes:a.data.foreach_set('color_srgb',np.tile(np.array([1,1,1,1],np.float32),len(a.data)))
 obj=bpy.data.objects.new(name,me);col.objects.link(obj);parts.append(obj);return obj
def box(name,lo,hi,family='madeira',bevel=.002,collision=False,front_open=False):
 x,y,z=lo;X,Y,Z=hi;verts=[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)]
 faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
 if front_open:faces.remove((0,1,5,4))
 obj=mesh(name,verts,faces,family)
 if family in ['madeira','arte1','arte2']:
  for loop in obj.data.loops:
   v=obj.data.vertices[loop.vertex_index].co;obj.data.uv_layers[0].data[loop.index].uv=((v.x-x)/(X-x),(v.z-z)/(Z-z))
 if bevel:
  mod=obj.modifiers.new('Chanfro real','BEVEL');mod.width=bevel;mod.segments=2;bpy.context.view_layer.objects.active=obj;obj.select_set(True);bpy.ops.object.modifier_apply(modifier=mod.name);obj.select_set(False)
 if collision:solids.append({'name':name,'lo':list(lo),'hi':list(hi)})
 return obj
def lathe(name,profile,center,family,sides=24):
 verts=[];faces=[];uv=[];rings=[]
 for k,(r,z) in enumerate(profile):
  if r==0:rings.append([len(verts)]);verts.append((center[0],center[1],center[2]+z));uv.append((.5,k/len(profile)))
  else:
   rings.append(list(range(len(verts),len(verts)+sides)))
   for i in range(sides):a=i/sides*math.tau;verts.append((center[0]+r*math.cos(a),center[1]+r*math.sin(a),center[2]+z));uv.append((i/sides,k/len(profile)))
 for a,b in zip(rings,rings[1:]):
  for i in range(sides):
   j=(i+1)%sides
   if len(a)==len(b)==1:continue
   if len(a)==1:faces.append((a[0],b[j],b[i]))
   elif len(b)==1:faces.append((a[i],a[j],b[0]))
   else:faces.append((a[i],a[j],b[j],b[i]))
 return mesh(name,verts,faces,family,uv,True)
def bottle(name,x,y,z,h=.32,whisky=False,sides=20):
 r=.038 if not whisky else .048
 profile=[(0,0),(r*.85,0),(r,.008),(r,h*.65),(r*.65,h*.75),(r*.29,h*.78),(r*.29,h*.96),(r*.36,h*.965),(r*.36,h),(0,h)]
 lathe(name+' corpo e gargalo',profile,(x,y,z),'vinho' if not whisky else 'bronze',sides)
 lathe(name+' rotulo',[(r*1.004,h*.23),(r*1.004,h*.57)],(x,y,z),'rotulo',sides)
 lathe(name+' selo',[(r*.365,h*.96),(r*.365,h)],(x,y,z),'preto',sides)
 if whisky:
  box(name+' emblema',(x-.013,y-r-.001,z+h*.35),(x+.013,y-r+.001,z+h*.43),'bronze',0)
def vase(name,x,y,z,h,r,family='ceramica',kind='round'):
 if kind=='bowl':profile=[(0,0),(r*.55,.009),(r*.93,h*.65),(r,h),(r*.95,h),(r*.82,h*.68),(r*.53,.02),(0,.02)]
 elif kind=='narrow':profile=[(0,0),(r*.70,0),(r,.025),(r,h*.55),(r*.53,h*.75),(r*.45,h*.96),(r*.49,h),(r*.39,h),(r*.36,h*.80),(r*.50,h*.68),(r*.80,h*.50),(r*.70,.04),(0,.04)]
 else:profile=[(0,0),(r*.64,0),(r*.98,h*.27),(r,h*.53),(r*.73,h*.72),(r*.4,h*.78),(r*.4,h*.95),(r*.45,h),(r*.35,h),(r*.30,h*.82),(r*.67,h*.65),(r*.85,h*.48),(r*.8,h*.20),(0,.027)]
 return lathe(name,profile,(x,y,z),family,32)
def glass(name,x,y,z):
 profile=[(0,.0),(.041,.002),(.041,.006),(.014,.01),(.005,.021),(.004,.121),(.038,.148),(.046,.192),(.048,.231),(.045,.246),(.043,.246),(.045,.230),(.043,.195),(.034,.154),(.003,.133),(0,.130)]
 return lathe(name,profile,(x,y,z),'vidro_transparente',24)
# Design space: X left-to-right on the marked wall, negative Y toward room.
# An additive fitted ensemble; no replacement of architectural geometry.
def tube(name,pts,r,family='bronze',sides=8):
    for a,b in zip(pts,pts[1:]):
        v=Vector(b)-Vector(a)
        o=lathe(name,[(0,0),(r,0),(r*.8,v.length),(0,v.length)],(0,0,0),family,sides)
        tx=v.to_track_quat('Z','Y').to_matrix().to_4x4()
        for vert in o.data.vertices:vert.co=tx@vert.co+Vector(a)
def frame(name,x0,x1,z0,z1,width=.035):
    for a,b in [((x0,-.042,z0),(x0+width,-.008,z1)),((x1-width,-.042,z0),(x1,-.008,z1)),((x0+width,-.042,z0),(x1-width,-.008,z0+width)),((x0+width,-.042,z1-width),(x1-width,-.008,z1))]:
        box(name,a,b,'creme',.003)
    for a,b in [((x0+width,-.030,z0+width),(x0+width+.009,-.018,z1-width)),((x1-width-.009,-.030,z0+width),(x1-width,-.018,z1-width)),((x0+width,-.030,z0+width),(x1-width,-.018,z0+width+.009)),((x0+width,-.030,z1-width-.009),(x1-width,-.018,z1-width))]:
        box(name+' filete',a,b,'creme',.002)
frame('Boiserie painel quadros',.15,3.42,.15,3.047,.043)
frame('Boiserie porta',3.50,5.53,.05,3.047,.041)
# Three separate moldings above the doorway imitate the reference lintel.
box('Friso sobre porta',(3.55,-.042,2.775),(5.485,-.008,2.814),'creme',.003)
box('Friso superior',(3.55,-.038,2.977),(5.485,-.008,3.012),'creme',.002)
# Floating console, true cabinet structure and four separately beveled fronts.
box('Aparador suspenso corpo',(.29,-.403,.35),(3.30,-.017,.865),'madeira',.004,True)
for j in range(4):
    a=.30+j*.7475
    box('Aparador frente %d'%j,(a,-.422,.363),(a+.738,-.398,.844),'madeira',.003)
box('Aparador tampo',(.275,-.425,.844),(3.315,-.012,.871),'madeira',.003)
box('Perfil luz sob aparador',(.34,-.225,.342),(3.25,-.208,.351),'bronze',.001)
box('LED sob aparador',(.35,-.22,.340),(3.24,-.212,.343),'led',0)
for i,(x0,x1) in enumerate([(.46,1.69),(1.89,3.12)]):
    z0=1.135;z1=2.760
    box('Quadro %d suporte'%i,(x0-.018,-.051,z0-.018),(x1+.018,-.016,z1+.018),'creme',.002)
    box('Quadro %d tela'%i,(x0,-.066,z0),(x1,-.051,z1),'arte'+str(i+1),0)
    for a,b in [((x0-.018,-.082,z0-.018),(x0,-.025,z1+.018)),((x1,-.082,z0-.018),(x1+.018,-.025,z1+.018)),((x0,-.082,z0-.018),(x1,-.025,z0)),((x0,-.082,z1),(x1,-.025,z1+.018))]:box('Quadro moldura bronze %d'%i,a,b,'bronze',.001)
    cx=(x0+x1)/2
    box('Arandela placa %d'%i,(cx-.045,-.071,2.887),(cx+.045,-.01,2.940),'bronze',.002)
    box('Arandela braco %d'%i,(cx-.009,-.175,2.905),(cx+.009,-.065,2.920),'bronze',.002)
    box('Arandela barra %d'%i,(cx-.325,-.192,2.892),(cx+.325,-.159,2.918),'bronze',.003)
    box('Arandela luz %d'%i,(cx-.310,-.183,2.889),(cx+.310,-.166,2.893),'led',0)
# Left branch vase and second small porcelain vessel.
vase('Vaso ramo oliva',.66,-.234,.874,.338,.129,'ceramica')
vase('Vaso ceramica branco',.975,-.258,.874,.248,.087,'creme','narrow')
rng=np.random.default_rng(913)
for k in range(8):
    start=Vector((.66,-.234,1.162))
    end=Vector((.66+rng.uniform(-.46,.32),-.22+rng.uniform(-.12,.13),1.62+rng.uniform(.10,.35)))
    pts=[tuple(start.lerp(end,j/5)+Vector((.025*math.sin(j+k),0,0))) for j in range(6)]
    tube('Ramo oliva',pts,.003,'bronze',6)
    for j in range(2,6):
        p=Vector(pts[j])
        for sign in [-1,1]:
            tip=p+Vector((sign*rng.uniform(.055,.11),rng.uniform(-.025,.025),rng.uniform(-.028,.052)))
            mid=(p+tip)/2;d=tip-p;side=Vector((-d.z,0,d.x)).normalized()*.013
            mesh('Folha oliva',list(map(tuple,[p,mid+side,tip,mid-side])),[(0,1,2,3),(3,2,1,0)],'folha',[(0,0),(.2,.5),(1,1),(.8,.5)],True)
vase('Tigela preta central',1.89,-.244,.874,.161,.244,'preto','bowl')
for j,(w,d) in enumerate([(.43,.24),(.40,.245),(.445,.235)]):
    x=2.73;z=.874+j*.031
    box('Livro paginas '+str(j),(x-w/2,-.31,z+.004),(x+w/2,-.31+d,z+.025),'creme',.001)
    for zz in [z,z+.025]:box('Livro capa '+str(j),(x-w/2-.003,-.314,zz),(x+w/2+.003,-.31+d+.002,zz+.004),'ceramica',.0008)
vase('Objeto ceramico redondo',2.73,-.215,.97,.135,.074,'creme')
for k in range(4):tube('Ramo pequeno ceramica',[(2.73,-.215,1.102),(2.725+k*.009,-.213,1.165+k*.01)],.0015,'bronze',5)
# Door frame fits the existing 1.1 m opening; the leaf is a separate model.
for a,b in [((3.64,-.060,0),(3.684,.20,2.5)),((4.696,-.060,0),(4.74,.20,2.5)),((3.684,-.060,2.455),(4.696,.20,2.5))]:box('Batente madeira porta',a,b,'madeira',.003,True)
box('Rebaixo escuro acima folha',(3.684,-.021,2.431),(4.696,.030,2.456),'preto',.001)
# The wall molding follows the jamb; it must not run across the door opening.
for o in list(parts):
    if o.name.startswith('Boiserie porta'):
        ps=[v.co for v in o.data.vertices]
        if max(p.z for p in ps)<.16 and min(p.x for p in ps)<3.64 and max(p.x for p in ps)>4.74:
            parts.remove(o);bpy.data.objects.remove(o,do_unlink=True)
for a,b in [((3.541,-.042,.05),(3.64,-.008,.091)),((4.74,-.042,.05),(5.489,-.008,.091))]:box('Boiserie rodape lateral porta',a,b,'creme',.003)
fixed_parts=list(parts);fixed_solids=list(solids)
# Leave 85 mm clearance beyond the perpendicular wine cabinet's 647 mm depth.
panel_s=(3.42-.72)/(3.42-.15)
for o in fixed_parts:
    if o.name.startswith(('Boiserie porta','Friso sobre porta','Friso superior','Batente madeira porta')):continue
    for v in o.data.vertices:v.co.x=.72+(v.co.x-.15)*panel_s
    o.data.update()
for q in fixed_solids:
    if q['name'].startswith('Aparador'):
        q['lo'][0]=.72+(q['lo'][0]-.15)*panel_s;q['hi'][0]=.72+(q['hi'][0]-.15)*panel_s
parts.clear();solids.clear()
# Door in design coordinates; negative X from the right-hand hinge in export.
left=3.684;right=4.696;z0=.015;z1=2.442;glass0=4.19;glass1=4.423;g0=.218;g1=2.290
for name,a,b in [('Folha madeira esquerda',(left,-.0225,z0),(glass0,.0225,z1)),('Folha madeira direita',(glass1,-.0225,z0),(right,.0225,z1)),('Folha madeira base vidro',(glass0,-.0225,z0),(glass1,.0225,g0)),('Folha madeira topo vidro',(glass0,-.0225,g1),(glass1,.0225,z1))]:box(name,a,b,'madeira',.002,True)
for a,b in [((glass0-.014,-.026,g0-.014),(glass0,-.022,g1+.014)),((glass1,-.026,g0-.014),(glass1+.014,-.022,g1+.014)),((glass0,-.026,g0-.014),(glass1,-.022,g0)),((glass0,-.026,g1),(glass1,-.022,g1+.014))]:box('Perfil preto visor',a,b,'preto',.001)
box('Visor vidro fumado',(glass0,-.004,g0),(glass1,.004,g1),'vidro_transparente',0,True)
for sign in [-1,1]:
    a=sorted([sign*.042,sign*.024]);b=sorted([sign*.070,sign*.054])
    for z in [.87,1.32]:box('Puxador suporte',(left+.071,a[0],z),(left+.09,a[1],z+.024),'preto',.002)
    box('Puxador vertical',(left+.069,b[0],.860),(left+.092,b[1],1.358),'preto',.005)
for z in [.18,1.19,2.2]:box('Dobradiça preta',(right-.017,-.018,z),(right+.007,.040,z+.073),'preto',.002)
door_parts=list(parts);door_solids=list(solids);parts[:]=fixed_parts+door_parts
spec['parts']=len(parts);spec['collision_boxes']=fixed_solids;spec['door_collision_boxes']=door_solids
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'parede_aparador_editavel.blend'),compress=True)
tx=Matrix(((0,1,0,14.168),(-1,0,0,-.98),(0,0,1,-.8),(0,0,0,1)))
def export_group(srcparts,model,transform):
    root=bpy.data.objects.new(model,None);bpy.context.scene.collection.objects.link(root);root.sollum_type=SollumType.DRAWABLE;out=[]
    for src in srcparts:
        me=src.data.copy();me.transform(transform);me.update();obj=bpy.data.objects.new(src.name+'_export',me);bpy.context.scene.collection.objects.link(obj);obj.parent=root;convert_obj_to_model(obj);out.append(obj)
    pts=np.array([v.co for o in out for v in o.data.vertices]);bounds={'lo':pts.min(0).tolist(),'hi':pts.max(0).tolist()}
    with export_context_scope(ExportContext(model,ExportSettings(targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)))):export_ydr(root).save(O,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),))
    for ratio,suffix in [(.6,'medium'),(.25,'low'),(.10,'verylow')]:
        bpy.ops.object.select_all(action='DESELECT');copies=[]
        for src in out:
            obj=src.copy();obj.data=src.data.copy();bpy.context.scene.collection.objects.link(obj);obj.parent=None;obj.select_set(True);copies.append(obj)
        bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();obj=bpy.context.object
        dec=obj.modifiers.new('LOD simplificado','DECIMATE');dec.ratio=ratio;dec.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=dec.name)
        name=model+'_'+suffix;lr=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(lr);lr.sollum_type=SollumType.DRAWABLE;obj.parent=lr;convert_obj_to_model(obj)
        with export_context_scope(ExportContext(name,ExportSettings(targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)))):export_ydr(lr).save(O,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),))
        bpy.data.objects.remove(obj,do_unlink=True);bpy.data.objects.remove(lr,do_unlink=True)
    return bounds
spec['fixed_bounds']=export_group(fixed_parts,spec['model'],tx)
spec['door_bounds']=export_group(door_parts,spec['door_model'],Matrix.Translation(-Vector(spec['door_hinge_local'])))
spec['door_hinge_house']=list(tx@Vector(spec['door_hinge_local']))
(P/'spec.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
print('APARADOR_BUILT',spec['parts'],spec['fixed_bounds'],spec['door_hinge_house'],flush=True)
