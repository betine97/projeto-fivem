import sys,shutil,json,hashlib
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.rpf import open_rpf
root=Path(__file__).resolve().parents[1];out=root/'source';out.mkdir(parents=True,exist_ok=True)
r=open_rpf(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V\update\x64\dlcpacks\mpheist\dlc.rpf').open_nested('x64/models/cdimages/mpheist_streamedpeds.rpf')
d='mp_m_freemode_01_male_heist';names=r.list_dir(d);manifest=[]
for name in names:
 if name.startswith(('jbib_','lowr_','berd_','feet_')) and (name.endswith('_u.ydd') or name.endswith('_r.ydd') or ('_a_' in name and name.endswith('.ytd'))):
  data=r.read_bytes(d+'/'+name);(out/name).write_bytes(data);manifest.append({'name':name,'sha256':hashlib.sha256(data).hexdigest()})
shutil.copy2(root.parent/'templates_freemode/source/mp_m_freemode_01.yft',out/'mp_m_freemode_01.yft')
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('EXTRACTED',len(manifest))
