import bpy,bmesh,sys,math,json
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.geometry import tessellate_polygon
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=W/'source_assets/piano_tapetes';OUT=W/'piano_tapetes_fivem';OUT.mkdir(exist_ok=True)
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz']
import numpy as np,addon_utils
from PIL import Image
from shapely.geometry import box as sbox
from shapely.ops import unary_union
bpy.ops.wm.read_factory_settings(use_empty=True);addon_utils.enable('Sollumz',default_set=True)
from Sollumz.sollumz_properties import SollumType
from Sollumz.tools.drawablehelper import convert_obj_to_model
from Sollumz.tools.meshhelper import mesh_add_missing_uv_maps,mesh_add_missing_color_attrs
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.iecontext import ExportContext,ExportSettings,export_context_scope
from Sollumz.ydr.ydrexport import export_ydr
from szio.gta5 import AssetTarget,AssetFormat,AssetVersion
styles={};groups={};current='piano';cols={}
for family in ('black','gold','ivory','felt','leather','nose','fur_edge','wood','bear','carpet'):
 m=create_shader('normal_spec.sps');m.name='piano_tapetes_'+family
 for sampler,suffix in [('DiffuseSampler','d'),('BumpSampler','n'),('SpecSampler','s')]:
  node=m.node_tree.nodes[sampler];im=bpy.data.images.load(str(D/(family+'_'+suffix+'.dds')),check_existing=True)
  if suffix!='d':im.colorspace_settings.name='Non-Color'
  assert len(im.pixels)>0;im.pack();node.image=im;node.texture_properties.embedded=True;m.node_tree.links.new(m.node_tree.nodes['UVMap 0'].outputs['UV'],node.inputs['Vector'])
 for param,value in [('specularIntensityMult',1.0 if family in ('black','gold') else .25),('specularFalloffMult',180 if family in ('black','gold') else 45),('specularFresnel',.55 if family=='black' else .18),('wetnessMultiplier',0),('bumpiness',.6 if family in ('bear','carpet') else .12)]:
  node=m.node_tree.nodes.get(param)
  if node is not None:node.set(0,value)
 styles[family]=m
for name in ('piano','bear','carpet'):
 cols[name]=bpy.data.collections.new('Modelo '+name);bpy.context.scene.collection.children.link(cols[name]);groups[name]=[]
def mesh(name,verts,faces,family,uv=None,smooth=False):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();layer=me.uv_layers.new(name='UVMap 0')
 for p in me.polygons:
  coords=[k for k in range(3) if k!=int(np.argmax(abs(np.array(p.normal))))]
  for li in p.loop_indices:
   idx=me.loops[li].vertex_index;co=me.vertices[idx].co;layer.data[li].uv=uv[idx] if uv is not None else (co[coords[0]],co[coords[1]])
  p.use_smooth=smooth
 me.materials.append(styles[family]);mesh_add_missing_uv_maps(me);mesh_add_missing_color_attrs(me)
 for a in me.color_attributes:a.data.foreach_set('color_srgb',np.tile(np.array([1,1,1,1],np.float32),len(a.data)))
 o=bpy.data.objects.new(name,me);cols[current].objects.link(o);groups[current].append(o);return o
def bevel(o,width=.003,segments=3):
 mod=o.modifiers.new('Bordas reais arredondadas','BEVEL');mod.width=width;mod.segments=segments;bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.modifier_apply(modifier=mod.name);o.select_set(False);return o
def box(name,lo,hi,family='black',rounding=.003):
 x,y,z=lo;X,Y,Z=hi;v=[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)];f=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)];o=mesh(name,v,f,family);return bevel(o,rounding) if rounding else o
def tube(name,points,radius,family='gold',sides=10):
 v=[];f=[];uv=[]
 for k,q in enumerate(points):
  p=Vector(q);t=(Vector(points[min(k+1,len(points)-1)])-Vector(points[max(k-1,0)])).normalized();a=t.cross(Vector((1,0,0)))
  if a.length<.01:a=t.cross(Vector((0,1,0)))
  a.normalize();b=t.cross(a).normalized()
  for i in range(sides):ang=i/sides*math.tau;v.append(p+radius*(a*math.cos(ang)+b*math.sin(ang)));uv.append((i/sides,k*.2))
 for k in range(len(points)-1):
  for i in range(sides):a=k*sides+i;b=k*sides+(i+1)%sides;f.append((a,b,b+sides,a+sides))
 f.extend([tuple(range(sides-1,-1,-1)),tuple((len(points)-1)*sides+i for i in range(sides))]);return mesh(name,v,f,family,uv,True)
