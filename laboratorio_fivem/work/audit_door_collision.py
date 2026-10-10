import sys, json, numpy as np
from pathlib import Path
sys.path.insert(0, r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset
from szio.gta5.bounds import BoundPrimitiveType

w=Path(__file__).resolve().parent
p=json.loads((w.parent/'placement.json').read_text())
origin=np.array(p['origin']);basis=np.array(p['basis'])
for src in (w/'base_assets', w.parent/'exports',w.parent.parent/'server-data/resources/cidade_laboratorio/stream'):
 for f in src.glob('*ch3_08*.ybn'):
  a=try_load_asset(f); hits=[]
  def scan(b):
   if b is None:return
   for ch in getattr(b,'children',[]):scan(ch)
   if not hasattr(b,'geometry_primitives'):return
   tx=np.array(b.composite_transform)
   for i,t in enumerate(b.geometry_primitives):
    if t.primitive_type!=BoundPrimitiveType.TRIANGLE:continue
    xyz=np.array([list(b.geometry_vertices[j].co)+[1] for j in t.vertices])@tx
    q=(xyz[:,:3]-origin)@basis
    if np.all(q.max(axis=0)>[-3.7,-8.8,-.3]) and np.all(q.min(axis=0)<[-1.5,-7.2,2.7]):hits.append((i,np.round(q,2).tolist()))
  scan(a)
  if hits:print(src.name,f.name,'hits',len(hits),'sample',hits[:8])
