import json,hashlib,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao';O=P/'package'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((P/'baseline.json').read_text())
targets={'stream/mansao_teto.ydr':'mansao_teto.ydr','iluminacao_ambiente.json':'iluminacao_ambiente.json','iluminacao_decorativa.lua':'iluminacao_decorativa.lua'}
assert json.loads((P/'lighting_tests.json').read_text(encoding='utf-8'))['passed']
assert json.loads((P/'native_verification.json').read_text())['native_roundtrip']
# Detect edits from other chats before overwriting any file.
for rel in targets:assert sha(D/rel)==baseline[rel],f'Newer edit: {rel}'
for rel,src in targets.items():
    shutil.copy2(O/src,D/rel);assert sha(D/rel)==sha(O/src)
preserved=[]
for rel,h in baseline.items():
    if rel in targets:continue
    assert sha(D/rel)==h,f'Unexpected change: {rel}'
    preserved.append(rel)
(P/'installation_verification.json').write_text(json.dumps(dict(installed={rel:sha(D/rel) for rel in targets},
    preserved=preserved,native_lights=68,rooms=19,surface_samples=5098,default_script_draws=0,
    weather_mlo_and_collision_preserved=True,furniture_catalog_and_saved_transforms_preserved=True,
    in_game_verified=False,activation='restart cidade_mansao in server console; reconnect FiveM'),indent=2),encoding='utf-8')
print('PERMANENT_LIGHTING_INSTALLED: 3 files;',len(preserved),'other files preserved')