def slab(name,outline,za,zb,family):
 n=len(outline);v=[(x,y,za) for x,y in outline]+[(x,y,zb) for x,y in outline];f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
 for i in range(n):j=(i+1)%n;f.append((i,j,j+n,i+n))
 return mesh(name,v,f,family)
def ellipsoid(name,center,radii,family,rings=12,sides=24):
 v=[(center[0],center[1],center[2]-radii[2])];f=[]
 for j in range(1,rings):
  lat=-math.pi/2+j/rings*math.pi
  for i in range(sides):ang=i/sides*math.tau;v.append((center[0]+radii[0]*math.cos(lat)*math.cos(ang),center[1]+radii[1]*math.cos(lat)*math.sin(ang),center[2]+radii[2]*math.sin(lat)))
 v.append((center[0],center[1],center[2]+radii[2]));top=len(v)-1
 for i in range(sides):f.append((0,1+(i+1)%sides,1+i));a=1+(rings-2)*sides+i;b=1+(rings-2)*sides+(i+1)%sides;f.append((top,a,b))
 for j in range(rings-2):
  for i in range(sides):a=1+j*sides+i;b=1+j*sides+(i+1)%sides;f.append((a,b,b+sides,a+sides))
 return mesh(name,v,f,family,smooth=True)
# A real curved grand-piano rim, not a rectangular keyboard with a pasted reference.
controls=[(.77,.22),(.77,.48),(.66,.75),(.43,1.02),(.34,1.54),(.12,1.90),(-.16,2.06),(-.46,2.02),(-.68,1.83),(-.77,1.59),(-.77,.22)]
outline=[(-.77,.22)]
for j in range(len(controls)-1):
 p0=np.array(controls[max(0,j-1)]);p1=np.array(controls[j]);p2=np.array(controls[j+1]);p3=np.array(controls[min(j+2,len(controls)-1)])
 for k in range(8):
  t=k/8;q=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t);outline.append(tuple(q))
outline.append(controls[-1]);outline=outline[:-1] # closes against the first point
inner=[(x*.932,.95+(y-.95)*.945) for x,y in outline];n=len(outline)
v=[(x,y,z) for z in (.768,.998) for ring in (outline,inner) for x,y in ring];f=[]
for i in range(n):
 j=(i+1)%n;f.extend([(i,j,j+2*n,i+2*n),(i+n,i+3*n,j+3*n,j+n),(i+2*n,j+2*n,j+3*n,i+3*n),(i,i+n,j+n,j)])
rim=mesh('Aro curvo preto laqueado com espessura',v,f,'black',smooth=True)
rim.data.set_sharp_from_angle(angle=math.radians(40))
slab('Fundo estrutural da caixa harmonica',outline,.738,.772,'black');slab('Tabua harmonica de madeira',inner,.782,.826,'wood')
for z,r in [(.999,.005),(.772,.004)]:tube('Filete de acabamento no aro '+str(z),[(x,y,z) for x,y in outline]+[(outline[0][0],outline[0][1],z)],r,'gold',8)
tube('Moldura dourada da chapa',[(x,y,.883) for x,y in inner]+[(inner[0][0],inner[0][1],.883)],.014,'gold',12)
box('Cepo de afinacao',(-.665,.275,.834),(.652,.419,.904),'wood',.007)
for j,(a,b) in enumerate([((-.64,.42,.862),(-.54,1.79,.862)),((-.43,.42,.866),(.06,1.87,.866)),((-.12,.42,.870),(.33,1.46,.870)),((.32,.42,.874),(.47,.98,.874))]):tube('Travessa fundida dourada %d'%j,[a,b],.021,'gold',10)
box('Ponte de agudos',(-.05,.56,.835),(.64,.584,.86),'wood')
strings=180
for i in range(strings):
 t=i/(strings-1);sx=-.65+1.27*t;ex=-.60+.92*t;ey=1.80-1.00*t;sy=.42+(i%3)*.011
 tube('Corda de piano %03d'%i,[(sx,sy,.911),(ex,ey,.891)],.00075 if i<45 else .00050,'gold',6)
 tube('Pino afinacao %03d'%i,[(sx,sy-.04,.897),(sx,sy-.04,.924)],.003,'gold',8)
