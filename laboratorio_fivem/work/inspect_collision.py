import sys,json,numpy as np
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset
p0=np.array([1552.61585,842.28992,78.8]);r=[]
for p in Path('laboratorio_fivem/work/base_assets').glob('*ch3_08*.ybn'):
 a=try_load_asset(p)
 if np.all(p0>=np.array(a.bb_min)-2) and np.all(p0<=np.array(a.bb_max)+2):
  print(p.name,'bb',list(a.bb_min),list(a.bb_max))
  for i,b in enumerate(a.children):
   if b is None:continue
   if hasattr(b,'geometry_vertices'):
    vs=np.array([list(v.co)+[1] for v in b.geometry_vertices])@np.array(b.composite_transform)
    if np.all(p0>=vs[:,:3].min(0)-2) and np.all(p0<=vs[:,:3].max(0)+2):print('CHILD',i,b.bound_type,len(b.geometry_primitives),'range',vs[:,:3].min(0),vs[:,:3].max(0),'transform',b.composite_transform)
