"""Inspect native Online map layers for duplicated nearby props, read only."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';N=W/'work/native'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset
G=Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V')
origin=np.array(json.loads((W/'medidas_estudo.json').read_text())['native_origin']);found=[];props=[];seen=set()
def walk(r,folder='',prefix='',depth=0):
 for name in r.list_dir(folder):
  p=folder+'/'+name if folder else name
  if r.is_dir(p):walk(r,p,prefix,depth)
  elif p.lower().endswith('.rpf') and depth<5:
   try:walk(r.open_nested(p),'',prefix+'|'+p,depth+1)
   except Exception:pass
  elif p.lower().endswith('.ymap') and 'ch2_09b' in p.lower():
   f=N/Path(p).name;found.append(prefix+'|'+p)
   if f.name in seen:return
   seen.add(f.name)
   if not f.exists():f.write_bytes(r.read_bytes(p))
   a=try_load_asset(f)
   for i,e in enumerate(a.entities):
    q=np.array(e.position)-origin
    if np.linalg.norm(q[:2])<35 and -12<q[2]<12:
     props.append(dict(map=f.name,index=i,name=str(e.archetype_name),pos=list(e.position),rot=list(e.rotation),scale=[e.scale_xy,e.scale_xy,e.scale_z]))
for f in [G/'update/update.rpf',*list((G/'update/x64/dlcpacks').glob('*/dlc.rpf'))]:
 try:walk(open_rpf(f),prefix=str(f.relative_to(G)))
 except Exception as ex:print('SCAN_ERROR',f.name,type(ex).__name__,flush=True)
(W/'work/dlc_near_house_props.json').write_text(json.dumps(props,indent=2))
(W/'work/dlc_plant_map_sources.json').write_text(json.dumps(found,indent=2))
print('DLC_MAPS',len(found),'NEARBY_PROPS',len(props),flush=True)
for e in props:
 if any(k in e['name'] for k in ['plant','bush','pot','tree']):print(e['map'],e['name'],np.round(np.array(e['pos'])-origin,3).tolist(),e['scale'],flush=True)
