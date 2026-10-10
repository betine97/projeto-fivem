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
col=bpy.data.collections.new('24_BAR_PAREDE_REFERENCIA');bpy.context.scene.collection.children.link(col)
for key in ['madeira','marmore','arte','preto','bronze','creme','ceramica','vidro','vinho','rotulo','folha','led','vidro_transparente']:
 preset='emissive.sps' if key=='led' else 'glass.sps' if key=='vidro_transparente' else 'normal_spec.sps'
 m=create_shader(preset);m.name='bar_'+key
 for sampler,txname in [('DiffuseSampler','bar_'+key),('BumpSampler','bar_madeira_n' if key=='madeira' else 'bar_normal'),('SpecSampler','bar_spec_fosco' if key in ['arte','folha','rotulo','creme','ceramica'] else 'bar_spec_metal' if key=='bronze' else 'bar_spec')]:
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
 if family in ['madeira','arte']:
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
L=4.38;U=6.90;D=.535
box('Rodape recuado',(L+.027,-.405,.018),(U-.027,-.065,.115),'preto')
box('Caixa inferior',(L,-D,.105),(U,-.008,.88),'madeira',.003,True,True)
box('Lateral esquerda continuo',(L-.032,-.43,.0),(L,-.008,3.12),'creme',.003,True)
box('Lateral direita continuo',(U,-.43,0),(U+.032,-.008,3.12),'creme',.003,True)
box('Travessa superior',(L,-.43,3.07),(U,-.008,3.12),'creme',.002,True)
box('Marmore preto veios bronze fundo',(L+.005,-.032,.91),(U-.005,-.008,3.07),'marmore',.001)
# Consistent stone mapping across all three tiers.
for o in [parts[-1]]:
 for loop in o.data.loops:
  v=o.data.vertices[loop.vertex_index].co;o.data.uv_layers[0].data[loop.index].uv=((v.x-L)/2.52,(v.z-.91)/2.16)
for j,z in enumerate([.88,1.58,2.22]):
 box('Prateleira espessa '+str(j),(L,-.435,z),(U,-.006,z+.031),'marmore',.002,True)
 for y in [-.397,-.379]:box('Perfil aluminio LED '+str(j)+str(y),(L+.013,y,z-.009),(U-.013,y+.008,z-.002),'bronze',.001)
 box('Difusor LED continuo '+str(j),(L+.015,-.388,z-.011),(U-.015,-.380,z-.008),'led',0)
box('LED teto nicho',(L+.025,-.285,3.056),(U-.025,-.277,3.059),'led',0)
for j,x in enumerate([L,L+.615,L+1.23]):
 end=x+.615-.007 if j<2 else L+1.32
 box('Porta armario madeira '+str(j),(x+.008,-D-.023,.125),(end,-D+.003,.866),'madeira',.002)
box('Gabinete direito inferior',(U-.66,-D-.023,.125),(U-.008,-D+.003,.866),'madeira',.002)
# Wine cooler door with genuine interior racks/bottles behind transparent glass.
cx=L+1.65;wx=.59;h0=.125;h1=.862
box('Adega caixa preta',(cx-wx/2-.023,-D-.047,h0-.014),(cx+wx/2+.023,-.065,h1+.012),'preto',.004,False,True)
box('Adega interior fundo',(cx-wx/2+.02,-.065,h0+.04),(cx+wx/2-.02,-.05,h1-.055),'preto',0)
for j,z in enumerate([.207,.323,.439,.555,.671]):
 box('Adega prateleira madeira '+str(j),(cx-.257,-.494,z),(cx+.257,-.083,z+.018),'madeira',.002)
 for i in range(4):
  x=cx-.184+i*.122
  obj=bottle('Adega vinho %d %d'%(j,i),x,-.258,z+.024,.225,False,12)
  # The rack bottles lie lengthwise; rotate each of this bottle's three parts.
  for ob in parts[-3:]:
   for v in ob.data.vertices:v.co=Vector((x,-.258,z+.055))+Matrix.Rotation(math.pi/2,4,'X')@(v.co-Vector((x,-.258,z+.024)))
