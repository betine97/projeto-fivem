import sys,json
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset
out=Path(__file__).resolve().parent
base=open_rpf(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V\x64v.rpf').open_nested('models/cdimages/streamedpeds_mp.rpf')
names=base.list_dir('mp_m_freemode_01')
for n in names:
 if n.startswith('accs_') and n.endswith('.ydd') or n.startswith('accs_diff_000_a'):
  (out/n).write_bytes(base.read_bytes('mp_m_freemode_01/'+n))
a=try_load_asset(out/'accs_000_u.ydd');d=list(a.drawables.values())[0]
print('bounds',d.bounds,'models',d.models)
print('modelattrs',[k for k in dir(next(iter(d.models.values()))[0]) if not k.startswith('_')])
