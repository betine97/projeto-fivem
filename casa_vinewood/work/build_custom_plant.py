"""A fully volumetric reference-driven plant: lathed pot, tapered branches, curved leaf shells."""
import bpy,bmesh,sys,json,math,random
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=W/'source_assets/vaso_planta';OUT=W/'vaso_fivem';OUT.mkdir(exist_ok=True)
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz']
import numpy as np,addon_utils
bpy.ops.wm.read_factory_settings(use_empty=True)
from PIL import Image
addon_utils.enable('Sollumz',default_set=True)
from Sollumz.sollumz_properties import SollumType
from Sollumz.tools.drawablehelper import convert_obj_to_model
from Sollumz.tools.meshhelper import mesh_add_missing_uv_maps,mesh_add_missing_color_attrs
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.iecontext import ExportContext,ExportSettings,export_context_scope
from Sollumz.ydr.ydrexport import export_ydr
from szio.gta5 import AssetTarget,AssetFormat,AssetVersion
random.seed(903)
col=bpy.data.collections.new('Vaso autoral - modelo');bpy.context.scene.collection.children.link(col)
styles={}
for family in ('pot','bark','leaves','soil'):
 m=create_shader('normal_spec.sps');m.name='vaso_autoral_'+family
 for sampler,suffix in [('DiffuseSampler','diffuse'),('BumpSampler','normal'),('SpecSampler','spec')]:
  tx=m.node_tree.nodes[sampler];im=bpy.data.images.load(str(D/(family+'_'+suffix+'.dds')),check_existing=False)
  if suffix!='diffuse':im.colorspace_settings.name='Non-Color'
  assert len(im.pixels)>0;im.pack();tx.image=im;tx.texture_properties.embedded=True
  m.node_tree.links.new(m.node_tree.nodes['UVMap 0'].outputs['UV'],tx.inputs['Vector'])
 for param,value in [('specularIntensityMult',.5 if family=='leaves' else .13),('specularFalloffMult',70 if family=='leaves' else 18),('specularFresnel',.12),('wetnessMultiplier',0),('bumpiness',.7)]:
  node=m.node_tree.nodes.get(param)
  if node is not None:node.set(0,value)
 styles[family]=m
parts=[]
def mesh(name,verts,faces,uvs,family):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 assert np.max(abs(np.array([p.co for p in me.vertices])-np.array(verts)))<1e-6,name
 uv=me.uv_layers.new(name='UVMap 0')
 for loop in me.loops:uv.data[loop.index].uv=uvs[loop.vertex_index]
 for p in me.polygons:p.use_smooth=True
 me.set_sharp_from_angle(angle=math.radians(55))
 me.materials.append(styles[family]);mesh_add_missing_uv_maps(me);mesh_add_missing_color_attrs(me)
 shade=.55 if family=='leaves' else .72 if family=='pot' else .78 if family=='bark' else 1.0
 for attr in me.color_attributes:attr.data.foreach_set('color_srgb',np.tile(np.array([shade,shade,shade,1],np.float32),len(attr.data)))
 o=bpy.data.objects.new(name,me);col.objects.link(o);parts.append(o);return o
# Closed ceramic shell, rounded sides, a real 28 mm rim and a deep inner cavity.
profile=[(.215,0),(.237,.012),(.256,.035),(.278,.075),(.302,.14),(.322,.24),(.331,.34),(.329,.43),(.319,.51),(.307,.58),(.296,.621),(.29,.63),(.266,.632),(.259,.62),(.26,.59),(.27,.52),(.278,.40),(.271,.24),(.232,.07),(.215,.045)]
v=[];f=[];uv=[];N=96
for k,(r,z) in enumerate(profile):
 for i in range(N+1):
  ang=i/N*2*math.pi;v.append((r*math.cos(ang),r*math.sin(ang),z))
  # Project a clean central region of the supplied pot texture around the circumference.
  uv.append((i/N*6.0,z/.33))
for k in range(len(profile)-1):
 for i in range(N):
  a=k*(N+1)+i;b=a+N+1;f.append((a,a+1,b+1,b))
bottom=len(v);v.append((0,0,0));uv.append((.5,.27));inner=len(v);v.append((0,0,.045));uv.append((.5,.30))
for i in range(N):f.append((bottom,i+1,i));a=(len(profile)-1)*(N+1)+i;f.append((inner,a,a+1))
mesh('Vaso ceramica grafite - parede e borda espessas',v,f,uv,'pot')
# Soil plus irregular pebbles inside the opening.
v=[(0,0,.579)];uv=[(.5,.5)];f=[]
for i in range(64):
 a=i/64*2*math.pi;v.append((.263*math.cos(a),.263*math.sin(a),.579));uv.append((.5+.49*math.cos(a),.5+.49*math.sin(a)))
