"""Install only the validated MLO files; retain an immutable pre-change backup."""
import json,hashlib,shutil,sys
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao'
B=P/'backup';O=P/'package'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((P/'baseline.json').read_text())
targets=['stream/'+name for name in ['mansao_paredes.ydr','mansao_pisos.ydr','mansao_escada.ydr','mansao_teto.ydr','mansao_teto.ybn','cidade_mansao.ytyp','cidade_mansao.ymap']]+['clima_interior.json']
originals=[rel for rel in targets+['fxmanifest.lua'] if rel in baseline]
for rel in originals:
    assert sha(D/rel)==baseline[rel],f'{rel} changed after backup; do not overwrite newer work'
assert json.loads((P/'native_verification.json').read_text())['native_roundtrip']
assert len(json.loads((P/'weather_tests.json').read_text())['checks_passed'])==31
# Keep a reproducible copy of the runtime code together with the native package.
for rel in ['clima_shared.lua','clima_client.lua','clima_interior.xml']:
    shutil.copy2(D/rel,O/rel)
for rel in targets:
    src=O/Path(rel).name;dst=D/rel
    assert src.is_file();shutil.copy2(src,dst);assert sha(src)==sha(dst)
manifest=D/'fxmanifest.lua'
addition="""

-- Local indoor climate: real MLO rooms and structural collision, no global weather override.
files { 'clima_interior.json', 'clima_interior.xml' }
data_file 'TIMECYCLEMOD_FILE' 'clima_interior.xml'
client_script 'clima_shared.lua'
client_script 'clima_client.lua'
"""
manifest.write_text(manifest.read_text(encoding='utf-8').rstrip()+addition,encoding='utf-8')
shutil.copy2(manifest,O/'fxmanifest.lua')
allowed=set(targets+['fxmanifest.lua','README.md'])
preserved=[]
for rel,h in baseline.items():
    if rel in allowed:continue
    assert sha(D/rel)==h,f'Unexpected modification: {rel}'
    preserved.append(rel)
report={'installed':{rel:sha(D/rel) for rel in targets+['fxmanifest.lua','clima_shared.lua','clima_client.lua','clima_interior.xml']},
    'untouched_files_verified':preserved,'native_roundtrip':True,'lua_checks':31,'polygon_samples':3000,
    'in_game_verified':False,'activation':'restart cidade_mansao in server console; reconnect clients'}
(P/'installation_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('WEATHER_INSTALLED:',len(targets)+4,'files;',len(preserved),'existing files preserved')
