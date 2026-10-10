from pathlib import Path
import sys,numpy as np,json
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset
from szio.gta5.bounds import BoundPrimitiveType
root=Path(__file__).resolve().parents[2]
assets=root/('laboratorio_fivem/elevator_update' if '--update' in sys.argv else 'server-data/resources/cidade_laboratorio/stream')
p=json.loads((root/'laboratorio_fivem/placement.json').read_text())
origin=np.array(p['origin']);basis=np.array(p['basis'])
def test(q,x,z):
 n=np.cross(q[1]-q[0],q[2]-q[0]);
 if abs(n[1])<1e-9:return None
 y=q[0,1]-(n[0]*(x-q[0,0])+n[2]*(z-q[0,2]))/n[1]
 a=q[2]-q[0];b=q[1]-q[0];c=np.array([x,y,z])-q[0]
 aa=a@a;ab=a@b;bb=b@b;ca=c@a;cb=c@b;den=aa*bb-ab*ab
 if abs(den)<1e-9:return None
 u=(bb*ca-ab*cb)/den;v=(aa*cb-ab*ca)/den
 return y if u>=-1e-4 and v>=-1e-4 and u+v<=1+1e-4 else None
for name in ('hi@ch3_08_20.ybn','lab_estrutura.ydr'):
 asset=try_load_asset(assets/name)
 hits=[]
 def scan(bound):
  for child in getattr(bound,'children',[]):scan(child)
  if not hasattr(bound,'geometry_primitives'):return
  transform=np.array(bound.composite_transform)
  for i,prim in enumerate(bound.geometry_primitives):
   if prim.primitive_type!=BoundPrimitiveType.TRIANGLE:continue
   xyz=np.array([list(bound.geometry_vertices[j].co)+[1] for j in prim.vertices])@transform
   q=xyz[:,:3] if name.endswith('.ydr') else (xyz[:,:3]-origin)@basis
   for x in (0,.7,1.0):
    y=test(q,x,1.0)
    if y is not None and 5.7<y<7.45:hits.append((i,x,round(float(y),3)))
 scan(asset.bounds if name.endswith('.ydr') else asset)
 print(name,hits[:50],flush=True)
station=np.array(p['station'])
asset=try_load_asset(assets/'ch3_08_ppbldg003.ydr')
from szio.gta5.drawables import LodLevel
hits=[]
for gi,g in enumerate(asset.models[LodLevel.HIGH][0].geometries):
 verts=(np.asarray(g.vertex_buffer['Position'])+station-origin)@basis
 for ti,tri in enumerate(g.index_buffer.reshape(-1,3)):
  q=verts[tri]
  for x in (0,.7,1.0):
   y=test(q,x,1.0)
   if y is not None and 5.7<y<7.45:hits.append((gi,ti,x,round(float(y),3)))
print('station_render',hits[:50],flush=True)
