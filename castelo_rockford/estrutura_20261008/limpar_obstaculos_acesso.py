import sys,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(R/'casa_vinewood/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from shapely.geometry import shape,Point
from szio.gta5 import try_load_asset
from szio.rpf import open_rpf
import pymateria.gta5 as pm
plan=json.loads((P/'implantacao.json').read_text());affected=shape(plan['affected']);props=[];extra=P/'originais_adicionais';extra.mkdir(exist_ok=True)
dlcs=json.loads((R/'castelo_rockford/dlc_sources.json').read_text())
for name in ['bh1_45_strm_0.ymap','hei_bh1_45_strm_0.ymap']:
 if name.startswith('hei_'):raw=(R/'castelo_rockford/originais'/name).read_bytes()
 else:
  path=next(s for s in dlcs if 'patchday27ng' in s and s.endswith('|'+name));parts=path.split('|');arc=open_rpf(Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V')/parts[0])
  for q in parts[1:-1]:arc=arc.open_nested(q)
  raw=arc.read_bytes(parts[-1])
 src=extra/name;src.write_bytes(raw);a=pm.MapData.import_rsc(src).result;resolved=try_load_asset(src).entities;removed=[];retained=[]
 for i,e in enumerate(a.entities):
  pos=[e.position.x,e.position.y,e.position.z];label=str(resolved[i].archetype_name)
  gate=label in ['prop_lrggate_01_l','prop_lrggate_01_r'] and Point(pos[:2]).distance(Point(*plan['grade_gate']))<4
  obstacle=affected.buffer(-.025).covers(Point(pos[:2])) and 62.9<pos[2]<92 and not label.startswith('bh1')
  if gate or obstacle:
   assert e.parent_index==-1 and e.num_children==0
   removed.append({'name':label,'position':pos});continue
  retained.append(e)
 # Map-level fields and opaque extensions remain in the original native form.
 a.entities=retained;out=P/'terrain/stream'/name;pm.MapData.export_rsc(a,out)
 assert len(pm.MapData.import_rsc(out).result.entities)==len(retained)
 props.append({'file':name,'source_sha256':hashlib.sha256(raw).hexdigest(),'before':len(resolved),'after':len(retained),'removed':removed})
 print('ACCESS_OBSTACLES',name,len(removed),[q['name'] for q in removed],flush=True)
(P/'obstaculos_acesso.json').write_text(json.dumps(props,indent=2),encoding='utf-8')