# 52 individual white keys and 36 raised black keys, in the A0-C8 sequence.
white=[m for m in range(21,109) if m%12 not in (1,3,6,8,10)];keyw=.0235;kw=len(white)*keyw;left=-kw/2
box('Mesa do teclado',(-.77,-.330,.669),(.77,.228,.719),'black',.008)
box('Frente do teclado',(-.77,-.342,.645),(.77,-.301,.690),'black',.005)
for i,note in enumerate(white):
 x=left+i*keyw;box('Tecla branca MIDI %03d'%note,(x+.0005,-.283,.720),(x+keyw-.0005,.080,.742),'ivory',.001)
for note in range(21,109):
 if note in white:continue
 i=sum(m<note for m in white);x=left+i*keyw;box('Tecla preta MIDI %03d'%note,(x-.0073,-.104,.742),(x+.0073,.084,.765),'black',.0015)
box('Feltro vermelho atras das teclas',(-.64,.080,.737),(.64,.098,.751),'felt',.0005)
box('Feltro vermelho perto das cordas',(-.63,.427,.896),(.63,.435,.904),'felt',.0005)
for side in (-1,1):
 profile=[(-.335,.690),(-.335,.774),(-.28,.800),(-.19,.810),(-.09,.826),(.04,.880),(.16,.964),(.227,.990),(.227,.675)]
 x0=.665*side;x1=.778*side;vv=[(x,y,z) for x in (x0,x1) for y,z in profile];nn=len(profile);ff=[tuple(range(nn-1,-1,-1)),tuple(range(nn,2*nn))]
 for j in range(nn):k=(j+1)%nn;ff.append((j,k,k+nn,j+nn))
 bevel(mesh('Braco curvo do teclado '+str(side),vv,ff,'black'),.003)
box('Faixa fallboard laqueado',(-.66,.102,.746),(.66,.202,.954),'black',.01)
tube('Filete dourado do teclado',[(-.65,.098,.944),(.65,.098,.944)],.0025,'gold',8)
# Raised music desk, tilted back, on a separate adjustable support.
desk=box('Estante de partituras',(-.355,-.012,0),(.355,.012,.302),'black',.006);desk.rotation_euler.x=math.radians(-18);desk.location=(0,.229,.962)
box('Apoio das partituras',(-.36,.181,.958),(.36,.258,.977),'black',.004)
for x in (-.27,.27):tube('Suporte estante '+str(x),[(x,.243,.964),(x,.333,1.18)],.007,'black')
# Open lid rotates around its long left hinge; the matching inner finish is visible.
lid=slab('Tampa curva aberta',outline,0,.030,'black');lid.data.transform(Matrix.Translation((.77,0,0)));lid.location=(-.77,0,1.012);lid.rotation_euler.y=math.radians(-43)
under=slab('Acabamento interno da tampa',[(x*.98,.95+(y-.95)*.98) for x,y in outline],-.002,0,'black');under.data.transform(Matrix.Translation((.77,0,0)));under.location=lid.location;under.rotation_euler=lid.rotation_euler
for y in (.48,1.08,1.67):tube('Dobradica dourada da tampa '+str(y),[(-.766,y-.055,1.01),(-.766,y+.055,1.01)],.011,'gold',12)
bpy.context.view_layer.update();end=lid.matrix_world@Vector((.66,.62,0));tube('Haste sustentacao tampa',[(.64,.62,.992),end],.015,'black',16)
ellipsoid('Articulacao dourada da haste',(.64,.62,.990),(.034,.028,.009),'gold',8,16)
# Three shaped legs, brass caster wheels, and a three-pedal lyre.
legs=[(-.650,-.216),(.650,-.216),(-.37,1.74)]
for j,(x,y) in enumerate(legs):
 vv=[];ff=[];profile=[(.112,.064),(.19,.056),(.40,.068),(.63,.091),(.743,.12)]
 for z,r in profile:vv.extend([(x-r,y-r,z),(x+r,y-r,z),(x+r,y+r,z),(x-r,y+r,z)])
 for k in range(len(profile)-1):
  for a in range(4):b=(a+1)%4;ff.append((k*4+a,k*4+b,(k+1)*4+b,(k+1)*4+a))
 ff.extend([(3,2,1,0),tuple(range((len(profile)-1)*4,len(profile)*4))]);bevel(mesh('Perna esculpida %d'%j,vv,ff,'black'),.005)
 box('Faixa dourada perna %d'%j,(x-.065,y-.065,.128),(x+.065,y+.065,.139),'gold',.001)
 tube('Roda dourada %d'%j,[(x-.024,y,.047),(x+.024,y,.047)],.046,'gold',24)
 tube('Eixo roda %d'%j,[(x-.028,y,.047),(x+.028,y,.047)],.013,'black',16)
 for side in (-1,1):box('Garfo rodizio %d %d'%(j,side),(x+side*.025-.007,y-.032,.045),(x+side*.025+.007,y+.032,.116),'gold',.007)
