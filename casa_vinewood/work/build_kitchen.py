import bpy,bmesh,sys,json,math
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=W/'source_assets/cozinha_completa';OUT=W/'cozinha_fivem';OUT.mkdir(exist_ok=True)
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
col=bpy.data.collections.new('Cozinha completa - pecas editaveis');bpy.context.scene.collection.children.link(col);parts=[];solids=[];styles={}
for family in ('wood','marble','greige','black','steel','stone','darkwood','microwave','oven','led'):
 m=create_shader('emissive.sps' if family=='led' else 'normal_spec.sps');m.name='cozinha_'+family
 for sampler,suffix in [('DiffuseSampler','d'),('BumpSampler','n'),('SpecSampler','s')]:
  tx=m.node_tree.nodes.get(sampler)
  if tx is None:continue
  im=bpy.data.images.load(str(D/(family+'_'+suffix+'.dds')),check_existing=True)
  if suffix!='d':im.colorspace_settings.name='Non-Color'
  assert len(im.pixels)>0;im.pack();tx.image=im;tx.texture_properties.embedded=True
  m.node_tree.links.new(m.node_tree.nodes['UVMap 0'].outputs['UV'],tx.inputs['Vector'])
 for param,value in [('specularIntensityMult',.65 if family=='steel' else .35),('specularFalloffMult',100 if family in ('steel','black','stone') else 30),('specularFresnel',.3),('wetnessMultiplier',0),('bumpiness',.25),('emissiveMultiplier',4)]:
  node=m.node_tree.nodes.get(param)
  if node is not None:node.set(0,value)
 styles[family]=m
def mesh(name,verts,faces,family,uv=None):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 me.materials.append(styles[family]);layer=me.uv_layers.new(name='UVMap 0')
 for p in me.polygons:
  n=p.normal;axis=int(np.argmax(abs(np.array(n))));coords=[k for k in range(3) if k!=axis]
  for li in p.loop_indices:
   idx=me.loops[li].vertex_index;v=me.vertices[idx].co;layer.data[li].uv=uv[idx] if uv is not None else (v[coords[0]],v[coords[1]])
  p.use_smooth=False
 mesh_add_missing_uv_maps(me);mesh_add_missing_color_attrs(me)
 for a in me.color_attributes:a.data.foreach_set('color_srgb',np.tile(np.array([1,1,1,1],np.float32),len(a.data)))
 o=bpy.data.objects.new(name,me);col.objects.link(o);parts.append(o);return o
def box(name,lo,hi,family,bevel=.002,collision=False):
 x,y,z=lo;X,Y,Z=hi;v=[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)];faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
 o=mesh(name,v,faces,family)
 if family in ('wood','microwave','oven'):
  for p in o.data.polygons:
   for li in p.loop_indices:
    co=o.data.vertices[o.data.loops[li].vertex_index].co;o.data.uv_layers[0].data[li].uv=((co.x-x)/(X-x), (co.z-z)/(Z-z))
 if bevel:
  mod=o.modifiers.new('Bordas arredondadas reais','BEVEL');mod.width=bevel;mod.segments=3;mod.affect='EDGES'
  bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.modifier_apply(modifier=mod.name);o.select_set(False)
 if collision:solids.append({'name':name,'lo':lo,'hi':hi})
 return o
def tube(name,points,radius,family,sides=12):
 v=[];f=[];uv=[]
 for k,q in enumerate(points):
  p=Vector(q);t=(Vector(points[min(k+1,len(points)-1)])-Vector(points[max(k-1,0)])).normalized();a=t.cross(Vector((1,0,0)))
  if a.length<.01:a=t.cross(Vector((0,0,1)))
  a.normalize();b=t.cross(a).normalized()
  for i in range(sides):
   ang=i/sides*math.tau;v.append(p+radius*(a*math.cos(ang)+b*math.sin(ang)));uv.append((i/sides,k*.1))
 for k in range(len(points)-1):
  for i in range(sides):a=k*sides+i;b=k*sides+(i+1)%sides;f.append((a,b,b+sides,a+sides))
 f.append(tuple(range(sides-1,-1,-1)));f.append(tuple((len(points)-1)*sides+i for i in range(sides)))
 o=mesh(name,v,f,family,uv)
 for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
 return o
