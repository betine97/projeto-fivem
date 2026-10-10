import sys, numpy as np, json, collections
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset
w=Path(__file__).resolve().parent
for f in [w/'base_assets/ch3_08_20.ybn',w/'base_assets/hi@ch3_08_20.ybn',w.parent.parent/'server-data/resources/cidade_laboratorio/stream/hi@ch3_08_20.ybn']:
 a=try_load_asset(f);counter=collections.Counter()
 def walk(b):
  if b is None:return
  counter[type(b).__name__]+=1
  for q in getattr(b,'geometry_primitives',[]):counter[str(q.primitive_type)]+=1
  for c in getattr(b,'children',[]):walk(c)
 walk(a)
 print(f,dict(counter),flush=True)
