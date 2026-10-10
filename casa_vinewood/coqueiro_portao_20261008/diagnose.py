import sys,json,collections
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao';S=D/'stream'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
origin=np.array(json.loads((D/'garagem_acesso.json').read_text())['origin'])
def run():
 rows=[]
 for directory in [S,R/'casa_vinewood/work/native']:
  for f in directory.glob('*.ymap'):
   a=try_load_asset(f)
   for i,e in enumerate(a.entities):
    pos=np.array(e.position)-origin
    if 'palm' in str(e.archetype_name) or 'combo0126' in str(e.archetype_name):
     if np.linalg.norm(pos[:2])<38:rows.append(dict(file=str(f.relative_to(R)),index=i,model=str(e.archetype_name),localPos=pos.tolist(),parent=e.parent_index))
 (P/'palms.json').write_text(json.dumps(rows,indent=2));print('PALMS',rows)
 f=S/'mansao_portao_subsolo.ydr';a=try_load_asset(f)
 for lod,models in a.models.items():
  tris=np.concatenate([g.vertex_buffer['Position'][g.index_buffer.reshape(-1,3)] for m in models for g in m.geometries])
  print('GATE',str(lod),len(tris),'bounds',tris.reshape(-1,3).min(0),tris.reshape(-1,3).max(0))
  # Identical surface triangles, including reversed winding, flicker with Z fighting.
  keys=[tuple(sorted(tuple(np.round(p,5)) for p in t)) for t in tris]
  print('DUPLICATE_TRIANGLES',sum(n-1 for n in collections.Counter(keys).values()))
 for f in S.glob('*.ymap'):
  a=try_load_asset(f)
  for e in a.entities:
   if str(e.archetype_name)=='mansao_portao_subsolo':print('DUPLICATE_MAP_GATE',f.name)

if __name__=="__main__":run()