def cylinder(name,u,v,h,r,depth,family):return tube(name,[(u,v,h),(u,v,h+depth)],r,family,32)
# Local X is left to right. The front faces the room (negative local Y).
# Tall appliance column at the left; useful lengths are 0.75 + 4.70 + 1.05 m.
box('Torre esquerda caixa',(.0,.04,.06),(.75,.64,3.03),'wood',.004,True)
box('Lateral madeira esquerda',(-.018,.03,0),(.012,.640,3.03),'wood',.003)
box('Torre rodape',(.018,-.004,.02),(.732,.10,.12),'darkwood')
box('Torre gaveta inferior',(.018,-.022,.13),(.732,.02,.59),'greige',.003)
box('Forno vidro e moldura inox',(.07,-.035,.64),(.68,.015,1.21),'oven',.005)
box('Puxador forno suportes',(.11,-.083,1.026),(.13,-.035,1.048),'black')
box('Puxador forno suportes 2',(.61,-.083,1.026),(.63,-.035,1.048),'black')
box('Puxador forno inox',(.112,-.103,1.027),(.628,-.073,1.051),'steel',.008)
box('Microondas embutido',(.07,-.035,1.28),(.68,.012,1.65),'microwave',.004)
box('Torre porta madeira superior',(.018,-.022,1.73),(.732,.02,3.02),'wood',.003)
for z in (.61,1.23,1.68):box('Separador torre '+str(z),(.012,-.008,z),(.738,.08,z+.018),'black')
# Lower cases: actual 18 mm walls, visible gaps and recessed plinth.
start=.75;end=5.45;N=8;step=(end-start)/N
box('Rodape recuado continuo',(start,.10,.015),(end,.62,.12),'darkwood',.002)
box('Fundo armarios inferiores',(start,.61,.12),(end,.64,.88),'greige')
box('Base armarios inferiores',(start,.055,.12),(end,.64,.138),'greige',collision=True)
for j in range(N+1):
 u=start+j*step;box('Divisoria inferior %02d'%j,(u-.009,.04,.125),(u+.009,.64,.88),'greige',collision=True)
for j in range(N):
 u=start+j*step
 for k,(a,b) in enumerate(((.14,.502),(.506,.873))):box('Gaveta greige %02d %d'%(j,k),(u+.007,-.021,a),(u+step-.007,.025,b),'greige',.003)
 # Simple cabinet collision has closed fronts, not hollow back faces that can trap a player.
 solids.append({'name':'Armario inferior '+str(j),'lo':(u,-.021,.12),'hi':(u+step,.64,.89)})
# Countertop is split around a real sink cutout.
su=4.03;sw=.60;sv=.325;sd=.40;za=.882;zb=.913
for name,lo,hi in [('Bancada esquerda',(start,-.045,za),(su-sw/2,.640,zb)),('Bancada direita',(su+sw/2,-.045,za),(end,.640,zb)),('Bancada frente cuba',(su-sw/2,-.045,za),(su+sw/2,sv-sd/2,zb)),('Bancada atras cuba',(su-sw/2,sv+sd/2,za),(su+sw/2,.640,zb))]:box(name,lo,hi,'stone',.0025,True)
box('Revestimento marmore atras bancada',(start,.620,.913),(end,.644,1.67),'marble',.002)
# Sink cavity: dark metal bottom and four sloping, separated sides; no top covering it.
x0=su-sw/2;x1=su+sw/2;y0=sv-sd/2;y1=sv+sd/2
box('Fundo cuba real',(x0+.025,y0+.025,.707),(x1-.025,y1-.025,.723),'black',.009)
for name,v,f in [('Cuba lateral esquerda',[(x0,y0,.909),(x0,y1,.909),(x0+.025,y1-.025,.722),(x0+.025,y0+.025,.722)],[(0,1,2,3)]),('Cuba lateral direita',[(x1,y0,.909),(x1-.025,y0+.025,.722),(x1-.025,y1-.025,.722),(x1,y1,.909)],[(0,1,2,3)]),('Cuba frente',[(x0,y0,.909),(x0+.025,y0+.025,.722),(x1-.025,y0+.025,.722),(x1,y0,.909)],[(0,1,2,3)]),('Cuba fundo',[(x0,y1,.909),(x1,y1,.909),(x1-.025,y1-.025,.722),(x0+.025,y1-.025,.722)],[(0,1,2,3)])]:
 o=mesh(name,v,[tuple(reversed(face)) for face in f],'black');mod=o.modifiers.new('Espessura metal da cuba','SOLIDIFY');mod.thickness=.001;mod.offset=-1
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.modifier_apply(modifier=mod.name);o.select_set(False)
for lo,hi in [((x0-.011,y0-.011,.912),(x1+.011,y0+.005,.920)),((x0-.011,y1-.005,.912),(x1+.011,y1+.011,.920)),((x0-.011,y0,.912),(x0+.005,y1,.920)),((x1-.005,y0,.912),(x1+.011,y1,.920))]:box('Borda da cuba',lo,hi,'black',.002)
cylinder('Ralo inox',su,sv,.724,.035,.003,'steel');cylinder('Interior ralo',su,sv,.727,.021,.001,'black')
# Gooseneck faucet with actual curved pipe and a separate control lever.
fv=.58;pts=[(su,fv,.92),(su,fv,1.16),(su,fv,1.235)]
for k in range(1,17):
 a=k/16*math.pi;pts.append((su,fv-.098+.098*math.cos(a),1.235+.098*math.sin(a)))
