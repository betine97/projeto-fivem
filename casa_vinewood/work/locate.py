import sys,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'laboratorio_fivem/work/pydeps'),r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps']
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset
game=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V')
out=Path(__file__).parent;assets=out/'native';assets.mkdir(exist_ok=True)
index=(ROOT/'laboratorio_fivem/work/assets_index.txt').read_text().splitlines()
cache={};entities=[]
def archive(parts):
 key='|'.join(parts[:-1])
 if key not in cache:
  r=open_rpf(game/parts[0])
  for sub in parts[1:-1]:r=r.open_nested(sub)
  cache[key]=r
 return cache[key]
for s in index:
 if '_hills/' not in s or not s.endswith('.ymap'):continue
 parts=s.split('|')
 try:
  f=assets/Path(parts[-1]).name
  if not f.exists():f.write_bytes(archive(parts).read_bytes(parts[-1]))
  a=try_load_asset(f)
  for e in a.entities:
   x,y,z=map(float,e.position)
   if -1100<x<200 and 350<y<1200:
    entities.append(dict(map=f.name,name=str(e.archetype_name),pos=[x,y,z],rot=list(e.rotation)))
 except Exception as ex:print('ERROR',s,str(ex),flush=True)
(out/'entities.json').write_text(json.dumps(entities,indent=2))
names={e['name'] for e in entities if re.search(r'house|hous|bldg|build|_h\d\d',e['name']) and not re.search(r'lod|emiss|decal|rail|light',e['name'])}
for s in index:
 parts=s.split('|');stem=Path(parts[-1]).stem
 if s.endswith('.ydr') and stem in names:
  f=assets/(stem+'.ydr')
  if not f.exists():f.write_bytes(archive(parts).read_bytes(parts[-1]))
(out/'candidates.json').write_text(json.dumps([e for e in entities if e['name'] in names],indent=2))
print('Candidates',len(names), sorted(names),flush=True)
