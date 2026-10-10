import sys,json,numpy as np
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset
from szio.gta5.bounds import BoundPrimitiveType
w=Path(__file__).resolve().parent; p=json.loads((w.parent/'placement.json').read_text());o=np.array(p['origin']);B=np.array(p['basis'])
src=w.parent.parent/'server-data/resources/cidade_laboratorio/stream'
for name in ['hi@ch3_08_20.ybn','ch3_08_20.ybn','lab_estrutura.ydr','lab_porta.ydr']:
 a=try_load_asset(src/name); hits=[]
 def scan(b):
  if b is None:return
  for ch in getattr(b,'children',[]):scan(ch)
  if not hasattr(b,'geometry_primitives'):return
  tx=np.array(b.composite_transform)
  for i,t in enumerate(b.geometry_primitives):
   if t.primitive_type!=BoundPrimitiveType.TRIANGLE:continue
   v=np.array([list(b.geometry_vertices[j].co)+[1] for j in t.vertices])@tx
   q=(v[:,:3]-o)@B if name.startswith('hi@') else v[:,:3]
   # Segment at door center, one metre above floor, pointing through entrance.
   x,z=-2.695,1.0
   if not(q[:,0].min()<=x<=q[:,0].max() and q[:,2].min()<=z<=q[:,2].max()):continue
   normal=np.cross(q[1]-q[0],q[2]-q[0]);det=normal[1]
   if abs(det)<1e-8:continue
   y=q[0,1]-(normal[0]*(x-q[0,0])+normal[2]*(z-q[0,2]))/det
   if not (-8.5<y<6.5):continue
   point=np.array([x,y,z]);v0=q[2]-q[0];v1=q[1]-q[0];v2=point-q[0]
   d00=v0@v0;d01=v0@v1;d11=v1@v1;d20=v2@v0;d21=v2@v1;den=d00*d11-d01*d01
   if abs(den)<1e-8:continue
   u=(d11*d20-d01*d21)/den;vv=(d00*d21-d01*d20)/den
   if u>=-1e-4 and vv>=-1e-4 and u+vv<=1+1e-4:hits.append((i,round(y,3),np.round(q,2).tolist()))
 scan(a.bounds if hasattr(a,'bounds') else a)
 print(name,'PATH_BLOCKERS',hits[:20],flush=True)



