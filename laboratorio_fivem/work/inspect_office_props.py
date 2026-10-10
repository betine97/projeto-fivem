import sys
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset
import numpy as np
base=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V')
out=Path(__file__).resolve().parent/'office_props';out.mkdir(exist_ok=True)
index=(out.parent/'assets_index.txt').read_text().splitlines()
names={'prop_off_chair_04','prop_off_chair_04b','prop_off_phone_01','prop_monitor_01c','prop_monitor_01d','prop_keyboard_01a','prop_mouse_01a','prop_pc_01a'}
cache={}
for s in index:
 parts=s.split('|');name=Path(parts[-1]).stem
 if name not in names or not s.endswith('.ydr'):continue
 key='|'.join(parts[:2])
 if key not in cache:cache[key]=open_rpf(base/parts[0]).open_nested(parts[1])
 path=out/parts[-1];path.write_bytes(cache[key].read_bytes(parts[-1]))
 a=try_load_asset(path)
 pts=[]
 for lod in a.models.values():
  for model in lod:
   for g in model.geometries:
    key=next(k for k in g.vertex_buffer.dtype.names if k.lower()=='position')
    pts.extend(g.vertex_buffer[key])
 xyz=np.asarray(pts);lo=xyz.min(0);hi=xyz.max(0)
 print(name,'min',np.round(lo,3).tolist(),'max',np.round(hi,3).tolist(),'bounds',type(a.bounds).__name__ if a.bounds else None,flush=True)
