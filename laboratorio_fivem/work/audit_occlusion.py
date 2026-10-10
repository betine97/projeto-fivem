import sys,json,numpy as np
from pathlib import Path
sys.path.insert(0,r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps')
from szio.gta5 import try_load_asset
w=Path(__file__).resolve().parent
origin=np.array(json.loads((w.parent/'placement.json').read_text())['origin'])
for p in (w/'base_assets').glob('*occl*.ymap'):
 a=try_load_asset(p)
 for i,b in enumerate(a.box_occluders):
  c=np.array(b.center);s=np.array(b.size)
  if np.linalg.norm(c[:2]-origin[:2])<40: print(p.name,'BOX',i,'center',c,'size',s,'rotation',b.cos_sin_z,flush=True)
 for i,b in enumerate(a.model_occluders):
  lo=b.vertices.min(axis=0);hi=b.vertices.max(axis=0)
  if np.all(hi>origin-15) and np.all(lo<origin+15):print(p.name,'MODEL',i,'bounds',lo,hi,'triangles',b.indices.shape,flush=True)
