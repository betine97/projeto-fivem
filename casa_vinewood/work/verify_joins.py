"""Check facade corner continuity against the serialized drawable, not the .blend."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from shapely.geometry import Polygon,Point
from szio.gta5 import try_load_asset
rows=[]
for name in ['mansao_paredes','mansao_pisos','mansao_teto']:
 a=try_load_asset(W/'fivem'/(name+'.ydr'))
 for models in a.models.values():
  for m in models:
   for g in m.geometries:rows.extend(g.vertex_buffer['Position'][g.index_buffer.reshape(-1,3)].astype(float))
T=np.array(rows);low=T.min(1);high=T.max(1)
def hits(a,b):
 ix=np.flatnonzero(np.all(high>=np.minimum(a,b)-.001,1)&np.all(low<=np.maximum(a,b)+.001,1))
 ts=T[ix];d=b-a;v1=ts[:,1]-ts[:,0];v2=ts[:,2]-ts[:,0];h=np.cross(d,v2);det=np.einsum('ij,ij->i',v1,h)
 inv=np.divide(1,det,out=np.zeros_like(det),where=np.abs(det)>1e-9);s=a-ts[:,0]
 u=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,v1);v=inv*(q@d);t=inv*np.einsum('ij,ij->i',v2,q)
 return bool(np.any((np.abs(det)>1e-9)&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1+1e-6)&(t>0)&(t<1)))
spec=json.loads((W/'encaixe_fachada.json').read_text());checks=[]
for key,levels in [('ground_polygon',[-.78,.2,1.4,2.52]),('upper_polygon',[2.83,3.7,5.6,6.48])]:
 poly=Polygon(spec[key]);vertices=spec[key]
 for i,p in enumerate(vertices):
  p=np.array(p);prev=np.array(vertices[i-1]);nxt=np.array(vertices[(i+1)%len(vertices)])
  e1=(prev-p)/np.linalg.norm(prev-p);e2=(nxt-p)/np.linalg.norm(nxt-p);bis=(e1+e2);bis/=np.linalg.norm(bis)
  if not poly.contains(Point(p+bis*.10)):bis=-bis
  for z in levels:
   a=np.r_[p+bis*.25,z];b=np.r_[p-bis*.25,z]
   checks.append({'floor':key,'corner':i,'z':z,'closed':hits(a,b)})
joins=json.loads((W/'revisao_juntas.json').read_text())
result={'serialized_geometry_checked':True,'corner_rays':checks,'corner_rays_tested':len(checks),'open_corner_rays':sum(not q['closed'] for q in checks),'facade_panels':len(joins['panels']),'passed':all(q['closed'] for q in checks),'in_game_verified':False}
(W/'verificacao_juntas.json').write_text(json.dumps(result,indent=2))
print('FACADE_CORNERS',len(checks),'rays;',result['open_corner_rays'],'open;',result['passed'],flush=True)
if not result['passed']:print('OPEN', [q for q in checks if not q['closed']])
assert result['passed']
