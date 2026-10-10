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
for key in ['madeira','marmore','arte','preto','bronze','creme','ceramica','vidro','vinho','rotulo','folha','led','vidro_transparente','vinho_escuro','ambar','rotulo_1','rotulo_2','rotulo_3','cristal','arte_mini']:
 preset='emissive.sps' if key=='led' else 'glass.sps' if key in ['vidro_transparente','cristal'] else 'normal_spec.sps'
 m=create_shader(preset);m.name='adega_'+key
 for sampler,txname in [('DiffuseSampler','adega_'+key),('BumpSampler','adega_madeira_n' if key=='madeira' else 'adega_normal'),('SpecSampler','adega_spec_fosco' if key in ['arte','folha','rotulo','creme','ceramica'] else 'adega_spec_metal' if key=='bronze' else 'adega_spec')]:
  node=m.node_tree.nodes.get(sampler)
  if node is None:continue
  im=bpy.data.images.load(str(T/(txname+'.dds')),check_existing=True);im.pack();node.image=im;node.texture_properties.embedded=True
  if sampler!='DiffuseSampler':im.colorspace_settings.name='Non-Color'
  m.node_tree.links.new(m.node_tree.nodes['UVMap 0'].outputs['UV'],node.inputs['Vector'])
 for param,value in [('specularIntensityMult',1.1 if key in ['vidro','vinho_escuro','ambar','cristal'] else .7 if key in ['marmore','bronze'] else .18),('specularFalloffMult',160 if key in ['marmore','bronze','vidro','vinho_escuro','ambar','cristal'] else 28),('specularFresnel',.4),('wetnessMultiplier',0),('bumpiness',.15),('emissiveMultiplier',3.0),('reflectivePower',.70 if key=='cristal' else .35)]:
  if (node:=m.node_tree.nodes.get(param)) is not None:node.set(0,value)
 if (node:=m.node_tree.nodes.get('specMapIntMask')) is not None:
  node.set(0,1.0);node.set(1,0.0);node.set(2,0.0)
 bsdf=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if bsdf:
  # Sollumz preview defaults can suppress the glass Fresnel completely.
  # Native reflection still comes from each preset and its actual parameters.
  for link in list(bsdf.inputs['Specular IOR Level'].links):m.node_tree.links.remove(link)
  bsdf.inputs['Specular IOR Level'].default_value=.5 if key not in ['folha','rotulo','rotulo_1','rotulo_2','rotulo_3'] else .18
  for field,value in [('Roughness',.065 if key in ['vidro','vinho_escuro','ambar','cristal'] else .25 if key in ['marmore','bronze'] else .42 if key=='madeira' else .60),('Metallic',.65 if key=='bronze' else 0)]:
   for link in list(bsdf.inputs[field].links):m.node_tree.links.remove(link)
   bsdf.inputs[field].default_value=value
  if key in ['vidro_transparente','cristal']:
   for field,value in [('Alpha',1.0),('Transmission Weight',1.0),('Roughness',.055),('IOR',1.45)]:
    if field in bsdf.inputs:
     for link in list(bsdf.inputs[field].links):m.node_tree.links.remove(link)
     bsdf.inputs[field].default_value=value
   # Physical Blender glass is separate from the native alpha/reflection
   # preset. The generic alpha preview suppresses highlights, and its
   # Principled/normal combination produces dark transmission in Cycles.
   glass=m.node_tree.nodes.new('ShaderNodeBsdfGlass')
   glass.name='Vidro fisico Blender'
   glass.inputs['Color'].default_value=(.98,.98,.98,1)
   glass.inputs['Roughness'].default_value=.02
   glass.inputs['IOR'].default_value=1.45
   out=next(n for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL')
   m.node_tree.links.new(glass.outputs[0],out.inputs['Surface'])
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

# All dimensions follow the supplied frontal reference, measured in pixels.
sx=spec['width_m']/1393;sz=spec['height_m']/871
X=lambda pixel:(pixel-27)*sx
Z=lambda pixel:(978-pixel)*sz
height=spec['height_m'];width=spec['width_m'];depth=.57
def face_uv(obj,lo,hi):
 for loop in obj.data.loops:
  v=obj.data.vertices[loop.vertex_index].co
  obj.data.uv_layers[0].data[loop.index].uv=((v.x-lo[0])/(hi[0]-lo[0]),(v.z-lo[2])/(hi[2]-lo[2]))
def panel(name,x0,x1,z0,z1,family,y0=-.061,y1=-.028,collision=False,bevel=.002):
 return box(name,(x0,y0,z0),(x1,y1,z1),family,bevel,collision)
def pivot_rotate(objects,center,axis,angle):
 rotation=Matrix.Rotation(angle,4,axis);center=Vector(center)
 for obj in objects:
  for v in obj.data.vertices:v.co=center+rotation@(v.co-center)
  obj.data.update()
def wine(name,center,length=.36,label=1,sides=24,angle=math.pi/2):
 x,y,z=center;start=len(parts);r=.045
 lathe(name+' vidro verde escuro',[(0,0),(r*.70,0),(r*.91,.003),(r,.009),(r,length*.64),(r*.98,length*.66),(r*.92,length*.69),(r*.65,length*.74),(r*.35,length*.77),(r*.31,length*.79),(r*.31,length*.94),(r*.35,length*.95),(r*.35,length),(0,length)],center,'vinho_escuro',sides)
 label_obj=lathe(name+' rotulo papel',[(r+.0005,length*.23),(r+.0005,length*.53)],center,'rotulo_'+str(label),sides)
 for li in label_obj.data.loops:
  v=label_obj.data.vertices[li.vertex_index].co
  label_obj.data.uv_layers[0].data[li.index].uv=((math.atan2(v.y-y,v.x-x)/math.tau+.75)%1,(v.z-z-length*.23)/(length*.30))
 lathe(name+' lacre bronze',[(r*.36,length*.94),(r*.36,length)],center,'bronze' if label==3 else 'vinho',sides)
 pivot_rotate(parts[start:],center,'Y',angle)
 return parts[start:]
def spirit(name,center,h=.29,shape='round',crystal=False,label=2):
 x,y,z=center;r=h*.17;start=len(parts)
 if shape=='square':
  # Faceted shoulders and bevelled square body, based on luxury decanters.
  profile=[(0,0),(r*.80,0),(r,.012),(r,h*.58),(r*.82,h*.69),(r*.27,h*.76),(r*.27,h*.95),(r*.33,h*.96),(r*.33,h),(0,h)]
  sides=8
 else:
  profile=[(0,0),(r*.79,0),(r,.008),(r,h*.58),(r*.72,h*.69),(r*.30,h*.75),(r*.30,h*.93),(r*.36,h*.94),(r*.36,h),(0,h)];sides=24
 if crystal:
  inner=h*.68
  lathe(name+' bebida ambar',[(0,.015),(r*.70,.015),(r*.86,.027),(r*.86,inner),(0,inner)],center,'ambar',sides)
  o=lathe(name+' cristal lapidado',profile,center,'cristal',sides)
  lathe(name+' tampa cristal',[(0,0),(r*.43,.003),(r*.48,.018),(r*.25,.036),(0,.040)],(x,y,z+h),'cristal',16)
 else:
  lathe(name+' vidro ambar',profile,center,'ambar',sides)
  lathe(name+' tampa preta',[(r*.36,h*.94),(r*.36,h)],center,'preto',sides)
 if label:
  o=panel(name+' etiqueta',x-r*.58,x+r*.58,z+h*.18,z+h*.52,'rotulo_'+str(label),y-r-.002,y-r,False,0)
  face_uv(o,(x-r*.58,y-r,z+h*.18),(x+r*.58,y,z+h*.52))
 return parts[start:]
def leaf(name,center,size,rotation,narrow=False):
 # Curved, tapered heart/oval leaves with a central ridge and pigment texture.
 vertices=[(0,0,0),(-.50,-.06,.23),(-.48,-.05,.57),(-.24,-.07,.85),(0,-.035,1),(.24,-.07,.85),(.48,-.05,.57),(.50,-.06,.23),(0,-.115,.48)]
 if narrow:vertices=[(v[0]*.3,v[1],v[2]) for v in vertices]
 matrix=Matrix.Rotation(rotation,4,'Y')@Matrix.Rotation(math.sin(rotation)*.4,4,'Z')
 points=[Vector(center)+matrix@(Vector(v)*size) for v in vertices]
 faces=[(i,(i+1)%8,8) for i in range(8)]
 # Actual back faces prevent single-sided leaf disappearance in the game.
 faces=faces+[tuple(i+9 for i in reversed(f)) for f in faces]
 points=points+[p+Vector((0,.0002,0)) for p in points]
 obj=mesh(name,points,faces,'folha',[(v[0]+.5,v[2]) for v in vertices]*2,True)
 return obj
def stem(name,points,r=.0015):
 for a,b in zip(points,points[1:]):
  v=Vector(b)-Vector(a);obj=lathe(name,[(0,0),(r,0),(r,v.length),(0,v.length)],(0,0,0),'folha',6)
  rot=v.to_track_quat('Z','Y').to_matrix().to_4x4()
  for vert in obj.data.vertices:vert.co=rot@vert.co+Vector(a)

# Solid carcass only at the sides/back. The front stays open behind glass.
box('Plinto madeira',(0,-.555,0),(width,-.015,.048),'madeira',.002)
panel('Costas madeira continuo',0,width,0,height,'madeira',-.023,0,True)
panel('Topo madeira continuo',0,width,height-.035,height,'madeira',-.575,0,True)
for x in [0,X(404),X(1038),width-.024]:
 box('Lateral estrutural madeira',(x,-.555,.025),(x+.024,-.015,height-.03),'madeira',.002,True)

vitrines=[(45,219),(225,400),(1048,1224),(1228,1402)]
spec['display_wine_bottles']=52
for k,(p0,p1) in enumerate(vitrines):
 a=X(p0);b=X(p1);bottom=Z(962);top=Z(116);s=.047
 panel('Vitrine %d pedra fundo'%k,a+.016,b-.016,bottom+.016,top-.016,'marmore',-.064,-.023)
 for name,lo,hi in [
  ('vertical esquerda',(a,-.567,bottom),(a+s,-.535,top)),
  ('vertical direita',(b-s,-.567,bottom),(b,-.535,top)),
  ('inferior',(a+s,-.567,bottom),(b-s,-.535,bottom+s)),
  ('superior',(a+s,-.567,top-s),(b-s,-.535,top))]:box('Porta vitrine %d %s'%(k,name),lo,hi,'preto',.003)
 panel('Vidro transparente porta vitrine '+str(k),a+s,b-s,bottom+s,top-s,'vidro_transparente',-.550,-.548,True)
 # Deep black reveals and slim brushed brass support rails.
 box('Montante interior esquerdo '+str(k),(a+.020,-.529,bottom+.017),(a+.033,-.029,top-.016),'preto',.001)
 box('Montante interior direito '+str(k),(b-.033,-.529,bottom+.017),(b-.020,-.029,top-.016),'preto',.001)
 for xx in [a+.058,b-.058]:
  box('Canal LED vitrine '+str(k),(xx,-.175,bottom+.047),(xx+.009,-.159,top-.047),'bronze',.001)
  box('LED vertical vitrine '+str(k),(xx+.002,-.178,bottom+.047),(xx+.007,-.176,top-.047),'led',0)
 for z in [bottom+.05,top-.068]:panel('LED horizontal vitrine '+str(k),a+.049,b-.049,z,z+.006,'led',-.175,-.173,False,0)
 handle_x=b-.018 if k in [0,2] else a+.018
 box('Puxador preto longo vitrine '+str(k),(handle_x-.007,-.597,Z(593)),(handle_x+.007,-.568,Z(510)),'preto',.003)
 for row,pixel in enumerate(range(201,850,53)):
  z=Z(pixel);base=z-.048
  panel('Suporte garrafa %d %d'%(k,row),a+.043,b-.043,base-.004,base+.006,'bronze',-.432,-.164)
  for yy in [-.415,-.220]:panel('Friso suporte %d %d'%(k,row),a+.037,b-.037,base+.002,base+.014,'bronze',yy,yy+.005)
  wine('Vinho vitrine %d %d'%(k,row),(a+.095,-.315,z),.355,(row+k)%3+1)
  panel('Luz sob suporte %d %d'%(k,row),a+.05,b-.05,base-.006,base-.004,'led',-.175,-.172,False,0)

# Central wood niches with long recessed warm LED lines.
l=X(414);r=X(1035)
panel('Nicho central fundo madeira',l,r,Z(705),Z(119),'madeira',-.035,-.014)
panel('Nicho inferior marmore creme',l,r,Z(706),Z(504),'marmore',-.057,-.035)
for z,thick in [(Z(734),.079),(Z(505),.044),(Z(334),.044)]:
 box('Prateleira central espessa %.3f'%z,(l,-.588,z),(r,-.029,z+thick),'marmore' if z<1 else 'madeira',.003,True)
 if z>1:
  panel('Perfil LED central %.3f'%z,l+.020,r-.020,z-.010,z-.003,'bronze',-.395,-.385,False,.001)
  panel('Difusor LED central %.3f'%z,l+.022,r-.022,z-.012,z-.008,'led',-.393,-.387,False,0)
panel('LED topo nicho central',l+.022,r-.022,Z(161),Z(156),'led',-.123,-.117,False,0)
panel('LED fundo bancada central',l+.022,r-.022,Z(511),Z(506),'led',-.124,-.118,False,0)

# Lower cabinetry exactly follows the split cooler / three full-height doors.
lower_h=Z(736)
box('Base central caixa aberta',(l,-.560,.060),(r,-.026,lower_h),'madeira',.002,True,True)
cool_l=X(432);cool_r=X(598)
for a,b in [(X(605),X(753)),(X(757),X(890)),(X(894),X(1033))]:
 panel('Porta inferior carvalho',a,b,Z(952),Z(739),'madeira',-.586,-.563)
panel('Adega refrigerada caixa aberta',cool_l,cool_r,Z(973),Z(735),'preto',-.585,-.05)
# Remove its solid frontal face so every rack/bottle remains visible.
o=parts.pop();bpy.data.objects.remove(o,do_unlink=True)
box('Adega refrigerada caixa aberta',(cool_l,-.589,Z(973)),(cool_r,-.03,Z(735)),'preto',.003,False,True)
for row,pixel in enumerate([769,802,835,868,901]):
 z=Z(pixel)
 box('Prateleira adega refrigerada '+str(row),(cool_l+.05,-.535,z-.027),(cool_r-.05,-.100,z-.009),'madeira',.002)
 for i in range(5):
  x=cool_l+.075+i*.083;wine('Vinho horizontal adega %d %d'%(row,i),(x,-.120,z+.015),.295,(i+row)%3+1,sides=16,angle=0)
  # In the mini fridge bottles point towards the viewer, perpendicular to racks.
  pivot_rotate(parts[-3:],(x,-.120,z+.015),'X',math.pi/2)
for a,b in [((cool_l,-.600,Z(964)),(cool_l+.035,-.581,Z(738))),((cool_r-.035,-.600,Z(964)),(cool_r,-.581,Z(738))),((cool_l+.035,-.600,Z(738)-.035),(cool_r-.035,-.581,Z(738))),((cool_l+.035,-.600,Z(952)),(cool_r-.035,-.581,Z(952)+.035))]:box('Adega refrigerada moldura',a,b,'preto',.002)
panel('Adega refrigerada vidro',cool_l+.035,cool_r-.035,Z(950),Z(754),'vidro_transparente',-.591,-.589)
panel('Adega refrigerada puxador',cool_l+.070,cool_r-.060,Z(751),Z(746),'preto',-.624,-.602)
for j in range(9):panel('Adega refrigerada grelha '+str(j),cool_l+.048,cool_r-.048,.017+j*.0038,.019+j*.0038,'preto',-.602,-.590,False,0)

# Eight different amber decanters, arranged in their original niches.
for i,(px,typ) in enumerate([(783,'square'),(842,'round'),(895,'square'),(946,'square')]):
 spirit('Destilado superior '+str(i),(X(px),-.277,Z(315)),.305 if i!=1 else .29,typ,crystal=i==1,label=(i%3)+1)
for i,(px,typ) in enumerate([(463,'square'),(500,'round'),(541,'square'),(582,'round')]):
 spirit('Destilado prateleira meio '+str(i),(X(px),-.313,Z(489)),.30 if i in [0,3] else .275,typ,crystal=i==3,label=(i%3)+1)
vase('Tigela preta central',X(681),-.308,Z(489),.112,.150,'preto','bowl')

# Framed miniature artwork and five clear wine glasses.
ax=X(859);az=Z(433);aw=.345;ah=.376
panel('Quadro mini suporte',ax-aw/2-.018,ax+aw/2+.018,az-ah/2-.018,az+ah/2+.018,'preto',-.126,-.105)
panel('Quadro mini passe partout',ax-aw/2+.003,ax+aw/2-.003,az-ah/2+.003,az+ah/2-.003,'creme',-.130,-.128,False,0)
o=panel('Quadro mini arte',ax-.102,ax+.102,az-.132,az+.132,'arte_mini',-.133,-.131,False,0)
face_uv(o,(ax-.102,0,az-.132),(ax+.102,0,az+.132))
for i,px in enumerate([882,923,947,971,995]):glass('Taca cristal prateleira '+str(i),X(px),-.368,Z(489))

# Marble countertop accessories: ceramic leafy vase, brass tray, three
# decanters plus dark bottle, and a genuine hemispherical table lamp.
z=Z(706);vase('Vaso ceramica bancada',X(493),-.298,z,.260,.120,'ceramica')
lathe('Bandeja bronze bancada',[(0,0),(.322,0),(.322,.012),(.315,.018),(0,.018)],(X(695),-.325,z),'bronze',40)
for i,(px,typ) in enumerate([(642,'round'),(683,'square'),(721,'square')]):
 spirit('Licoreira bancada '+str(i),(X(px),-.325,z+.018),.27 if i==0 else .29,typ,crystal=i<2,label=0 if i<2 else 1)
wine('Vinho escuro sobre bancada',(X(753),-.318,z+.018),.245,3,24,0)
lamp_x=X(967);lamp_y=-.280
lathe('Abajur base disco',[(0,0),(.085,0),(.085,.010),(.075,.016),(0,.016)],(lamp_x,lamp_y,z),'bronze',32)
lathe('Abajur haste',[(0,0),(.019,0),(.019,.293),(0,.293)],(lamp_x,lamp_y,z+.016),'bronze',24)
lathe('Abajur copa dourada',[(.145,0),(.144,.029),(.133,.062),(.112,.095),(.080,.122),(.039,.138),(0,.146)],(lamp_x,lamp_y,z+.313),'bronze',48)
lathe('Abajur difusor luminoso',[(0,0),(.133,0),(.133,.001),(0,.001)],(lamp_x,lamp_y,z+.313),'led',32)
lathe('Abajur pino topo',[(0,0),(.010,0),(.010,.037),(0,.037)],(lamp_x,lamp_y,z+.457),'bronze',16)

# Dense cascading pothos at upper left, plus narrow leafy stems in the vase.
rng=np.random.default_rng(928);plant_center=(X(508),-.290,Z(314))
vase('Cachepo preto planta pendente',*plant_center,.18,.104,'preto')
for k in range(24):
 theta=k*math.tau/24;start=Vector(plant_center)+Vector((math.cos(theta)*.025,math.sin(theta)*.025,.11))
 length=rng.uniform(.42,.69) if k<12 else rng.uniform(.16,.31);pts=[]
 for j in range(9):
  t=j/8;fall=(max(0,t-.28)/.72)**1.2;pt=start+Vector((math.cos(theta)*.18*math.sin(t*1.7),math.sin(theta)*.10-.030*t,.15*math.sin(t*math.pi)-length*fall));pts.append(pt)
  if j in [1,3,5,7,8]:
   leaf('Folha pothos %d %d'%(k,j),pt,rng.uniform(.055,.088),theta+math.pi*.45)
   if j in [1,3,5]:leaf('Folha pothos par %d %d'%(k,j),pt+Vector((.016*math.cos(theta),-.013,.011)),rng.uniform(.05,.078),theta-math.pi*.35)
 stem('Ramo pothos '+str(k),pts)
for k in range(11):
 start=Vector((X(493),-.299,z+.22));theta=k*2.399;end=start+Vector((math.cos(theta)*rng.uniform(.15,.35),math.sin(theta)*.10,rng.uniform(.17,.35)))
 pts=[start.lerp(end,t/6)+Vector((.018*math.sin(t),0,0)) for t in range(7)];stem('Ramo vaso creme '+str(k),pts)
 for j in range(2,7):
  for side in [-1,1]:leaf('Folha vaso creme %d %d %d'%(k,j,side),pts[j],.085,theta+side*.95,True)

spec['parts']=len(parts);spec['collision_boxes']=solids
bpy.context.view_layer.update();points=np.array([v.co for o in parts for v in o.data.vertices]);spec['local_lo']=points.min(0).tolist();spec['local_hi']=points.max(0).tolist()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'adega_vitrines_editavel.blend'),compress=True)
tx=Matrix.Translation(Vector((spec['placement']['left_x'],spec['placement']['back_y'],spec['placement']['floor_z'])))
root=bpy.data.objects.new(spec['model'],None);bpy.context.scene.collection.objects.link(root);root.sollum_type=SollumType.DRAWABLE;exportparts=[]
for src in parts:
 me=src.data.copy();me.transform(tx);me.update();obj=bpy.data.objects.new(src.name+'_export',me);bpy.context.scene.collection.objects.link(obj);obj.parent=root;convert_obj_to_model(obj);exportparts.append(obj)