pts.append((su,fv-.196,1.18));tube('Torneira preta curva',pts,.016,'black',16)
cylinder('Base torneira',su,fv,.913,.028,.12,'black');tube('Comando torneira',[(su,fv,.978),(su+.064,fv,.978),(su+.064,fv,1.031)],.009,'black')
# Five burners, supports, control knobs and a recessed hood.
cu=2.36;cv=.33;box('Cooktop placa',(cu-.405,cv-.265,.915),(cu+.405,cv+.265,.928),'steel',.006)
box('Cooktop vidro negro',(cu-.393,cv-.251,.925),(cu+.393,cv+.251,.930),'black',.003)
for j,(du,dv,r) in enumerate([(-.24,-.12,.044),(.24,-.12,.044),(-.24,.13,.058),(.24,.13,.058),(0,.01,.074)]):
 cylinder('Queimador %d'%j,cu+du,cv+dv,.932,r,.022,'black')
 for ax in (0,1):
  points=[]
  for delta,z in [(-.10,.938),(-.07,.972),(.07,.972),(.10,.938)]:points.append((cu+du+(delta if ax==0 else 0),cv+dv+(delta if ax else 0),z))
  tube('Grelha %d %d'%(j,ax),points,.007,'black')
for j in range(5):cylinder('Botao cooktop %d'%j,cu-.15+j*.075,.096,.939,.014,.016,'black')
box('Coifa caixa embutida',(cu-.435,.270,1.61),(cu+.435,.617,1.68),'black',.003)
box('Coifa moldura inox',(cu-.415,.265,1.602),(cu+.415,.614,1.616),'steel',.002)
for j in range(12):box('Ranhura coifa %d'%j,(cu-.35+j*.06,.30,1.600),(cu-.33+j*.06,.56,1.602),'black',0)
# Upper cabinet wood doors: nearly full ceiling height as in the reference.
box('Fundo armario superior',(start,.615,1.68),(6.50,.644,3.03),'wood')
box('Base armario superior',(start,.265,1.658),(end,.64,1.676),'wood',collision=True)
upperstep=(end-start)/10
for j in range(10):
 u=start+j*upperstep;box('Porta madeira superior %02d'%j,(u+.004,.24,1.68),(u+upperstep-.004,.262,3.024),'wood',.0025)
 box('Lateral superior %02d'%j,(u,.265,1.68),(u+.018,.64,3.024),'wood')
box('Topo madeira',(start,.245,3.012),(6.50,.640,3.03),'wood')
# Under-cabinet light has a visible emitting underside and a recessed aluminum channel.
box('Perfil LED sob armario',(start+.02,.282,1.639),(end-.02,.309,1.658),'black',.002)
box('Difusor LED continuo',(start+.025,.279,1.638),(end-.025,.311,1.642),'led',.001)
# Stainless refrigerator, genuine depth, recessed dispenser and physical handles.
ru=5.49;re=6.49
box('Geladeira corpo',(ru,.05,.04),(re,.643,2.20),'steel',.008,True)
box('Geladeira borda preta',(ru+.009,-.035,.07),(re-.009,.04,2.19),'black',.004)
mid=(ru+re)/2
for j,(a,b) in enumerate(((ru+.02,mid-.004),(mid+.004,re-.02))):
 box('Geladeira porta inox %d'%j,(a,-.061,.68),(b,-.02,2.175),'steel',.005)
 tube('Geladeira puxador vertical %d'%j,[(mid+(-.046 if j==0 else .046),-.112,1.0),(mid+(-.046 if j==0 else .046),-.112,1.84)],.012,'steel',16)
