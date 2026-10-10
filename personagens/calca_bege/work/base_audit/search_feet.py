import sys,json,os
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.rpf import open_rpf
out=Path(__file__).resolve().parent
root=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V')
found=[]
for ap in sorted((root/'update/x64/dlcpacks').glob('*/dlc.rpf')):
 if 'g9ec' in str(ap).lower():continue
 try:
  r=open_rpf(ap)
  for cd in ['x64/models/cdimages','x64/models','']:
   if not r.is_dir(cd):continue
   for n in r.list_dir(cd):
    if not n.endswith('.rpf') or n.endswith('_p.rpf') or 'weapons' in n:continue
    nr=r.open_nested((cd+'/' if cd else '')+n)
    for d in nr.list_dir(''):
     if not d.startswith('mp_m_freemode_01') or not nr.is_dir(d):continue
     for f in nr.list_dir(d):
      if f.startswith('feet_') and f.endswith('_r.ydd'):
       print(ap.parent.name,d,f,flush=True)
       found.append({'archive':str(ap),'nested':(cd+'/' if cd else '')+n,'dir':d,'file':f})
  r.close()
 except Exception as e: print('ERR',ap.parent.name,str(e)[:100])
for rp in ['x64w.rpf','x64v.rpf']:
 r=open_rpf(root/rp);print(rp,r.list_dir(''));r.close()
(out/'barefoot_candidates.json').write_text(json.dumps(found,indent=2))
print('COUNT',len(found))

