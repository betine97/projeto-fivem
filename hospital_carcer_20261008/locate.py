import sys,json,re
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parent;N=P/'native';N.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.rpf import open_rpf
from szio.gta5 import *
import numpy as np
game=Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V');index=(R/'laboratorio_fivem/work/assets_index.txt').read_text().splitlines();cache={}
def archive(parts):
 key='|'.join(parts[:-1])
 if key not in cache:
  a=open_rpf(game/parts[0])
  for sub in parts[1:-1]:a=a.open_nested(sub)
  cache[key]=a
 return cache[key]
def extract(s):
 p=s.split('|');f=N/Path(p[-1]).name
 if not f.exists():f.write_bytes(archive(p).read_bytes(p[-1]))
 return f
if __name__=='__main__':
 rows=[];maps=[]
 for s in index:
  if 'beverly_metadata.rpf|' not in s or not s.endswith('.ymap'):continue
  p=s.split('|');name=Path(p[-1]).name
  if not re.match(r'bh1_\d',name) or 'interior' in name:continue
  f=extract(s);a=try_load_asset(f);hit=False
  for i,e in enumerate(a.entities):
   v=np.array(e.position)
   if -570<v[0]<-340 and -450<v[1]<-200:
    rows.append(dict(map=name,index=i,name=str(e.archetype_name),pos=list(v),rot=list(e.rotation),parent=e.parent_index,lod=str(e.lod_level)));hit=True
  if hit:maps.append(s)
 (P/'entities.json').write_text(json.dumps(rows,indent=2));(P/'map_sources.json').write_text(json.dumps(maps,indent=2))
 candidates=[q for q in rows if 'build' in q['name'] or 'hosp' in q['name'] or (q['name'].endswith(('_strm','_bldg','_build')))]
 print('MAPS',sorted({q['map'] for q in rows}));print('BUILDINGS',candidates);print('LOCAL_ENTITIES',len(rows))
 names={q['name'] for q in rows}
 for s in index:
  if s.endswith('.ydr') and Path(s.split('|')[-1]).stem in names:extract(s)
 print('EXTRACTED_GEOMETRY',len(names),flush=True)