box('Freezer gaveta inferior',(ru+.02,-.061,.085),(re-.02,-.02,.663),'steel',.005)
box('Puxador freezer',(ru+.14,-.112,.567),(re-.14,-.087,.591),'steel',.01)
box('Dispensador nicho preto',(ru+.07,-.063,1.025),(ru+.31,-.061,1.34),'black',.007)
box('Dispensador bandeja',(ru+.065,-.084,1.017),(ru+.315,-.062,1.032),'steel',.002)
box('Dispensador display',(ru+.1,-.065,1.285),(ru+.28,-.063,1.318),'black',.002)
for j in range(7):box('Ventilacao geladeira '+str(j),(ru+.05,-.045,.05+j*.005),(re-.05,-.035,.052+j*.005),'black',0)
box('Armario sobre geladeira',(ru+.009,.24,2.23),(re-.009,.262,3.024),'wood',.003)
box('Lateral geladeira madeira',(6.49,.03,.01),(6.518,.644,3.03),'wood',.003)
# Fitted scribed caps close the small gap to the actual ceiling, as in the reference.
for name,lo,hi in [('Fechamento torre ate o forro',(0,-.021,3.030),(.75,.640,3.15)),('Fechamento superiores ate o forro',(.75,.24,3.030),(6.518,.640,3.15))]:
 o=box(name,lo,hi,'wood',.002)
 for loop in o.data.loops:
  p=o.data.vertices[loop.vertex_index].co;o.data.uv_layers[0].data[loop.index].uv=(p.x/.47,(p.z-1.68)/1.344)
# Two leaning cutting boards from the complete reference, individually modeled.
for j,(u,height,width) in enumerate(((1.03,.30,.16),(1.20,.23,.125))):
 box('Tabua madeira %d'%j,(u,.568,.915),(u+width,.586,.915+height),'darkwood',.025)
 box('Cabo tabua %d'%j,(u+width*.36,.568,.91+height),(u+width*.64,.586,.97+height),'darkwood',.008)
 tube('Furo cabo tabua %d'%j,[(u+width*.5,.566,.935+height),(u+width*.5,.567,.935+height)],.009,'black')
bpy.context.view_layer.update()
triangles=0
for o in parts:o.data.calc_loop_triangles();triangles+=len(o.data.loop_triangles)
spec=json.loads((W/'cozinha_completa.json').read_text());spec.update(parts=len(parts),triangles=triangles,collision_boxes=solids,real_sink_cutout=True,appliances=['microwave','oven','fridge','cooktop','sink','faucet','extractor'],height_m=3.15,ceiling_gap_m=.008,wall_gap_m=.008)
# Keep an editable local-coordinate standalone source.
spec['local_bounds']=[[-.018,-.112,0],[6.518,.644,3.15]]
bpy.ops.wm.save_as_mainfile(filepath=str(W/'cozinha_completa.blend'))
tx=Matrix(((0,1,0,13.534),(-1,0,0,-6.6),(0,0,1,-.8),(0,0,0,1)))
root=bpy.data.objects.new(spec['model'],None);bpy.context.scene.collection.objects.link(root);root.sollum_type=SollumType.DRAWABLE
ps=[]
for src in parts:
 me=src.data.copy();me.transform(tx);me.update();ps.extend(v.co[:] for v in me.vertices)
 ob=bpy.data.objects.new(src.name+'_export',me);bpy.context.scene.collection.objects.link(ob);ob.parent=root;convert_obj_to_model(ob)
points=np.array(ps);spec['lo']=points.min(0).tolist();spec['hi']=points.max(0).tolist()
targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
with export_context_scope(ExportContext(spec['model'],ExportSettings(targets=targets))):export_ydr(root).save(OUT,targets)
(W/'cozinha_completa.json').write_text(json.dumps(spec,indent=2),encoding='utf-8');print('KITCHEN_BUILT',len(parts),'parts;',triangles,'triangles; bounds',spec['lo'],spec['hi'],flush=True)


