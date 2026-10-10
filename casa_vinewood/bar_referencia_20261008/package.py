import sys,json,re,struct,hashlib,shutil
from pathlib import Path
P=Path(__file__).resolve().parent; W=P.parent; R=W.parent; O=P/'stream'; D=R/'server-data/resources/cidade_mansao'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
from szio.gta5.bounds import *
from szio.gta5.maps import *
from szio.gta5.entities import *
from szio.types import Vector,Quaternion,DataSource
spec=json.loads((P/'spec.json').read_text());origin=np.array(spec['origin']);target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
def load(p):
 a=try_load_asset(p);assert a is not None,p;return a
def bounds(a,lod=LodLevel.HIGH):
 ps=np.concatenate([g.vertex_buffer['Position'] for m in a.models[lod] for g in m.geometries]);return ps.min(0),ps.max(0)
def shaderkey(s):return s.preset_filename,tuple((p.name,p.value) for p in s.parameters if isinstance(p.value,str))
a=load(O/(spec['model']+'.ydr'));stats={}
for lod,name in [(LodLevel.HIGH,spec['model']),(LodLevel.MEDIUM,'bar_medium'),(LodLevel.LOW,'bar_low'),(LodLevel.VERYLOW,'bar_verylow')]:
 variant=load(O/(name+'.ydr'));mapping={i:next(j for j,s in enumerate(a.shader_group.shaders) if shaderkey(s)==shaderkey(old)) for i,old in enumerate(variant.shader_group.shaders)}
 count=0;degenerate=0
 for m in variant.models[LodLevel.HIGH]:
  for g in m.geometries:
   g.shader_index=mapping[g.shader_index];vb=g.vertex_buffer.copy();ids=g.index_buffer.reshape(-1,3);ts=vb['Position'][ids];area=np.linalg.norm(np.cross(ts[:,1]-ts[:,0],ts[:,2]-ts[:,0]),axis=1)
   keep=area>1e-12;degenerate+=int(sum(~keep));g.index_buffer=ids[keep].reshape(-1).copy();count+=len(g.index_buffer)//3
   if 'Tangent' in vb.dtype.names:
    bad=np.flatnonzero(np.linalg.norm(vb['Tangent'][:,:3],axis=1)<.5)
    if len(bad):
     n=vb['Normal'][bad];axis=np.eye(3)[np.argmin(abs(n),axis=1)];t=np.cross(axis,n);t/=np.maximum(np.linalg.norm(t,axis=1,keepdims=True),1e-9);vb['Tangent'][bad,:3]=t;vb['Tangent'][bad,3]=1
   g.vertex_buffer=vb
 a.models[lod]=variant.models[LodLevel.HIGH];stats[lod.name]={'triangles':count,'degenerate_removed':degenerate}
a.lod_thresholds={LodLevel.HIGH:18.,LodLevel.MEDIUM:35.,LodLevel.LOW:65.,LodLevel.VERYLOW:120.}
for name,tx in list(a.shader_group.embedded_textures.items()):
 f=P/'textures'/(name+'.dds');data=f.read_bytes();h,w=struct.unpack_from('<II',data,12);a.shader_group.embedded_textures[name]=EmbeddedTexture(name,w,h,DataSource.create(data,name=name+'.dds'))
