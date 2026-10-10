import sys,json
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset
out=Path(__file__).resolve().parent
base=open_rpf(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V\x64v.rpf').open_nested('models/cdimages/streamedpeds_mp.rpf')
names=base.list_dir('mp_m_freemode_01')
print([n for n in names if n.startswith(('jbib_015','berd_000','accs_000','task_000','decl_000','teef_015','feet_')) and n.endswith('.ydd')])
for n in ['jbib_015_u.ydd','berd_000_u.ydd','accs_000_u.ydd','task_000_u.ydd','decl_000_u.ydd','teef_015_u.ydd']:
 if n in names:
  (out/n).write_bytes(base.read_bytes('mp_m_freemode_01/'+n))
print('EXTRACTED AUDIT')
for p in sorted((out.parent.parent.parent/'templates_freemode/source').glob('feet_*.ydd')):
 a=try_load_asset(p)
 print(p.name,type(a),type(a.drawables),len(a.drawables))
 d=list(a.drawables.values())[0]
 print(' ATTRS',[k for k in dir(d) if not k.startswith('_')])
 break
