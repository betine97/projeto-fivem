import sys, json, hashlib
from pathlib import Path
sys.path.insert(0, r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.rpf import open_rpf
root=Path(__file__).resolve().parents[1]/'source'
root.mkdir(exist_ok=True)
r=open_rpf(Path(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V\x64v.rpf')).open_nested('models/cdimages/streamedpeds_mp.rpf')
files=r.list_dir('mp_m_freemode_01')
selected=[f for f in files if ((f.startswith(('lowr_','feet_','uppr_')) and f.endswith('.ydd')) or f=='head_000_r.ydd' or (f.startswith(('lowr_diff_','feet_diff_','uppr_diff_','head_diff_000')) and '_a_' in f and f.endswith('.ytd')))]
manifest=[]
for n in ['mp_m_freemode_01.yft','mp_m_freemode_01.ymt']+selected:
    p=n if n not in selected else 'mp_m_freemode_01/'+n
    data=r.read_bytes(p)
    (root/n).write_bytes(data)
    manifest.append(dict(file=n,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),archive_path=p))
(root/'source_manifest.json').write_text(json.dumps(manifest,indent=2))
print('Extracted',len(manifest),'files')
print([f for f in selected if f.endswith('.ydd')])
