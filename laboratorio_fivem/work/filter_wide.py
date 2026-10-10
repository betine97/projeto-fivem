import sys,json
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset
es=[]
for p in Path('laboratorio_fivem/work/base_assets').glob('*.ymap'):
 a=try_load_asset(p)
 for e in a.entities:
  x,y,z=e.position
  if 800<x<2300 and 200<y<1800:es.append(dict(map=p.name,name=e.archetype_name,pos=list(e.position),rot=list(e.rotation)))
Path('laboratorio_fivem/work/area_wide.json').write_text(json.dumps(es,indent=2))
for e in es:
 if any(t in e['name'] for t in ['dam','pipe','build','water','elec','struc','pwr','industrial']):print(e['name'],[round(float(v),2) for v in e['pos']])
