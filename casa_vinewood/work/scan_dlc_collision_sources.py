"""Find additional GTA Online/DLC collision files for this map sector."""
import sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.rpf import open_rpf
G=Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V')
targets=[G/'update/update.rpf']+list((G/'update/x64/dlcpacks').glob('*/dlc.rpf'));found=[]
def walk(r,folder='',prefix='',depth=0):
 for name in r.list_dir(folder):
  p=folder+'/'+name if folder else name
  if r.is_dir(p):walk(r,p,prefix,depth)
  elif p.lower().endswith('.rpf') and depth<5:
   try:walk(r.open_nested(p),'',prefix+'|'+p,depth+1)
   except Exception:pass
  elif p.lower().endswith('.ybn') and any(k in p.lower() for k in ('ch2_09','stilthouse','hs05')):
   f=prefix+'|'+p;found.append(f);print('FOUND',f,flush=True)
for f in targets:
 try:walk(open_rpf(f),prefix=str(f.relative_to(G)))
 except Exception as e:print('ERROR',f.name,type(e).__name__,flush=True)
(W/'work/dlc_collision_sources.txt').write_text('\n'.join(found))
print('DLC_SCAN_DONE',len(targets),'archives',len(found),'matches',flush=True)
