import sys,json
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset
base=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V')
out=Path('laboratorio_fivem/work/base_assets');out.mkdir(exist_ok=True)
index=Path('laboratorio_fivem/work/assets_index.txt').read_text().splitlines();cache={}; entities=[]
for s in index:
 if not ('ch3_11' in s):continue
 parts=s.split('|');key='|'.join(parts[:-1])
 if key not in cache:cache[key]=open_rpf(base/parts[0]).open_nested(parts[1])
 p=out/parts[-1];p.write_bytes(cache[key].read_bytes(parts[-1]))
 if p.suffix=='.ymap':
  a=try_load_asset(p)
  for e in a.entities:entities.append(dict(map=p.name,name=e.archetype_name,pos=list(e.position),rot=list(e.rotation)))
Path('laboratorio_fivem/work/ch3_11_entities.json').write_text(json.dumps(entities,indent=2))
print('STRUCTURES',[(e['name'],[round(float(v),2) for v in e['pos']]) for e in entities if 'structures' in e['name']]);print(len(entities))

