import sys,json
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.rpf import open_rpf
base=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'); out=[]
def walk(r,folder='',prefix='',depth=0):
 for name in r.list_dir(folder):
  p=folder+'/'+name if folder else name
  if r.is_dir(p):walk(r,p,prefix,depth)
  elif p.endswith('.rpf') and depth<2:
   try:walk(r.open_nested(p),'',prefix+p+'|',depth+1)
   except:pass
  elif p.endswith(('.ydr','.ymap','.ybn','.ytyp')):out.append(prefix+p)
for f in base.glob('x64*.rpf'):
 try:walk(open_rpf(f),prefix=f.name+'|')
 except:pass
Path('laboratorio_fivem/work/assets_index.txt').write_text('\n'.join(out))
print(len(out))
