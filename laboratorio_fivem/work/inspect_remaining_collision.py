import sys
from pathlib import Path
sys.path.insert(0, r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset
w=Path(__file__).resolve().parents[2]
for name in ('ch3_08_ppbldg003.ydr','lab_estrutura.ydr','lab_porta.ydr','lab_equipamentos.ydr','lab_ventilacao.ydr'):
 a=try_load_asset(w/'server-data/resources/cidade_laboratorio/stream'/name)
 b=a.bounds
 print(name,'bounds',type(b).__name__ if b else None,'children',len(getattr(b,'children',[])) if b else None,flush=True)
 if b:
  for c in getattr(b,'children',[]):print('  child',type(c).__name__,'primitives',len(getattr(c,'geometry_primitives',[])),flush=True)
