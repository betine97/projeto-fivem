from pathlib import Path
import sys,json,copy,re,struct
P=Path(__file__).resolve().parents[1];R=P.parent;O=P/'fivem/stream'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
from szio.gta5.bounds import *
from szio.gta5.maps import *
from szio.gta5.entities import *
from szio.types import Vector,Quaternion,DataSource
grid=np.load(P/'dados/terreno.npz')['terrain'];rows=json.loads((P/'nativo/modelos.json').read_text());targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),);archetypes=[];report=[]
names=re.findall(r'CollisionMaterialDef\("([A-Z_0-9]+)"',Path(r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz/Sollumz/ybn/collision_materials.py').read_text())
def setbounds(b,lo,hi):b.bb_min=Vector(lo);b.bb_max=Vector(hi);b.centroid=Vector((lo+hi)/2);b.cg=b.centroid;b.radius_around_centroid=float(np.linalg.norm(hi-lo)/2)
def collision(v,ts):
 b=AssetBoundBvh();b.margin=.002;b.composite_collision_type_flags=CollisionFlags.MAP_TYPE_WEAPON|CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_HORSE|CollisionFlags.MAP_TYPE_COVER|CollisionFlags.MAP_TYPE_VEHICLE;b.composite_collision_include_flags=CollisionFlags(0xffffffff)
 b.geometry_vertices=[BoundVertex(Vector(p),None) for p in v];lo=v.min(0);hi=v.max(0);materials={}
 for i,name in enumerate(['GRASS','SAND_LOOSE','ROCK']):materials[name]=CollisionMaterial.from_packed(names.index(name))
 b.geometry_primitives=[]
 for t in ts:
  p=v[t];normal=np.cross(p[1]-p[0],p[2]-p[0]);slope=np.linalg.norm(normal[:2])/max(abs(normal[2]),1e-6);material='SAND_LOOSE' if p[:,2].mean()<10 else 'ROCK' if slope>.7 else 'GRASS'
  b.geometry_primitives.append(BoundPrimitive.new_triangle(*(int(i) for i in t),materials[material]))
 setbounds(b,lo,hi);c=AssetBoundComposite(children=[b]);setbounds(c,lo,hi);return c
for row in rows:
 name=row['name'];center=np.array(row['center']);a=try_load_asset(P/'nativo/ydr'/f'{name}.ydr');tri={}
 for lod,suffix in [(LodLevel.HIGH,''),(LodLevel.MEDIUM,'_MED'),(LodLevel.LOW,'_LOW'),(LodLevel.VERYLOW,'_VLOW')]:
  path=P/'nativo/ydr'/f'{name}{suffix}.ydr';src=try_load_asset(path) if path.exists() else a
  a.models[lod]=copy.deepcopy(src.models[LodLevel.HIGH]);tri[lod.name]=sum(len(g.index_buffer)//3 for m in a.models[lod] for g in m.geometries)
  for m in a.models[lod]:
   for g in m.geometries:
    if 'Tangent' in g.vertex_buffer.dtype.names:
     v=g.vertex_buffer.copy();bad=np.linalg.norm(v['Tangent'][:,:3],axis=1)<.5;n=v['Normal'][bad];axis=np.eye(3)[np.argmin(abs(n),axis=1)];t=np.cross(axis,n);t/=np.maximum(np.linalg.norm(t,axis=1,keepdims=True),1e-9);v['Tangent'][bad,:3]=t;v['Tangent'][bad,3]=1;g.vertex_buffer=v
 for txname in list(a.shader_group.embedded_textures):
  b=(P/'nativo/texturas'/f'{txname}.dds').read_bytes();h,w=struct.unpack_from('<II',b,12);a.shader_group.embedded_textures[txname]=EmbeddedTexture(txname,w,h,DataSource.create(b,name=txname+'.dds'))
 for s in a.shader_group.shaders:s.name=Path(s.preset_filename).stem
 a.lod_thresholds={LodLevel.HIGH:420.,LodLevel.MEDIUM:850.,LodLevel.LOW:1800.,LodLevel.VERYLOW:6500.};a.bounds=None
 save_asset(a,targets,O,name);positions=np.concatenate([g.vertex_buffer['Position'] for m in a.models[LodLevel.HIGH] for g in m.geometries]);lo=positions.min(0);hi=positions.max(0);physics=[];coltri=0
 if 'grid_bounds' in row:
  x0,y0,x1,y1=row['grid_bounds'];patch=grid[y0:y1+1,x0:x1+1];n=len(patch);j,i=np.meshgrid(np.arange(n-1),np.arange(n-1),indexing='ij');v=patch.reshape(-1,3);q=(j*n+i).ravel();ts=np.concatenate([np.stack([q,q+1,q+n+1],1),np.stack([q,q+n+1,q+n],1)]);save_asset(collision(v,ts),targets,O,name);physics=[name];coltri=len(ts)
 archetypes.append(Archetype(name,ArchetypeType.BASE,32,6500,0,6500,'','','',name,Vector(lo),Vector(hi),Vector((lo+hi)/2),float(np.linalg.norm(hi-lo)/2),'',ArchetypeAssetType.DRAWABLE,[]))
 entity=Entity(name,Vector(center),Quaternion((1,0,0,0)),1,1,EntityFlags.IS_STATIC,0,-1,6500,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[])
 save_asset(AssetMapData(name=name+'_map',content_flags=MapContentFlags.HAS_ENTITIES_HD|MapContentFlags.HAS_PHYSICS,entities=[entity],physics_dictionaries=physics,streaming_extents=(Vector(center+lo-6500),Vector(center+hi+6500)),entities_extents=(Vector(center+lo-.01),Vector(center+hi+.01))),targets,O,name+'_map')
 report.append({'name':name,'center':row['center'],'lod_triangles':tri,'collision_triangles':coltri,'bounds':[lo.tolist(),hi.tolist()]});print('NATIVE_PACKAGED',name,flush=True)
save_asset(AssetMapTypes(name='teste_ilha',archetypes=archetypes),targets,O,'teste_ilha')
(P/'nativo/pacote.json').write_text(json.dumps(report,indent=2));print('NATIVE_ISLAND_PACKAGE_READY',len(report),flush=True)