box('Base da lira pedais',(-.15,-.053,.094),(.15,.142,.145),'black',.006)
box('Topo da lira pedais',(-.14,-.017,.625),(.14,.131,.68),'black',.005)
for x in (-.102,0,.102):
 tube('Coluna da lira '+str(x),[(x,.080,.145),(x,.080,.647)],.017,'gold',12)
 tube('Pedal curvo '+str(x),[(x,.058,.144),(x,-.015,.101),(x,-.125,.077),(x,-.20,.079)],.014,'gold',16)
 ellipsoid('Ponta pedal '+str(x),(x,-.20,.079),(.026,.043,.012),'gold',8,16)
# Proportional black upholstered bench accompanies the instrument.
box('Banco assento estofado',(-.46,-.920,.443),(.46,-.555,.495),'leather',.022)
box('Banco caixa laqueada',(-.447,-.907,.403),(.447,-.568,.446),'black',.008)
for j,(x,y) in enumerate([(-.388,-.853),(.388,-.853),(-.388,-.622),(.388,-.622)]):
 box('Perna banco %d'%j,(x-.029,y-.029,.003),(x+.029,y+.029,.410),'black',.004)
 box('Ponteira banco %d'%j,(x-.031,y-.031,.003),(x+.031,y+.031,.017),'gold',.001)
for x in (-.26,0,.26):ellipsoid('Botao estofado '+str(x),(x,-.737,.493),(.008,.008,.002),'leather',6,12)
# Bear-hide rug: photo UVs on a real cut silhouette and a raised head/muzzle.
current='bear';spec=json.loads((W/'piano_tapetes.json').read_text());width=spec['models']['bear']['width_m'];height=width*spec['bear_ratio'];mask=Image.open(D/'bear_mask.png').resize((192,round(192*spec['bear_ratio'])),Image.Resampling.NEAREST);a=np.array(mask)>127;H,IW=a.shape;rows=[]
for j,row in enumerate(a):
 runs=np.flatnonzero(np.diff(np.r_[False,row,False].astype(int)))
 for l,r in zip(runs[::2],runs[1::2]):rows.append(sbox(l/IW*width-width/2,(1-(j+1)/H)*height-height/2,r/IW*width-width/2,(1-j/H)*height-height/2))
poly=unary_union(rows);poly=max(list(poly.geoms),key=lambda p:p.area) if poly.geom_type=='MultiPolygon' else poly;poly=poly.buffer(.002).buffer(-.002).simplify(.003,preserve_topology=True)
outline_bear=list(poly.exterior.coords)[:-1];pv=[Vector((x,y,0)) for x,y in outline_bear];tris=tessellate_polygon([pv]);verts=[];faces=[];lookup={}
for tri in tris:
 ids=[]
 for p in tri:
  if isinstance(p,int):p=pv[p]
  key=(round(p.x,7),round(p.y,7));idx=lookup.get(key)
  if idx is None:idx=len(verts);lookup[key]=idx;verts.append(p[:])
  ids.append(idx)
 faces.append(tuple(ids))
me=bpy.data.meshes.new('Recorte urso malha base');me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=7,use_grid_fill=True);bm.to_mesh(me);bm.free();me.update();top=[]
for vtx in me.vertices:
 x,y=vtx.co.x,vtx.co.y;head=.152*math.exp(-((x/.253)**2+((y+height*.275)/.248)**2)*1.4);muzzle=.063*math.exp(-((x/.135)**2+((y+height*.407)/.138)**2)*1.5);ears=sum(.052*math.exp(-(((x-s*.205)/.086)**2+((y+height*.10)/.095)**2)*2) for s in (-1,1));fold=.0035*(1+math.sin(14*x+3*y))*math.exp(-(x/1.05)**2)
 top.append((x,y,.010+head+muzzle+ears+fold))
