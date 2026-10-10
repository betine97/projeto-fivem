import sys,json,numpy as np
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset
from szio.gta5.bounds import BoundPrimitiveType
w=Path(__file__).resolve().parent;p=json.loads((w.parent/'placement.json').read_text());o=np.array(p['origin']);B=np.array(p['basis'])
def boxes(path):
 a=try_load_asset(path);result=[]
 def scan(b):
  for c in getattr(b,'children',[]):scan(c)
  if not hasattr(b,'geometry_primitives'):return
  tx=np.array(b.composite_transform)
  for i,t in enumerate(b.geometry_primitives):
   if t.primitive_type!=BoundPrimitiveType.BOX:continue
   xyz=np.array([list(b.geometry_vertices[j].co)+[1] for j in t.vertices])@tx
   q=(xyz[:,:3]-o)@B;result.append((i,q.min(0),q.max(0)))
 scan(a);return result
src=boxes(w/'base_assets/ch3_08_36.ybn')
patched=boxes(w.parent.parent/'server-data/resources/cidade_laboratorio/stream/ch3_08_36.ybn')
previous=boxes(w.parent/'backup_before_office_fix/ch3_08_36.ybn')
print('COUNTS',len(src),len(patched),flush=True)
for a in patched:
 if np.all(a[2]>[-5,-9,-2]) and np.all(a[1]<[5,8,8]):
  print('NATIVE_BOX',a[0],'lo',np.round(a[1],3).tolist(),'hi',np.round(a[2],3).tolist(),flush=True)
for x,y in [(-2.695,-8.04),(0,5.3),(-3.4,3.8)]:
 hits=[i for i,lo,hi in patched if lo[0]<x<hi[0] and lo[1]<y<hi[1] and lo[2]<1<hi[2]]
 prior=[i for i,lo,hi in previous if lo[0]<x<hi[0] and lo[1]<y<hi[1] and lo[2]<1<hi[2]]
 print('CLEAR_AT',x,y,'before',prior,'after',hits,flush=True)
 assert not hits
assert len(patched)==len(src)-2
