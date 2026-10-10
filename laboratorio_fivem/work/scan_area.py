import sys,json
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset
base=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V');out=Path('laboratorio_fivem/work/base_assets');cache={};entities=[]
for s in Path('laboratorio_fivem/work/assets_index.txt').read_text().splitlines():
 if not ('cityhills_' in s and s.endswith('.ymap')):continue
 parts=s.split('|');key='|'.join(parts[:-1])
 if key not in cache:cache[key]=open_rpf(base/parts[0]).open_nested(parts[1])
 p=out/parts[-1];p.write_bytes(cache[key].read_bytes(parts[-1]))
 a=try_load_asset(p)
 for e in a.entities:
  x,y,z=e.position
  if 650<x<1400 and 200<y<1400:
   entities.append(dict(map=p.name,name=e.archetype_name,pos=list(e.position),rot=list(e.rotation)))
Path('laboratorio_fivem/work/area_entities.json').write_text(json.dumps(entities,indent=2))
print('TOTAL',len(entities))
print('\n'.join(str(e) for e in entities if not e['name'].startswith(('prop','v_','proc'))))
