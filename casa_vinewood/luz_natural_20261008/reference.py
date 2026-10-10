import sys,json,io,re
from pathlib import Path
from collections import Counter
P=Path(__file__).resolve().parent;R=P.parents[1]
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.rpf import open_rpf
import pymateria.gta5.gen8 as g8
game=Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V')
index=(R/'laboratorio_fivem/work/assets_index.txt').read_text().splitlines();cache={};rows=[];models=[]
for line in index:
 if not line.endswith('.ydr'):continue
 parts=line.split('|');name=Path(parts[-1]).stem
 group=('michael' if 'v_int_44.rpf' in line else ('suburban' if 'v_int_51.rpf' in line else ('clothes_mid' if 'v_int_52.rpf' in line else None)))
 if group is None or not re.search('shell|emis|emmi|chand|deta|lights|pendant|items',name):continue
 key='|'.join(parts[:-1])
 if key not in cache:
  a=open_rpf(game/parts[0])
  for sub in parts[1:-1]:a=a.open_nested(sub)
  cache[key]=a
 data=cache[key].read_bytes(parts[-1]);asset=g8.Drawable.import_rsc(io.BytesIO(data)).result
 models.append(dict(group=group,name=name,light_count=len(asset.lights)))
 for i,li in enumerate(asset.lights):
  rows.append(dict(group=group,model=name,index=i,type=li.type.name,position=list(li.position),direction=list(li.direction),extent=list(li.extents),rgb=list(li.color),intensity=li.intensity,range=li.falloff,falloff_exponent=li.falloff_exponent,inner=li.cone_inner_angle,outer=li.cone_outer_angle,flags=li.flags.value,volume=li.volume_intensity))
summary={}
for group in sorted(set(r['group'] for r in models)):
 subset=[r for r in rows if r['group']==group]
 summary[group]=dict(models_checked=sum(r['group']==group for r in models),native_lights=len(subset),types=dict(Counter(r['type'] for r in subset)))
 for key in ['intensity','range','falloff_exponent','inner','outer']:
  vals=[r[key] for r in subset if key not in ['inner','outer'] or r['type']=='SPOT']
  summary[group][key]=dict(zip(['min','median','max'],map(float,np.quantile(vals,[0,.5,1])))) if vals else None
print(json.dumps(summary,indent=2),flush=True)
(P/'reference_lights.json').write_text(json.dumps(dict(source='Read-only local original GTA V RPF assets; no game files changed or copied into server resource.',summary=summary,models=models,lights=rows),indent=2))