me.calc_loop_triangles();ff=[tuple(t.vertices) for t in me.loop_triangles];n=len(top);uv=[(x/width+.5,y/height+.5) for x,y,z in top];allv=top+[(x,y,.002) for x,y,z in top];alluv=uv+uv;allf=ff+[tuple(i+n for i in reversed(f)) for f in ff]
edges={}
for face in ff:
 for i,j in zip(face,face[1:]+face[:1]):key=tuple(sorted((i,j)));edges[key]=edges.get(key,0)+1
for (i,j),c in edges.items():
 if c==1:allf.append((i,i+n,j+n,j))
hide=mesh('Tapete urso - pelagem recortada e cabeca volumetrica',allv,allf,'bear',alluv,True);hide.data.materials.append(styles['fur_edge'])
for polygon in hide.data.polygons:
 if polygon.index>=len(ff):polygon.material_index=1
bpy.data.meshes.remove(me)
ny=-height*.429;nz=.01+.152*math.exp(-((ny+height*.275)/.248)**2*1.4)+.063*math.exp(-((ny+height*.407)/.138)**2*1.5)
ellipsoid('Nariz volumetrico do urso',(0,ny,nz+.013),(.063,.047,.031),'nose',12,24)
for x in (-.029,.029):ellipsoid('Narina '+str(x),(x,ny-.034,nz+.013),(.011,.006,.008),'black',8,16)
# Woven ornamental rug preserves the reference aspect ratio and has a closed hem.
current='carpet';cw=spec['models']['carpet']['width_m'];ch=cw*spec['carpet_ratio'];nx=64;nyg=76;v=[];uv=[];f=[]
for j in range(nyg+1):
 for i in range(nx+1):
  x=(i/nx-.5)*cw;y=(j/nyg-.5)*ch;z=.010+.0007*math.sin(x*31)*math.sin(y*29);v.append((x,y,z));uv.append((i/nx,j/nyg))
for j in range(nyg):
 for i in range(nx):a=j*(nx+1)+i;b=a+nx+1;f.append((a,a+1,b+1,b))
n=len(v);v+= [(x,y,.002) for x,y,z in v];uv+=list(uv);f+= [tuple(i+n for i in reversed(q)) for q in list(f)]
edge=[i for i in range(nx+1)]+[j*(nx+1)+nx for j in range(1,nyg+1)]+[nyg*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(nyg-1,0,-1)]
for i,j in zip(edge,edge[1:]+edge[:1]):f.append((i,i+n,j+n,j))
mesh('Tapete estampado tecido com borda espessa',v,f,'carpet',uv,True)
# Independent native props and one combined editable Blender source.
bpy.context.view_layer.update();targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
for family,parts in groups.items():
 row=spec['models'][family];ps=np.array([o.matrix_world@v.co for o in parts for v in o.data.vertices]);triangles=0
 for o in parts:o.data.calc_loop_triangles();triangles+=len(o.data.loop_triangles)
 row.update(lo=ps.min(0).tolist(),hi=ps.max(0).tolist(),dimensions=(ps.max(0)-ps.min(0)).tolist(),authored_triangles=triangles,parts=len(parts))
spec['models']['piano'].update(white_keys=52,black_keys=36,strings=strings,lid_angle_degrees=43,body_outline=outline,leg_centers=legs,bench_box=[[-.46,-.92,0],[.46,-.555,.495]],body_height=[.738,.998])
spec['models']['bear'].update(length_m=height,head_height_m=max(p[2] for p in top),head_center=[0,-height*.275],closed_geometry=True)
spec['models']['carpet'].update(length_m=ch,thickness_m=.008,closed_geometry=True)
bpy.ops.wm.save_as_mainfile(filepath=str(W/'piano_tapetes_autorais.blend'))
for family,parts in groups.items():
 row=spec['models'][family];root=bpy.data.objects.new(row['name'],None);bpy.context.scene.collection.objects.link(root);root.sollum_type=SollumType.DRAWABLE
 for src in parts:
  me=src.data.copy();me.transform(src.matrix_world);ob=bpy.data.objects.new(src.name+'_export',me);bpy.context.scene.collection.objects.link(ob);ob.parent=root;convert_obj_to_model(ob)
 with export_context_scope(ExportContext(row['name'],ExportSettings(targets=targets))):export_ydr(root).save(OUT,targets)
 print('PROP_BUILT',family,row['parts'],row['authored_triangles'],row['dimensions'],flush=True)
(W/'piano_tapetes.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