names=re.findall(r'CollisionMaterialDef\("([A-Z_0-9]+)"',Path(r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz/Sollumz/ybn/collision_materials.py').read_text())
fs=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
b=AssetBoundBvh();b.margin=.002;b.composite_collision_type_flags=CollisionFlags.MAP_TYPE_WEAPON|CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_HORSE|CollisionFlags.MAP_TYPE_COVER|CollisionFlags.MAP_TYPE_VEHICLE;b.composite_collision_include_flags=CollisionFlags(0xffffffff)
ps=[];faces=[]
def world(v):return np.array([spec['design_start_x']-v[0],spec['model_wall_y']-v[1],spec['floor_z']+v[2]])
for q in spec['collision_boxes']:
 x,y,z=q['lo'];X,Y,Z=q['hi'];n=len(ps);ps.extend(world(p) for p in [(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)]);faces.extend(tuple(n+i for i in f) for f in fs)
b.geometry_vertices=[BoundVertex(Vector(p),None) for p in ps];b.geometry_primitives=[BoundPrimitive.new_triangle(*f,CollisionMaterial.from_packed(names.index('WOOD_SOLID_MEDIUM'))) for f in faces]
def setbounds(b,lo,hi):
 b.bb_min=Vector(lo);b.bb_max=Vector(hi);b.centroid=Vector((lo+hi)/2);b.cg=b.centroid;b.radius_around_centroid=float(np.linalg.norm(hi-lo)/2)
setbounds(b,np.min(ps,0),np.max(ps,0));comp=AssetBoundComposite(children=[b]);setbounds(comp,np.min(ps,0),np.max(ps,0));a.bounds=comp
save_asset(a,target,O,spec['model']);lo,hi=bounds(a)
ar=Archetype(spec['model'],ArchetypeType.BASE,32,120,0,120,'','','',spec['model'],Vector(lo),Vector(hi),Vector((lo+hi)/2),float(np.linalg.norm(hi-lo)/2),spec['model'],ArchetypeAssetType.DRAWABLE,[])
save_asset(AssetMapTypes(name='mansao_bar_referencia',archetypes=[ar]),target,O,'mansao_bar_referencia')
e=Entity(spec['model'],Vector(origin),Quaternion((1,0,0,0)),1,1,EntityFlags.IS_STATIC,0,-1,120,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[])
save_asset(AssetMapData(name='mansao_bar_referencia',content_flags=MapContentFlags.HAS_ENTITIES_HD|MapContentFlags.HAS_PHYSICS,entities=[e],streaming_extents=(Vector(origin+lo-125),Vector(origin+hi+125)),entities_extents=(Vector(origin+lo-.01),Vector(origin+hi+.01))),target,O,'mansao_bar_referencia')
# A separate camera-only world bound for this fixed fitted cabinet. No changes
# to the mansion's existing world bounds or moving furniture collision.
cam=AssetBoundBvh();cam.margin=.005;cam.composite_collision_type_flags=b.composite_collision_type_flags;cam.composite_collision_include_flags=CollisionFlags.CAMERA_TEST
cam.geometry_vertices=[BoundVertex(Vector(p+origin),None) for p in ps];cam.geometry_primitives=[BoundPrimitive.new_triangle(*f,CollisionMaterial.from_packed(names.index('WOOD_SOLID_MEDIUM'))) for f in faces]
setbounds(cam,np.min(ps,0)+origin,np.max(ps,0)+origin);cw=AssetBoundComposite(children=[cam]);setbounds(cw,np.min(ps,0)+origin,np.max(ps,0)+origin)
save_asset(cw,target,O,'mansao_bar_referencia')
# Rug expansion changes only this drawable and its archetype. Existing player-
# saved position/rotation and the other piano/rug archetypes remain untouched.
B=P/'backup_antes';B.mkdir(exist_ok=True)
for name in ['mansao_tapete_urso.ydr','mansao_piano_tapetes.ytyp']:
 if not (B/name).exists():shutil.copy2(D/'stream'/name,B/name)
bear=load(B/'mansao_tapete_urso.ydr');oldlo,oldhi=bounds(bear);scale=1.5
for models in bear.models.values():
 for m in models:
  for g in m.geometries:
   vb=g.vertex_buffer.copy();vb['Position']*=scale;g.vertex_buffer=vb
def scale_bounds(b):
 if hasattr(b,'children'):
  for c in b.children:
   if c is not None:scale_bounds(c)
 if hasattr(b,'geometry_vertices'):
  for v in b.geometry_vertices:v.co=Vector(np.array(v.co)*scale)
 setbounds(b,np.array(b.bb_min)*scale,np.array(b.bb_max)*scale)
if bear.bounds:scale_bounds(bear.bounds)
save_asset(bear,target,O,'mansao_tapete_urso');newlo,newhi=bounds(bear)
types=load(B/'mansao_piano_tapetes.ytyp');row=next(t for t in types.archetypes if str(t.name)=='mansao_tapete_urso');row.bb_min=Vector(newlo);row.bb_max=Vector(newhi);row.bs_center=Vector((newlo+newhi)/2);row.bs_radius=float(np.linalg.norm(newhi-newlo)/2)
save_asset(types,target,O,'mansao_piano_tapetes')
spec['lods']=stats;spec['collision_triangles']=len(faces);spec['bear_resize']={'factor':scale,'old_dimensions':(oldhi-oldlo).tolist(),'new_dimensions':(newhi-newlo).tolist(),'lo':newlo.tolist(),'hi':newhi.tolist(),'uv_and_textures_preserved':True,'saved_pose_preserved':True}
(P/'spec.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
for name in [spec['model']+'.ydr','mansao_bar_referencia.ytyp','mansao_bar_referencia.ymap','mansao_bar_referencia.ybn','mansao_tapete_urso.ydr','mansao_piano_tapetes.ytyp']:assert load(O/name)
print('BAR_PACKAGE_READY',stats,'bear',(newhi-newlo).tolist(),flush=True)