points=np.array([v.co for o in exportparts for v in o.data.vertices]);spec['lo']=points.min(0).tolist();spec['hi']=points.max(0).tolist()
with export_context_scope(ExportContext(spec['model'],ExportSettings(targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)))):export_ydr(root).save(O,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),))
for ratio,suffix in [(.52,'medium'),(.22,'low'),(.070,'verylow')]:
 bpy.ops.object.select_all(action='DESELECT');copies=[]
 for src in exportparts:
  obj=src.copy();obj.data=src.data.copy();bpy.context.scene.collection.objects.link(obj);obj.parent=None;obj.select_set(True);copies.append(obj)
 bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();obj=bpy.context.object
 dec=obj.modifiers.new('LOD simplificado','DECIMATE');dec.ratio=ratio;dec.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=dec.name)
 lodroot=bpy.data.objects.new('adega_'+suffix,None);bpy.context.scene.collection.objects.link(lodroot);lodroot.sollum_type=SollumType.DRAWABLE;obj.parent=lodroot;convert_obj_to_model(obj)
 with export_context_scope(ExportContext('adega_'+suffix,ExportSettings(targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)))):export_ydr(lodroot).save(O,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),))
 bpy.data.objects.remove(obj,do_unlink=True);bpy.data.objects.remove(lodroot,do_unlink=True)
(P/'spec.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
print('ADEGA_BUILT',len(parts),'parts',spec['lo'],spec['hi'],flush=True)
