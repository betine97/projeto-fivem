import sys,collections
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset
from szio.gta5.bounds import BoundPrimitiveType
a=try_load_asset(Path(__file__).resolve().parent/'base_assets/ch3_08_36.ybn')
def scan(b):
 for c in getattr(b,'children',[]):scan(c)
 if not hasattr(b,'geometry_primitives'):return
 counts=collections.Counter(v for t in b.geometry_primitives for v in t.vertices)
 for i in (337,550):
  t=b.geometry_primitives[i]
  if t.primitive_type==BoundPrimitiveType.BOX:print('PRIMITIVE',i,'indices',t.vertices,'share_counts',[counts[v] for v in t.vertices],flush=True)
scan(a)
