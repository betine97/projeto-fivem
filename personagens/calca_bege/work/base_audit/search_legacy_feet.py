import sys,json
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset
out=Path(__file__).resolve().parent
root=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V')
r=open_rpf(root/'x64w.rpf');print(r.list_dir('dlcpacks'))
for d in r.list_dir('dlcpacks'):
 if not r.is_dir('dlcpacks/'+d): continue
 print(d,r.list_dir('dlcpacks/'+d))
 if not r.exists('dlcpacks/'+d+'/dlc.rpf'):continue
 nr=r.open_nested('dlcpacks/'+d+'/dlc.rpf')
 cd='x64/models/cdimages'
 if not nr.is_dir(cd):continue
 for n in nr.list_dir(cd):
  if not n.endswith('.rpf') or n.endswith('_p.rpf') or n=='weapons.rpf':continue
  inner=nr.open_nested(cd+'/'+n)
  for mpd in inner.list_dir(''):
   if not mpd.startswith('mp_m_freemode_01') or not inner.is_dir(mpd):continue
   print('COL',mpd)
   for f in inner.list_dir(mpd):
    if f.startswith('feet_') and f.endswith('.ydd'):
     print(f)
     if f.endswith('_r.ydd'):
      (out/(mpd+'^'+f)).write_bytes(inner.read_bytes(mpd+'/'+f))
      for td in inner.list_dir(mpd):
       if td.startswith('feet_diff_'+f[5:8]) and '_a_' in td and td.endswith('.ytd'):
        (out/(mpd+'^'+td)).write_bytes(inner.read_bytes(mpd+'/'+td))

