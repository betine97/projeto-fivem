import sys,json,re,math,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];W=ROOT/'casa_vinewood';OUT=W/'fivem'
sys.path[:0]=[str(ROOT/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
from szio.gta5.bounds import *
from szio.gta5.entities import *
from szio.gta5.maps import *
from szio.types import Vector,Quaternion
targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
origin=np.array(json.loads((W/'medidas_estudo.json').read_text())['native_origin'])
export=json.loads((W/'exportacao_fivem.json').read_text());models=export['models'];dynamic_models=export.get('dynamic_models',[])
names=re.findall(r'CollisionMaterialDef\("([A-Z_0-9]+)"',Path(r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz/Sollumz/ybn/collision_materials.py').read_text())
wood_index=names.index('WOOD_SOLID_POLISHED');concrete_index=names.index('CONCRETE')
tris=json.loads((W/'colisoes_fivem.json').read_text())
def material_index(t):return names.index(t['collision_material']) if 'collision_material' in t else wood_index if t['wood'] else concrete_index
xyz=np.array([t['points'] for t in tris]).reshape(-1,3);lo=xyz.min(0);hi=xyz.max(0)
# Native static-map type preset also lets the gameplay camera recognize solids.
static_types=CollisionFlags.MAP_TYPE_WEAPON|CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_HORSE|CollisionFlags.MAP_TYPE_COVER|CollisionFlags.MAP_TYPE_VEHICLE
# Spatially independent embedded collisions use their own drawable and bounds.
for m in models:
 name=m['name'];ts=[t for t in tris if t['group']==name]
 if not ts:
  a=try_load_asset(OUT/(name+'.ydr'));a.bounds=None
  for lod in a.models.values():
   for model in lod:
    for g in model.geometries:
     if 'Tangent' not in g.vertex_buffer.dtype.names:continue
     vb=g.vertex_buffer.copy();bad=np.flatnonzero(np.linalg.norm(vb['Tangent'][:,:3],axis=1)<.5)
     if len(bad):
      n=vb['Normal'][bad];axis=np.eye(3)[np.argmin(abs(n),axis=1)];tangent=np.cross(axis,n);tangent/=np.linalg.norm(tangent,axis=1,keepdims=True);vb['Tangent'][bad,:3]=tangent;vb['Tangent'][bad,3]=1.;g.vertex_buffer=vb
  save_asset(a,targets,OUT,name);continue
 b=AssetBoundBvh();b.composite_collision_type_flags=static_types;b.composite_collision_include_flags=CollisionFlags(0xffffffff);b.margin=.002
 vertex_ids={}
 for t in ts:
  ids=[]
  for p in t['points']:
   key=tuple(p)
   if key not in vertex_ids:
    vertex_ids[key]=len(b.geometry_vertices);b.geometry_vertices.append(BoundVertex(Vector(p),None))
   ids.append(vertex_ids[key])
  b.geometry_primitives.append(BoundPrimitive.new_triangle(*ids,CollisionMaterial.from_packed(material_index(t))))
 xyz=np.array([v.co for v in b.geometry_vertices]);mn=xyz.min(0);mx=xyz.max(0)
 b.bb_min=Vector(mn);b.bb_max=Vector(mx);b.centroid=Vector((mn+mx)*.5);b.cg=b.centroid;b.radius_around_centroid=float(np.linalg.norm(mx-mn)*.5)
 comp=AssetBoundComposite(children=[b]);comp.bb_min=b.bb_min;comp.bb_max=b.bb_max;comp.centroid=b.centroid;comp.cg=b.cg;comp.radius_around_centroid=b.radius_around_centroid
 a=try_load_asset(OUT/(name+'.ydr'));a.bounds=comp
 # Collapsed UV corners can have a zero tangent despite valid closed geometry.
 # Supply a finite orthogonal basis rather than a singular normal-map frame.
 if name in ('mansao_mobiliario','mansao_jantar','mansao_ilha'):
  for lod in a.models.values():
   for model in lod:
    for g in model.geometries:
     vb=g.vertex_buffer.copy();bad=np.flatnonzero(np.linalg.norm(vb['Tangent'][:,:3],axis=1)<.5)
     if len(bad):
      n=vb['Normal'][bad];axis=np.eye(3)[np.argmin(abs(n),axis=1)];tangent=np.cross(axis,n);tangent/=np.linalg.norm(tangent,axis=1,keepdims=True)
      vb['Tangent'][bad,:3]=tangent;vb['Tangent'][bad,3]=1.;g.vertex_buffer=vb
 save_asset(a,targets,OUT,name)
 m['lo']=np.minimum(np.array(m['lo']),mn).tolist();m['hi']=np.maximum(np.array(m['hi']),mx).tolist()
ar=[];entities=[]
for m in models:
 name=m['name'];mn=np.array(m['lo']);mx=np.array(m['hi'])
 ar.append(Archetype(name,ArchetypeType.BASE,32,240,0,240,'','','',name,Vector(mn),Vector(mx),Vector((mn+mx)/2),float(np.linalg.norm(mx-mn)/2),name,ArchetypeAssetType.DRAWABLE,[]))
 entities.append(Entity(name,Vector(origin),Quaternion((1,0,0,0)),1,1,EntityFlags.IS_STATIC,0,-1,240,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[]))
for m in dynamic_models:
 name=m['name'];mn=np.array(m['collision_box_lo']);mx=np.array(m['collision_box_hi'])
 vs=np.array([(mn[0],mn[1],mn[2]),(mx[0],mn[1],mn[2]),(mx[0],mx[1],mn[2]),(mn[0],mx[1],mn[2]),(mn[0],mn[1],mx[2]),(mx[0],mn[1],mx[2]),(mx[0],mx[1],mx[2]),(mn[0],mx[1],mx[2])])
 ids=[(0,3,2),(0,2,1),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
 b=AssetBoundBvh();b.composite_collision_type_flags=static_types;b.composite_collision_include_flags=CollisionFlags(0xffffffff);b.margin=.002
 b.geometry_vertices=[BoundVertex(Vector(p),None) for p in vs]
 b.geometry_primitives=[BoundPrimitive.new_triangle(*t,CollisionMaterial.from_packed(wood_index)) for t in ids]
 b.bb_min=Vector(mn);b.bb_max=Vector(mx);b.centroid=Vector((mn+mx)*.5);b.cg=b.centroid;b.radius_around_centroid=float(np.linalg.norm(mx-mn)*.5)
 comp=AssetBoundComposite(children=[b]);comp.bb_min=b.bb_min;comp.bb_max=b.bb_max;comp.centroid=b.centroid;comp.cg=b.cg;comp.radius_around_centroid=b.radius_around_centroid
 a=try_load_asset(OUT/(name+'.ydr'));a.bounds=comp;save_asset(a,targets,OUT,name)
 mn=np.array(m['lo']);mx=np.array(m['hi'])
 ar.append(Archetype(name,ArchetypeType.BASE,32,150,0,150,'','','',name,Vector(mn),Vector(mx),Vector((mn+mx)*.5),float(np.linalg.norm(mx-mn)*.5),name,ArchetypeAssetType.DRAWABLE,[]))
save_asset(AssetMapTypes(name='cidade_mansao',archetypes=ar),targets,OUT,'cidade_mansao')
y=AssetMapData(name='cidade_mansao',content_flags=MapContentFlags.HAS_ENTITIES_HD|MapContentFlags.HAS_PHYSICS,entities=entities,streaming_extents=(Vector(origin-260),Vector(origin+260)),entities_extents=(Vector(origin+lo),Vector(origin+hi)))
save_asset(y,targets,OUT,'cidade_mansao')
# A streamed world bound supplies the ordinary follow camera with static-map
# collision. Its include mask is CAMERA_TEST only: no second walking collider.
camera=AssetBoundBvh();camera.composite_collision_type_flags=static_types;camera.composite_collision_include_flags=CollisionFlags.CAMERA_TEST;camera.margin=.015
vertex_ids={}
for t in tris:
 ids=[]
 for p in t['points']:
  key=tuple(p)
  if key not in vertex_ids:
   vertex_ids[key]=len(camera.geometry_vertices);camera.geometry_vertices.append(BoundVertex(Vector(origin+np.array(p)),None))
  ids.append(vertex_ids[key])
 camera.geometry_primitives.append(BoundPrimitive.new_triangle(*ids,CollisionMaterial.from_packed(material_index(t))))
camera.bb_min=Vector(origin+lo);camera.bb_max=Vector(origin+hi);camera.centroid=Vector(origin+(lo+hi)*.5);camera.cg=camera.centroid;camera.radius_around_centroid=float(np.linalg.norm(hi-lo)*.5)
world=AssetBoundComposite(children=[camera]);world.bb_min=camera.bb_min;world.bb_max=camera.bb_max;world.centroid=camera.centroid;world.cg=camera.cg;world.radius_around_centroid=camera.radius_around_centroid
save_asset(world,targets,OUT,'cidade_mansao')
validation={}
for p in OUT.iterdir():
 if p.suffix not in ('.ydr','.ybn','.ytyp','.ymap'):continue
 assert try_load_asset(p) is not None
 validation[p.name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
assert len(try_load_asset(OUT/'cidade_mansao.ymap').entities)==len(models)
required_dlc={f'{prefix}ch2_09b_{sector}.ybn' for prefix in ('apa_','hei_','hi@apa_','hi@hei_') for sector in (1,3)}
assert required_dlc.issubset(validation),'DLC collision fixes must be included in the installed package.'
for n in ['mansao_pisos','mansao_escada']:
 a=try_load_asset(OUT/(n+'.ydr'));assert 'im_wood_panels_05' in a.shader_group.embedded_textures
assert sum(len(a.bounds.children[0].geometry_primitives) for m in models if (a:=try_load_asset(OUT/(m['name']+'.ydr'))).bounds is not None)==len(tris)
(W/'verificacao_fivem.json').write_text(json.dumps({'files':validation,'collision_triangles':len(tris),'camera_only_world_triangles':len(tris),'camera_include_flags':int(CollisionFlags.CAMERA_TEST),'static_map_type_flags':int(static_types),'wood_collision_material':wood_index,'native_roundtrip':True,'in_game_test':False},indent=2),encoding='utf-8')
print('PACKAGE_OK',len(validation),'files;',len(tris),'collision triangles; wood material',wood_index,flush=True)
