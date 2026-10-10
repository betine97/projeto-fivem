"""Record checked disk contents only. Does not restart server/game."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
RESOURCE=ROOT/'server-data/resources/cidade_core'
COVER=ROOT/'animacoes/cobertura_rapida'
def read(path):return json.loads(path.read_text(encoding='utf8'))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf8')

runtime=read(HERE/'runtime_v8_checks.json')
exit_checks=read(HERE/'exit_failure_v8_checks.json')
cover_checks=read(COVER/'test_results.json')
assert runtime['source_sha256']==digest(RESOURCE/'prone.lua')
assert cover_checks['source_sha256']==digest(RESOURCE/'cover.lua')
assert 'cover.lua' in (RESOURCE/'fxmanifest.lua').read_text()
assert 'ClearPedLookAt' not in (RESOURCE/'prone.lua').read_text()
preserved=[]
for asset in read(HERE/'v6_installation.json')['assets']:
    installed=RESOURCE/'stream'/Path(asset['file']).name
    assert digest(installed)==asset['sha256'],str(installed)
    preserved.append({'file':str(installed),'sha256':asset['sha256'],'unchanged':True})
scripts=[{'file':str(RESOURCE/name),'sha256':digest(RESOURCE/name)}
         for name in ('prone.lua','cover.lua','combat_weapon.lua','combat_mounts.lua','fxmanifest.lua')]
save(HERE/'v8_installation.json',{
    'revision':runtime['revision'],'installed_on_disk':True,'server_restarted':False,
    'game_tested':False,'root_cause_confirmed_in_live_log':True,
    'source_log':'CitizenFX_log_2026-10-07T194654.log','scripts':scripts,
    'preserved_ycd':preserved,'runtime_checks':runtime,'exit_checks':exit_checks,
})
save(COVER/'installation_v2.json',{
    'revision':cover_checks['revision'],'installed_on_disk':True,'server_restarted':False,
    'game_tested':False,'default_key':'Q','new_ycd_exported':False,
    'animation_source':'GTA native cover and crouched movement clipsets',
    'posture_revision':runtime['revision'],'scripts':scripts,'tests':cover_checks,
})
print('DISK_INSTALLATION_VERIFIED: v8 + cover v2; 3 YCD hashes unchanged; no live restart')