for i in range(64):f.append((0,1+i,1+(i+1)%64))
mesh('Terra no interior do vaso',v,f,uv,'soil')
# Low-poly grains add actual relief at the visible soil surface.
v=[];f=[];uv=[]
for i in range(65):
 a=random.uniform(0,math.tau);r=random.uniform(.035,.253);cx=r*math.cos(a);cy=r*math.sin(a);sx=random.uniform(.003,.008);sy=random.uniform(.003,.008);sz=random.uniform(.002,.006);start=len(v)
 for p in [(0,0,1),(1,0,0),(0,1,0),(-1,0,0),(0,-1,0),(0,0,-1)]:v.append((cx+p[0]*sx,cy+p[1]*sy,.581+p[2]*sz));uv.append((random.random(),random.random()))
 for j in range(4):f.append((start,start+1+j,start+1+(j+1)%4));f.append((start+5,start+1+(j+1)%4,start+1+j))
mesh('Graos e pequenas pedras no substrato',v,f,uv,'soil')
def tubes(name,paths,family):
 v=[];f=[];uv=[]
 for points,radii in paths:
  start=len(v);side=10
  for k,p in enumerate(points):
   tangent=Vector(points[min(k+1,len(points)-1)])-Vector(points[max(k-1,0)]);tangent.normalize();a=tangent.cross(Vector((0,1,0))).normalized();b=tangent.cross(a).normalized()
   for i in range(side+1):
    t=i/side*2*math.pi;q=Vector(p)+radii[k]*(math.cos(t)*a+math.sin(t)*b);v.append(q)
    uv.append((.477+.056*i/side,.11+.19*k/(len(points)-1)))
  for k in range(len(points)-1):
   for i in range(side):
    c=start+k*(side+1)+i;d=c+side+1;f.append((c,c+1,d+1,d))
  f.append(tuple(start+i for i in range(side-1,-1,-1)));last=start+(len(points)-1)*(side+1);f.append(tuple(last+i for i in range(side)))
 return mesh(name,v,f,uv,family)
stems=[];branches=[];leafsites=[]
for j in range(6):
 angle=j*2*math.pi/6+.24;rad=Vector((math.cos(angle),math.sin(angle),0));height=random.uniform(1.23,1.45)
 pts=[]
 for k in range(9):
  t=k/8;p=rad*(.07+.145*t**1.4)+Vector((.02*math.sin(t*5+j),.016*math.sin(t*4-j),.57+height*t));pts.append(p)
 stems.append((pts,[.026*(1-k/8)**.8+.004 for k in range(9)]))
 for tier in range(6):
  t=.28+tier*.115;start=rad*(.07+.145*t**1.4)+Vector((.02*math.sin(t*5+j),.016*math.sin(t*4-j),.57+height*t))
  az=angle+tier*2.4+random.uniform(-.4,.4);direction=Vector((math.cos(az),math.sin(az),0));length=random.uniform(.24,.36)
  end=start+direction*length+Vector((0,0,random.uniform(.10,.20)))
  if Vector((end.x,end.y,0)).length>.48:
   xy=Vector((end.x,end.y,0)).normalized()*.48;end.x=xy.x;end.y=xy.y
  branch=[start.lerp(end,k/4)+Vector((0,0,-.025*math.sin(k/4*math.pi))) for k in range(5)]
  branches.append((branch,[.008*(1-k/4)+.0018 for k in range(5)]))
  for leaf in range(8):
   u=.12+leaf*.115;base=start.lerp(end,u);la=az+(.95 if leaf%2 else -.95)+random.uniform(-.45,.45)
   pitch=random.uniform(-.95,.35)+(tier/5)*.35;axis=Vector((math.cos(la)*math.cos(pitch),math.sin(la)*math.cos(pitch),math.sin(pitch))).normalized()
   size=random.uniform(.22,.33);roll=random.choice((-1,1))*random.uniform(.65,1.3);leafsites.append((base,axis,size,roll,random.randrange(4)))
   pet=base+axis*.032;branches.append(([base,pet],[.002,.001]))
 for n in range(3):
  az=angle+n*2;axis=Vector((math.cos(az)*.35,math.sin(az)*.35,.82)).normalized();leafsites.append((pts[-1]-Vector((0,0,.055*n)),axis,random.uniform(.23,.30),random.uniform(-.5,.5),j%4))
