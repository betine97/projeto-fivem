"""Install the local verified light-only patch, rejecting concurrent target edits."""
import json,hashlib,shutil,os
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao';O=P/'package'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
tests=json.loads((P/'verification.json').read_text());assert tests['passed']
cw=json.loads((P/'codewalker_verification.json').read_text(encoding='utf-8-sig'));assert sum(r['lights'] for r in cw)==97
baseline=json.loads((P/'baseline.json').read_text())
changes={f.relative_to(O).as_posix():f for f in O.rglob('*') if f.is_file()}
before={f.relative_to(D).as_posix():sha(f) for f in D.rglob('*') if f.is_file()}
assert len(changes)==15 and 'fxmanifest.lua' not in changes
assert all(before.get(n)==baseline.get(n) for n in changes),'Concurrent lighting target change: inspect before installing'
for rel,src in changes.items():
    dst=D/rel;assert dst.resolve().is_relative_to(D.resolve())
    assert sha(P/'backup'/rel)==before[rel]
    temp=dst.with_name(dst.name+'.fixture-only-update')
    shutil.copy2(src,temp);os.replace(temp,dst)
after={f.relative_to(D).as_posix():sha(f) for f in D.rglob('*') if f.is_file()}
assert before.keys()==after.keys()
for rel in after:
    assert after[rel]==(sha(changes[rel]) if rel in changes else before[rel]),rel
report=dict(installed=True,changed={n:after[n] for n in changes},unrelated_live_files_preserved=len(before)-len(changes),
    native_sources=97,only_fixture_spotlights=True,decorative_and_room_fill_disabled=True,
    floor_radius_m=dict(spot_and_cylinder=1.10,linear=.80),floor_reach_verified=True,
    brightness_multiplier_minimum=tests['native_brightness_multiplier_minimum'],script_light_calls=0,
    maps_manifest_props_and_other_resources_unmodified=True,server_restarted=False,in_game_visual_verified=False)
(P/'installation_verification.json').write_text(json.dumps(report,indent=2))
print('INSTALLED',len(changes),'lighting files;',report['unrelated_live_files_preserved'],'unrelated live files preserved; 97 narrow fixture sources, no fill',flush=True)
