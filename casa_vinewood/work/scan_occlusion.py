"""Inspect native occluders near the house across the base game and DLC."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset
G=Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V')
targets=[G/'update/update.rpf',G/'x64o.rpf']+list((G/'update/x64/dlcpacks').glob('*/dlc.rpf'))
found=[]
def walk(r,folder='',prefix='',depth=0):
 for name in r.list_dir(folder):
  p=folder+'/'+name if folder else name
  if r.is_dir(p):walk(r,p,prefix,depth)
  elif p.lower().endswith('.rpf') and depth<5:
   try:walk(r.open_nested(p),'',prefix+'|'+p,depth+1)
   except Exception:pass
  elif p.lower().endswith('.ymap') and 'occl' in p.lower() and ('ch2' in p.lower() or 'apa' in p.lower() or 'hei' in p.lower()):
   dest=W/'work/occlusion_sources'/Path(p).name;dest.parent.mkdir(exist_ok=True)
   data=r.read_bytes(p)
   # update.rpf precedes DLC: keep its newer version of duplicate names.
   if not dest.exists():dest.write_bytes(data)
   found.append({'path':prefix+'|'+p,'file':dest.name,'bytes':len(data)})
for f in targets:
 try:walk(open_rpf(f),prefix=str(f.relative_to(G)))
 except Exception as e:print('ERROR',f.name,type(e).__name__,flush=True)
(W/'work/occlusion_sources.json').write_text(json.dumps(found,indent=2))
print('OCCLUSION_SOURCES',len(found),len({x['file'] for x in found}),flush=True)
for p in sorted((W/'work/occlusion_sources').glob('*.ymap')):
 a=try_load_asset(p)
 print(p.name,'boxes',len(a.box_occluders),'models',len(a.model_occluders),flush=True)
 if a.box_occluders:
  print('box sample',str(a.box_occluders[0])[:200],[k for k in dir(a.box_occluders[0]) if not k.startswith('_')],flush=True)
