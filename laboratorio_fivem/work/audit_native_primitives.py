import sys,json,numpy as np
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset
from szio.gta5.bounds import BoundPrimitiveType
w=Path(__file__).resolve().parent;p=json.loads((w.parent/'placement.json').read_text());o=np.array(p['origin']);B=np.array(p['basis'])
for f in [w/'base_assets/hi@ch3_08_20.ybn',w.parent.parent/'server-data/resources/cidade_laboratorio/stream/hi@ch3_08_20.ybn',w/'base_assets/ch3_08_20.ybn']:
 a=try_load_asset(f);found=[]
 def walk(b):
  if b is None:return
  for c in getattr(b,'children',[]):walk(c)
  if not hasattr(b,'geometry_primitives'):return
  tx=np.array(b.composite_transform)
  for i,t in enumerate(b.geometry_primitives):
   if t.primitive_type==BoundPrimitiveType.TRIANGLE:continue
   v=np.array([list(b.geometry_vertices[j].co)+[1] for j in t.vertices])@tx
   q=(v[:,:3]-o)@B
   r=t.radius or 0
   lo=q.min(0)-r;hi=q.max(0)+r
   if np.all(hi>[-4.2,-8.6,0]) and np.all(lo<[4.2,6.2,2.7]):
    found.append((i,str(t.primitive_type),np.round(lo,2).tolist(),np.round(hi,2).tolist()))
 walk(a)
 print(f.name,'found',len(found),found[:60],flush=True)