tubes('Seis troncos curvos com casca',stems,'bark');tubes('Ramos afilados e peciolos',branches,'bark')
# The outline and UVs follow each individual reference leaf, with a curved closed shell.
atlas=np.array(Image.open(D/'leaves.png'));H,IW=atlas.shape[:2]
rects=[(6,22,324,609),(337,20,620,609),(638,15,934,608),(947,18,1245,605)]
outlines=[]
for x0,y0,x1,y1 in rects:
 valid=[]
 for y in range(y0,y1):
  rgb=atlas[y,x0:x1,:3].astype(float);mask=(rgb[:,1]>25)&(rgb[:,1]>rgb[:,0]*.65)&(rgb[:,1]>rgb[:,2]*1.05)
  runs=np.flatnonzero(np.diff(np.r_[False,mask,False].astype(int)));pairs=list(zip(runs[::2],runs[1::2]))
  if pairs:
   a,b=max(pairs,key=lambda ab:ab[1]-ab[0])
   if b-a>3:valid.append((y,x0+a+1,x0+b-2))
 assert valid
 top=valid[0][0];bottom=valid[-1][0]
 rows=[]
 for k in range(11):
  target=bottom-(bottom-top)*k/10;y,left,right=min(valid,key=lambda row:abs(row[0]-target))
  if right-left<2:right=left+2
  rows.append((left,right,y))
 outlines.append(rows)
v=[];f=[];uv=[]
for base,axis,L,roll,index in leafsites:
 side=axis.cross(Vector((0,0,1))).normalized();up=side.cross(axis).normalized();side,up=side*math.cos(roll)+up*math.sin(roll),up*math.cos(roll)-side*math.sin(roll)
 rows=outlines[index];wid=max(b-a for a,b,y in rows);start=len(v);ncols=5;nr=len(rows);layer=nr*ncols
 for back in range(2):
  for k,(left,right,y) in enumerate(rows):
   t=k/(nr-1)
   for c in range(ncols):
    s=c/(ncols-1)*2-1;x=left+(right-left)*c/(ncols-1);span=(right-left)/wid*L*.25
    # Central keel, curled edges, a slight asymmetric twist and drooping leaf tip.
    curl=L*(.035*math.sin(math.pi*t)-.07*t*t-.018*abs(s)**1.6*math.sin(math.pi*t)+.014*s*t)
    q=base+axis*(.032+t*L)+side*(s*span)+up*(curl-back*.0007)
    v.append(q);uv.append((x/IW,1-y/H))
 for k in range(nr-1):
  for c in range(ncols-1):
   a=start+k*ncols+c;b=a+ncols;f.append((a,a+1,b+1,b));f.append((a+layer,b+layer,b+1+layer,a+1+layer))
 edge=[start+i for i in range(ncols)]+[start+k*ncols+ncols-1 for k in range(1,nr)]+[start+(nr-1)*ncols+i for i in range(ncols-2,-1,-1)]+[start+k*ncols for k in range(nr-2,0,-1)]
 for a,b in zip(edge,edge[1:]+edge[:1]):f.append((a,a+layer,b+layer,b))
mesh('Folhagem curva - folhas individuais de dupla face',v,f,uv,'leaves')
spec=json.loads((W/'vaso_planta_autoral.json').read_text());ps=np.array([o.matrix_world@p.co for o in parts for p in o.data.vertices]);lo=ps.min(0);hi=ps.max(0)
triangles=0
for o in parts:o.data.calc_loop_triangles();triangles+=len(o.data.loop_triangles)
spec.update(lo=lo.tolist(),hi=hi.tolist(),dimensions=(hi-lo).tolist(),pot_height_m=.632,pot_diameter_m=.662,pot_wall_thickness_m=.028,leaves=len(leafsites),main_trunks=6,triangles=triangles,leaf_geometry_closed=True,reference_uv_mapping=True,texture_resolution=2048)
(W/'vaso_planta_autoral.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(W/'vaso_planta_autoral.blend'))
root=bpy.data.objects.new(spec['model'],None);bpy.context.scene.collection.objects.link(root);root.sollum_type=SollumType.DRAWABLE
for src in parts:
 ob=bpy.data.objects.new(src.name+'_export',src.data.copy());bpy.context.scene.collection.objects.link(ob);ob.parent=root;convert_obj_to_model(ob)
targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
with export_context_scope(ExportContext(spec['model'],ExportSettings(targets=targets))):export_ydr(root).save(OUT,targets)
print('CUSTOM_PLANT_BUILT',triangles,'triangles;',len(leafsites),'leaves; bounds',lo,hi,flush=True)
