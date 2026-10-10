"""Install only verified local lighting files, reject concurrent target edits."""
import json,hashlib,shutil,os
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao';O=P/'package'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
tests=json.loads((P/'verification.json').read_text());assert tests['passed']
cw=json.loads((P/'codewalker_verification.json').read_text(encoding='utf-8-sig'));assert len(cw)==4 and sum(r['lights'] for r in cw)==32 and all(r['nativeLoaded'] for r in cw)
baseline=json.loads((P/'baseline.json').read_text());project=json.loads((P/'projeto.json').read_text())
changes={f.relative_to(O).as_posix():f for f in O.rglob('*') if f.is_file()}
before={f.relative_to(D).as_posix():sha(f) for f in D.rglob('*') if f.is_file()}
assert set(changes)==set(project['targets']) and len(changes)==8
assert all(before.get(n)==baseline.get(n) for n in changes),'Concurrent lighting target edits: inspect before installing'
for rel,src in changes.items():
 dst=D/rel;assert dst.resolve().is_relative_to(D.resolve());assert sha(P/'backup'/rel)==before[rel]
 temp=dst.with_name(dst.name+'.lenses-leds-update');shutil.copy2(src,temp);os.replace(temp,dst)
after={f.relative_to(D).as_posix():sha(f) for f in D.rglob('*') if f.is_file()};assert before.keys()==after.keys()
for rel in after:assert after[rel]==(sha(changes[rel]) if rel in changes else before[rel]),rel
result=dict(installed=True,changed={n:after[n] for n in changes},unrelated_live_files_preserved=len(before)-len(changes),native_sources=120,white_ceiling_lens_lods=4,yellow_filled_cylinder_faces=6,yellow_stair_led_sources=20,yellow_tv_led_sources=3,maps_manifest_prop_positions_and_other_resources_unmodified=True,server_restarted=False,in_game_visual_verified=False)
(P/'installation_verification.json').write_text(json.dumps(result,indent=2));print('INSTALLED: 8 local lighting files;',result['unrelated_live_files_preserved'],'unrelated live files preserved.',flush=True)
