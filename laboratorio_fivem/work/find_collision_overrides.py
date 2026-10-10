import sys
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.rpf import open_rpf
root=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V')
targets=[root/'update/update.rpf']
targets+=list((root/'update/x64/dlcpacks').glob('*/dlc.rpf'))
def walk(r,folder='',prefix='',depth=0):
 for name in r.list_dir(folder):
  p=folder+'/'+name if folder else name
  if r.is_dir(p):walk(r,p,prefix,depth)
  elif p.lower().endswith('.rpf') and depth<4:
   try:walk(r.open_nested(p),'',prefix+'|'+p,depth+1)
   except Exception:pass
  elif 'ch3_08' in p.lower() and p.lower().endswith(('.ybn','.rpf')):print(prefix+'|'+p,flush=True)
for f in targets:
 try:walk(open_rpf(f),prefix=str(f.relative_to(root)));print('SCANNED',f.relative_to(root),flush=True)
 except Exception as e:print('ERROR',f.relative_to(root),repr(e),flush=True)
