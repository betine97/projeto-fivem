import sys
from pathlib import Path
sys.path.insert(0,str(Path('personagens/catalogo_nativo').resolve()))
import render_catalog as r
m=next(m for m in r.DATA['models'] if m['collection']=='mp_m_freemode_01_male_heist' and m['part']=='task')
a=r.try_load_asset(r.vpath(m['path']))
print('slot',[(k,[(int(l),sum(len(g.index_buffer) for m in ms for g in m.geometries)) for l,ms in d.models.items()]) for k,d in a.drawables.items()])
a=r.try_load_asset(r.ROOT/'personagens/cracha_dea/source/task_001_u.ydd');print('sourcekeys',list(a.drawables));print('names',[d.name for d in a.drawables.values()])
