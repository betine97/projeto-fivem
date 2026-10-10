"""Offline checks of serialized collisions. Does not replace a GTA ped test."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];W=ROOT/'casa_vinewood'
sys.path[:0]=[str(ROOT/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import try_load_asset
from szio.gta5.bounds import BoundPrimitiveType
R=json.loads((W/'medidas_estudo.json').read_text());origin=np.array(R['native_origin']);O=np.array(R['interior_origin_relative_native'])
SIGNS=np.array([(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
FACES=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
native=[];labels=[]
def visit(b,parent=np.eye(4),file=''):
 tx=np.array(b.composite_transform)@parent
 for c in getattr(b,'children',[]):visit(c,tx,file)
 if not hasattr(b,'geometry_primitives'):return
 vs=np.array([v.co for v in b.geometry_vertices]);vs=(np.c_[vs,np.ones(len(vs))]@tx)[:,:3]-origin
 for i,t in enumerate(b.geometry_primitives):
  pts=vs[list(t.vertices)]
  if np.any(pts.max(0)<[-9.5,-14.5,-1.5]) or np.any(pts.min(0)>[14.5,10,7]):continue
  if t.primitive_type==BoundPrimitiveType.TRIANGLE:polys=[pts]
  elif t.primitive_type==BoundPrimitiveType.BOX:
   v1,v2,v3,v4=pts;e=((v3+v4)-(v1+v2))*.5;edges=np.array([e,v3-e-v1,v4-e-v1]);verts=pts.mean(0)+SIGNS@edges*.5
   polys=[verts[list(ids)] for ids in FACES]
  else:continue
  for tri in polys:native.append(tri);labels.append(f'{file}:{i}')
for p in sorted((W/'work/native').glob('*ch2_09b_[0-3].ybn')):
 f=W/'fivem'/p.name;visit(try_load_asset(f if f.exists() else p),file=p.name)
custom=json.loads((W/'colisoes_fivem.json').read_text());native.extend(np.array(t['points']) for t in custom);labels.extend(t['source'] for t in custom)
T=np.array(native);low=T.min(1);high=T.max(1)
def distances(p,ts):
 a,b,c=ts[:,0],ts[:,1],ts[:,2];n=np.cross(b-a,c-a);nn=np.einsum('ij,ij->i',n,n)
 ds=np.einsum('ij,ij->i',p-a,n);proj=p-ds[:,None]*n/np.maximum(nn[:,None],1e-20)
 cross=[np.einsum('ij,ij->i',np.cross(v-u,proj-u),n) for u,v in [(a,b),(b,c),(c,a)]]
 inside=(cross[0]>=-1e-9)&(cross[1]>=-1e-9)&(cross[2]>=-1e-9)&(nn>1e-15)
 best=np.where(inside,np.abs(ds)/np.sqrt(np.maximum(nn,1e-20)),np.inf)
 for u,v in [(a,b),(b,c),(c,a)]:
  e=v-u;t=np.clip(np.einsum('ij,ij->i',p-u,e)/np.maximum(np.einsum('ij,ij->i',e,e),1e-20),0,1)
  best=np.minimum(best,np.linalg.norm(p-(u+t[:,None]*e),axis=1))
 return best
routes={}
def route(name,waypoints):
 samples=[]
 for a,b in zip(waypoints,waypoints[1:]):
  a=np.array(a);b=np.array(b);n=max(1,int(np.linalg.norm(b-a)/.09));samples.extend(a+(b-a)*t/n for t in range(n+1))
 blockers=[];minimum=100.0
 for foot in samples:
  for height in [.4,.9,1.5]:
   p=foot+[0,0,height];mask=np.all(high>=p-.32,1)&np.all(low<=p+.32,1);ix=np.flatnonzero(mask)
   if not len(ix):continue
   ds=distances(p,T[ix]);minimum=min(minimum,float(ds.min()))
   for j in ix[ds<.30]:blockers.append({'foot':np.round(foot,3).tolist(),'object':labels[j]})
 routes[name]={'samples':len(samples),'minimum_sample_clearance_m':minimum,'blockers':blockers[:12],'passed':not blockers}
route('porta_exterior_ate_cozinha',[(5.8,-13.32,-.60),(5.85,-13.32,-.60),(7.12,-13.32,-.80),(7.85,-13.32,-.8),(7.85,-11.85,-.8)])
route('escada_terreo_ao_superior',[np.array(v)+O for v in [(9.2,15.5,0),(9.2,18.5,1.804),(9.2,18.9,1.804),(10.6,18.9,1.804),(10.6,18.5,1.9844),(10.6,15.8,3.608),(10.6,15.35,3.608)]])
# Check body clearance and a supporting horizontal floor in every room.
room_checks={}
for room in R['rooms']:
 if room['name']=='Escada':continue  # The entire ascent is checked above.
 x0,x1,y0,y1=room['bounds'];x,y=(x0+x1)*.5,(y0+y1)*.5
 if room['name']=='Sala intima / leitura':x,y=12.5,17.8
 z=0 if room['level']=='terreo' else R['levels_m'][1]
 foot=np.array([x,y,z])+O;key=room['level']+'_'+room['name'];route(key,[foot,foot])
 n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);mask=(n[:,2]>1e-6)&(low[:,0]<=foot[0])&(high[:,0]>=foot[0])&(low[:,1]<=foot[1])&(high[:,1]>=foot[1]);ix=np.flatnonzero(mask)
 candidates=T[ix];normals=n[ix];zs=candidates[:,0,2]-(normals[:,0]*(foot[0]-candidates[:,0,0])+normals[:,1]*(foot[1]-candidates[:,0,1]))/normals[:,2]
 points=np.c_[np.full(len(ix),foot[0]),np.full(len(ix),foot[1]),zs]
 support=False
 for p,tri in zip(points,candidates):
  if abs(p[2]-foot[2])<.015 and distances(p,np.array([tri]))[0]<.01:support=True;break
 room_checks[key]={'body_clear':routes[key]['passed'],'floor_support':support}
 assert support,key+' has no supporting floor'
# The serialized custom bound includes every authored triangle and both ramps.
a=try_load_asset(W/'fivem/mansao_paredes.ydr');assert len(a.bounds.children[0].geometry_primitives)==len(custom)
result={'offline_only':True,'in_game_test':False,'collision_triangles_checked':len(T),'body_radius_m':.30,'rooms':room_checks,'routes':routes}
(W/'verificacao_fisica.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2),flush=True)
assert all(r['passed'] for r in routes.values()),'A walking route intersects a collision; repair before installing.'