for a,b in [((cx-.313,-D-.057,h0),(cx-.283,-D-.033,h1)),((cx+.283,-D-.057,h0),(cx+.313,-D-.033,h1)),((cx-.283,-D-.057,h0),(cx+.283,-D-.033,h0+.032)),((cx-.283,-D-.057,h1-.065),(cx+.283,-D-.033,h1))]:box('Adega moldura porta',a,b,'preto',.002)
box('Adega vidro real',(cx-.281,-D-.050,h0+.035),(cx+.281,-D-.048,h1-.069),'vidro_transparente',0)
box('Adega puxador horizontal',(cx-.237,-D-.082,h1-.090),(cx+.237,-D-.062,h1-.074),'bronze',.003)
for j in range(8):box('Adega grelha ventilacao '+str(j),(cx-.271,-D-.060,.148+j*.004),(cx+.271,-D-.058,.15+j*.004),'bronze',0)
box('Adega display preto',(cx-.215,-D-.059,h1-.048),(cx+.18,-D-.057,h1-.020),'preto',0)
box('Adega digitos amarelos',(cx-.09,-D-.060,h1-.040),(cx-.059,-D-.059,h1-.030),'led',0)
# Exact arrangement from the reference: upper ceramics; middle nine bottles;
# lower stemware, books, tray, three bottles, a bowl and a tall ceramic vase.
vase('Vaso escuro alto superior',L+.18,-.20,2.253,.40,.082,'preto','narrow')
vase('Vaso escuro baixo superior',L+.40,-.19,2.253,.25,.084,'preto')
vase('Vaso creme superior central',L+.86,-.22,2.253,.43,.142)
vase('Tigela rasa superior',L+1.24,-.22,2.253,.095,.113,'ceramica','bowl')
vase('Vaso tigela creme superior',L+1.72,-.21,2.253,.215,.208,'creme','bowl')
vase('Vaso branco nicho medio esquerdo',L+.16,-.19,1.611,.275,.054,'ceramica','narrow')
vase('Vaso branco 2 nicho medio',L+.34,-.20,1.611,.255,.052,'creme','narrow')
for i in range(9):bottle('Garrafa fileira %02d'%i,L+.62+i*.177,-.222,1.611,.35 if i%3 else .39,True)
vase('Vaso direito medio',U-.15,-.20,1.611,.29,.06,'creme','narrow')
for i in range(4):glass('Taca vinho %02d'%i,L+.16+i*.13,-.265,.911)
for i,(w,z) in enumerate([(.31,.911),(.25,.938),(.295,.963)]):box('Livro decorativo '+str(i),(L+.11,-.382,z),(L+.11+w,-.163,z+.025),'rotulo',.001)
lathe('Bandeja garrafas',[(0,0),(.215,0),(.215,.014),(0,.014)],(L+1.15,-.248,.911),'bronze',32)
for i in range(3):bottle('Bebida bandeja '+str(i),L+.99+i*.153,-.244,.926,.325-i*.029,True)
vase('Tigela decorativa inferior',L+1.92,-.245,.911,.095,.218,'bronze','bowl')
vase('Vaso inferior direito',U-.15,-.224,.911,.315,.076,'ceramica','narrow')
# Hanging greenery at the upper right, with leaf geometry and curved stems.
vase('Cachepo planta pendente',U-.25,-.20,2.253,.23,.095,'bronze','bowl')
rng=np.random.default_rng(42)
for k in range(18):
 x=U-.25+rng.uniform(-.10,.10);y=-.19+rng.uniform(-.08,.08);fall=.33 if k<6 else rng.uniform(.32,.80);pts=[]
 for j in range(12):
  t=j/11;xx=x+math.sin(t*4+k)*.07;yy=y-.045-t*.035;z=2.48-fall*t;pts.append((xx,yy,z))
  if j%2==0:
   for sign in [-1,1]:
    vv=[(xx,yy,z),(xx+sign*.035,yy-.012,z+.030),(xx+sign*.08,yy-.024,z-.014),(xx+sign*.030,yy-.028,z-.040)]
    mesh('Folha pendente %d %d %d'%(k,j,sign),vv,[(0,1,2,3),(3,2,1,0)],'folha',smooth=True)
 for a,b in zip(pts,pts[1:]):
  v=Vector(b)-Vector(a);o=lathe('Ramo pendente',[(0,0),(.0018,0),(.0018,v.length),(0,v.length)],(0,0,0),'folha',6)
  rot=v.to_track_quat('Z','Y').to_matrix().to_4x4()
  for vert in o.data.vertices:vert.co=rot@vert.co+Vector(a)
