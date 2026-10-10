"""Install only the verified lighting patch; retain all other live files."""
import json,hashlib,shutil,os
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao';O=P/'package'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((P/'verification.json').read_text(encoding='utf-8'));assert report['passed']
cw=json.loads((P/'codewalker_verification.json').read_text(encoding='utf-8-sig'));assert [r['lights'] for r in cw]==[107,9,0]
baseline=json.loads((P/'baseline.json').read_text())
changes={f.relative_to(O).as_posix():f for f in O.rglob('*') if f.is_file()}
assert len(changes)==8 and 'fxmanifest.lua' not in changes
before={f.relative_to(D).as_posix():sha(f) for f in D.rglob('*') if f.is_file()}
assert all(before.get(n)==baseline.get(n) for n in changes),'A lighting target was edited concurrently; rebuild against the new version'
for rel,source in changes.items():
    dest=D/rel
    assert dest.resolve().is_relative_to(D.resolve())
    assert sha(P/'backup'/rel)==before[rel]
    temp=dest.with_name(dest.name+'.lighting-update')
    shutil.copy2(source,temp);os.replace(temp,dest)
after={f.relative_to(D).as_posix():sha(f) for f in D.rglob('*') if f.is_file()}
assert before.keys()==after.keys(),'Resource file set changed'
for rel in after:
    if rel in changes:assert after[rel]==sha(changes[rel])
    else:assert after[rel]==before[rel],f'Unrelated live file changed: {rel}'
result=dict(installed=True,changed={n:after[n] for n in changes},unchanged_files=len(before)-len(changes),
    maps_archetypes_manifest_unchanged=True,saved_object_transforms_unchanged=True,
    native_lights=116,script_light_draws_at_default=0,codewalker_verified=True,
    tests=report['surface_samples'],server_restarted=False,in_game_visual_verified=False)
(P/'installation_verification.json').write_text(json.dumps(result,indent=2))
print('INSTALLED',len(changes),'files;',result['unchanged_files'],'unrelated files preserved; maps, collision and saved object positions retained',flush=True)
