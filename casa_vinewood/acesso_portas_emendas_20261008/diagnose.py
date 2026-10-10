import sys,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao';S=D/'stream'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
from szio.gta5.bounds import *
origin=np.array(json.loads((D/'portas_madeira.json').read_text())['origin'])
faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
signs=np.array([(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
def physical(b,offset,parent=np.eye(4)):
 tx=np.asarray(b.composite_transform)@parent;tri=[]
 for c in getattr(b,'children',[]):tri.extend(physical(c,offset,tx))
 if hasattr(b,'geometry_primitives'):
  vs=np.array([v.co for v in b.geometry_vertices]);vs=(np.c_[vs,np.ones(len(vs))]@tx)[:,:3]+offset
  for t in b.geometry_primitives:
   v=vs[list(t.vertices)]
   if t.primitive_type==BoundPrimitiveType.TRIANGLE:tri.append(v)
   elif t.primitive_type==BoundPrimitiveType.BOX:
    v1,v2,v3,v4=v;c=v.mean(0);e=((v3+v4)-(v1+v2))*.5;edges=np.array([e,v3-e-v1,v4-e-v1])
    if np.linalg.det(edges)<0:edges=edges[[0,2,1]]
    corners=c+signs@edges*.5;tri.extend(corners[list(f)] for f in faces)
 return tri
def intersections(p,q,ts):
 p=np.array(p);d=np.array(q)-p;v=ts[:,0];e1=ts[:,1]-v;e2=ts[:,2]-v;h=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,h);safe=abs(det)>1e-7;inv=1/np.where(safe,det,1);r=p-v;u=np.einsum('ij,ij->i',r,h)*inv;s=np.cross(r,e1);w=np.einsum('j,ij->i',d,s)*inv;t=np.einsum('ij,ij->i',e2,s)*inv;keep=safe&(u>=-1e-5)&(w>=-1e-5)&(u+w<=1.00001)&(t>=0)&(t<=1)
 return p+t[keep,None]*d
if __name__=='__main__':
 hits=[]
 for f in S.glob('*.ybn'):
  a=try_load_asset(f);ts=np.array(physical(a,-origin))
  if not len(ts):continue
  for x in [3.9,4.745,5.55]:
   edge=16.235+.173*x
   for z in [-2.65,-2.45,-2.2,-1.8]:
    h=intersections([x,edge+.5,z],[x,edge-.55,z],ts)
    if len(h):hits.append([f.name,x,z,h.tolist()])
 (P/'stairs_hits.json').write_text(json.dumps(hits,indent=2));print('STAIR_HITS',hits)
 a=try_load_asset(S/'mansao_paredes.ydr')
 rows=[]
 for m in a.models[LodLevel.HIGH]:
  for g in m.geometries:
   ts=g.vertex_buffer['Position'][g.index_buffer.reshape(-1,3)]
   for t in ts:
    if t[:,2].min()<-.7 and t[:,2].max()>2.25:rows.append([t.min(0).tolist(),t.max(0).tolist()])
 (P/'wall_planes.json').write_text(json.dumps(rows,indent=2));print('WALL_PLANES',rows[:60])
 for f in S.glob('ch2_roads*.ymap'):
  a=try_load_asset(f)
  for e in a.entities:
   if 'palm' in str(e.archetype_name) and np.linalg.norm((np.array(e.position)-origin)[:2]-[14.03,15.9])<1:print('TREE_STILL_PRESENT',f.name,str(e.archetype_name))