# Artwork rectangle and thin champagne frame, matching the supplied canvas.
ax=2.53;az=1.95;aw=spec['art_canvas_width_m'];ah=spec['art_canvas_height_m'];z0=az-ah/2
box('Quadro fundo',(ax-aw/2-.014,-.041,z0-.014),(ax+aw/2+.014,-.012,z0+ah+.014),'creme')
box('Quadro tela abstrata referencia',(ax-aw/2,-.052,z0),(ax+aw/2,-.044,z0+ah),'arte',0)
for a,b in [((ax-aw/2-.014,-.065,z0-.014),(ax-aw/2,-.018,z0+ah+.014)),((ax+aw/2,-.065,z0-.014),(ax+aw/2+.014,-.018,z0+ah+.014)),((ax-aw/2,-.065,z0-.014),(ax+aw/2,-.018,z0)),((ax-aw/2,-.065,z0+ah),(ax+aw/2,-.018,z0+ah+.014))]:box('Moldura fina champagne',a,b,'bronze',.0008)
box('Arandela quadro suporte',(ax-.05,-.08,3.025),(ax+.05,-.01,3.060),'bronze',.002)
box('Arandela quadro braco',(ax-.012,-.195,3.039),(ax+.012,-.063,3.052),'bronze',.002)
box('Arandela quadro barra',(ax-.41,-.219,3.022),(ax+.41,-.190,3.048),'bronze',.002)
box('Arandela quadro difusor',(ax-.38,-.210,3.020),(ax+.38,-.196,3.023),'led',0)
spec['parts']=len(parts);spec['collision_boxes']=solids;spec['art_source_canvas']=str(T/'arte_canvas.png')
bpy.context.view_layer.update();pts=np.array([v.co for o in parts for v in o.data.vertices]);spec['local_lo']=pts.min(0).tolist();spec['local_hi']=pts.max(0).tolist()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'bar_parede_editavel.blend'),compress=True)
tx=Matrix(((-1,0,0,spec['design_start_x']),(0,-1,0,spec['model_wall_y']),(0,0,1,spec['floor_z']),(0,0,0,1)))
root=bpy.data.objects.new(spec['model'],None);bpy.context.scene.collection.objects.link(root);root.sollum_type=SollumType.DRAWABLE;exportparts=[]
for src in parts:
 me=src.data.copy();me.transform(tx);me.update();obj=bpy.data.objects.new(src.name+'_export',me);bpy.context.scene.collection.objects.link(obj);obj.parent=root;convert_obj_to_model(obj);exportparts.append(obj)
pts=np.array([v.co for o in exportparts for v in o.data.vertices]);spec['lo']=pts.min(0).tolist();spec['hi']=pts.max(0).tolist()
with export_context_scope(ExportContext(spec['model'],ExportSettings(targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)))):export_ydr(root).save(O,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),))
for ratio,suffix in [(.50,'medium'),(.20,'low'),(.075,'verylow')]:
 bpy.ops.object.select_all(action='DESELECT'); copies=[]
 for src in exportparts:
  obj=src.copy();obj.data=src.data.copy();bpy.context.scene.collection.objects.link(obj);obj.parent=None;obj.select_set(True);copies.append(obj)
 bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();obj=bpy.context.object
 dec=obj.modifiers.new('LOD simplificado','DECIMATE');dec.ratio=ratio;dec.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=dec.name)
 lodroot=bpy.data.objects.new('bar_'+suffix,None);bpy.context.scene.collection.objects.link(lodroot);lodroot.sollum_type=SollumType.DRAWABLE;obj.parent=lodroot;convert_obj_to_model(obj)
 with export_context_scope(ExportContext('bar_'+suffix,ExportSettings(targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)))):export_ydr(lodroot).save(O,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),))
 bpy.data.objects.remove(obj,do_unlink=True);bpy.data.objects.remove(lodroot,do_unlink=True)
(P/'spec.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
print('BAR_BUILT',len(parts),'parts',spec['lo'],spec['hi'],flush=True)
