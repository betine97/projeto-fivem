import sys
from pathlib import Path
sys.path.insert(0,str(Path('personagens/catalogo_nativo').resolve()))
import render_catalog as r
from dataclasses import fields
f=r.try_load_asset(r.ROOT/'personagens/templates_freemode/source/mp_m_freemode_01.yft');print('fragmentfields',[x.name for x in fields(f)])
d=f.drawable;print('bones',[(i,b.name,b.tag,tuple(b.position),tuple(b.rotation),b.parent_index) for i,b in enumerate(d.skeleton.bones) if 'Thigh' in b.name or 'Pelvis' in b.name])
t=r.try_load_asset(r.ROOT/'server-data/resources/cidade_laboratorio/stream/cidade_laboratorio.ytyp');ar=t.archetypes[0];print('archetype',ar)
