"""Guarded, atomic replacement of only the assets and targeted rug renderer in this revision."""
import json,hashlib,os
from pathlib import Path
from datetime import datetime
P=Path(__file__).resolve().parent;D=P.parents[1]/'server-data/resources/cidade_mansao'
verification=json.loads((P/'verification.json').read_text());independent=json.loads((P/'codewalker_validation.json').read_text(encoding='utf-8-sig'));baseline=json.loads((P/('installation_baseline_hashes.json' if (P/'installation_baseline_hashes.json').exists() else 'baseline_hashes.json')).read_text())
assert verification['passed'] and independent['passed'] and independent['validated']==verification['assets_loaded']
sha=lambda d:hashlib.sha256(d).hexdigest()
targets={n:(P/n).read_bytes() for n in verification['install_files']}
before={n:(D/n).read_bytes() if (D/n).exists() else None for n in targets}
for n,data in before.items():assert (sha(data) if data is not None else None)==baseline.get(n),('Concurrent change',n)
untouched={f.relative_to(D).as_posix():sha(f.read_bytes()) for f in D.rglob('*') if f.is_file() and f.relative_to(D).as_posix() not in targets}
backup=P/'backup_preinstall'/datetime.now().strftime('%Y%m%d_%H%M%S');backup.mkdir(parents=True)
for n,data in before.items():
    if data is not None:
        f=backup/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data)
changed=[]
try:
    for n,data in targets.items():
        f=D/n;current=f.read_bytes() if f.exists() else None;assert current==before[n],('Concurrent write',n)
        if current==data:continue
        f.parent.mkdir(parents=True,exist_ok=True);tmp=f.with_name(f.name+'.render-repair-stage')
        tmp.write_bytes(data);os.replace(tmp,f);changed.append(n)
except Exception:
    for n in reversed(changed):
        f=D/n
        if f.read_bytes()!=targets[n]:continue
        if before[n] is None:f.unlink()
        else:f.write_bytes(before[n])
    raise
assert all((D/n).read_bytes()==data for n,data in targets.items())
assert all(sha((D/n).read_bytes())==h for n,h in untouched.items())
report={'installed':True,'files_changed':changed,'backup':str(backup.resolve()),'verification':verification['checks'],'unrelated_files_preserved':len(untouched),'in_game_verified':False,'resource_restart_required':True}
(P/'installation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('INSTALLED',len(changed),'files; unrelated files preserved:',len(untouched),flush=True)
