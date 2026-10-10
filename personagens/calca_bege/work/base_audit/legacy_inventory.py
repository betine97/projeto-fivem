import sys
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.rpf import open_rpf
root=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V')
r=open_rpf(root/'x64w.rpf')
for d in ['mpbeach','mpbusiness','mphipster','mppilot']:
 nr=r.open_nested('dlcpacks/'+d+'/dlc.rpf')
 for p in ['','x64','x64/models','x64/models/cdimages']:
  if nr.is_dir(p):print(d,p,list(nr.list_dir(p)))
