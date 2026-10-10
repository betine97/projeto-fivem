import sys
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.rpf import open_rpf
root=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V')
for d in ['mppatchesng','mpapartment','mplowrider','mpluxe','mpluxe2','mpreplay']:
 r=open_rpf(root/'update/x64/dlcpacks'/d/'dlc.rpf')
 for p in ['','x64','x64/models','x64/models/cdimages']:
  if r.is_dir(p):print(d,p,list(r.list_dir(p)))
