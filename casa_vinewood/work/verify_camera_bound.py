"""Verify the serialized world camera layer, both wall sides and door openings."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import try_load_asset
from szio.gta5.bounds import CollisionFlags,CollisionMaterialFlags
from szio.gta5.maps import MapContentFlags
origin=np.array(json.loads((W/'medidas_estudo.json').read_text())['native_origin']);b=try_load_asset(W/'fivem/cidade_mansao.ybn');child=b.children[0]
assert child.composite_collision_include_flags == CollisionFlags.CAMERA_TEST
assert CollisionFlags.MAP_TYPE_COVER in child.composite_collision_type_flags
assert MapContentFlags.HAS_PHYSICS in try_load_asset(W/'fivem/cidade_mansao.ymap').content_flags
for t in child.geometry_primitives:assert not t.material.material_flags&(CollisionMaterialFlags.NO_CAM_COLLISION|CollisionMaterialFlags.NO_CAM_COLLISION_ALLOW_CLIPPING)
vs=np.array([v.co for v in child.geometry_vertices]);T=vs[np.array([t.vertices for t in child.geometry_primitives])]-origin
rows=json.loads((W/'colisoes_fivem.json').read_text());expected=np.array([t['points'] for t in rows]);assert T.shape==expected.shape
# BVH export reorders triangles and quantizes vertices. Match geometrically,
# including adjacent centroid bins rather than comparing serialization order.
from itertools import product
bins={}
for p in T:bins.setdefault(tuple(np.floor(p.mean(0)/.01).astype(int)),[]).append(p)
error=0.
for p in expected:
 key=np.floor(p.mean(0)/.01).astype(int);best=np.inf
 for shift in product((-1,0,1),repeat=3):
  for q in bins.get(tuple(key+shift),[]):
   ds=np.linalg.norm(p[:,None,:]-q[None,:,:],axis=2)
   best=min(best,max(ds.min(0).max(),ds.min(1).max()))
 error=max(error,float(best))
assert error<.002,error
lo=T.min(1);hi=T.max(1)
def hits(a,b):
 ix=np.flatnonzero(np.all(hi>=np.minimum(a,b)-.0001,1)&np.all(lo<=np.maximum(a,b)+.0001,1))
 ts=T[ix];d=b-a;e1=ts[:,1]-ts[:,0];e2=ts[:,2]-ts[:,0];h=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,h);ok=abs(det)>1e-12;inv=np.divide(1,det,out=np.zeros_like(det),where=ok);s=a-ts[:,0];u=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1);v=inv*(q@d);t=inv*np.einsum('ij,ij->i',e2,q)
 return bool(np.any(ok&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1.000001)&(t>0)&(t<1)))
tested=0;missing=[]
for row,p in zip(rows,expected):
 if row['group']!='mansao_paredes':continue
 n=np.cross(p[1]-p[0],p[2]-p[0]);l=np.linalg.norm(n)
 if l<1e-5 or abs(n[2]/l)>.01:continue
 n/=l;q=p.mean(0)
 for sign in (-1,1):
  tested+=1
  if not hits(q+n*.2*sign,q-n*.2*sign):missing.append(row['source'])
door_tests=[]
for name,x,y,z,axis in [('entrada',6.48,-12.90,.15,0),('sacada oeste',-9.15,-5.17,.15,0),('sacada leste',14.22,-5.17,.15,0),('sala deck',-5.53,-13.15,.15,1),('fundos',-1.123,6.98,.15,0)]:
 q=np.array([x,y,z]);d=np.eye(3)[axis]*.38;blocked=hits(q-d,q+d);door_tests.append(dict(name=name,blocked=blocked));assert not blocked,name
report=dict(passed=not missing,wall_side_ray_tests=tested,missing_wall_sources=sorted(set(missing)),door_tests=door_tests,world_local_alignment_error_m=error,include_flags=int(child.composite_collision_include_flags),body_collision_duplicated=False,in_game_verified=False)
(W/'verificacao_camera.json').write_text(json.dumps(report,indent=2));print('CAMERA_BOUND',report,flush=True);assert not missing
