import sys,json
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.rpf import open_rpf
out=Path(__file__).resolve().parent
root=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V')
for dlc in ['mpheist','mpapartment']:
 r=open_rpf(root/'update/x64/dlcpacks'/dlc/'dlc.rpf')
 def walk(p=''):
  for n in r.list_dir(p):
   path=(p+'/' if p else '')+n
   if r.is_dir(path):walk(path)
   elif n.endswith(('.meta','.xml','.ymt')):
    print(dlc,path)
    if n.endswith(('.meta','.xml')):
     text=r.read_bytes(path).decode('utf-8','replace')
     if 'ped' in path.lower() or 'apparel' in text.lower() or 'heist' in text.lower() or 'apartment' in text.lower():
      (out/(dlc+'__'+path.replace('/','__'))).write_text(text,encoding='utf-8')
 walk()
 cd='x64/models/cdimages'
 for n in r.list_dir(cd):
  if n.endswith('.rpf') and not n.endswith('_p.rpf') and 'weapons' not in n:
   nr=r.open_nested(cd+'/'+n)
   roots=list(nr.list_dir(''))
   print('INNER',dlc,n,roots)
   for f in roots:
    if f.startswith('mp_m_') and f.endswith('.ymt'):
     (out/(dlc+'__'+f)).write_bytes(nr.read_bytes(f))
