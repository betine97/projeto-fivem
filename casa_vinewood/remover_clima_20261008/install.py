"""Install the verified, narrowly scoped climate rollback without restarting the server."""
import json,hashlib,shutil,os
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
D=R/'server-data/resources/cidade_mansao';O=P/'package'
report=json.loads((P/'verification.json').read_text())
baseline=json.loads((P/'baseline.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
changed=report['changed'];removed=report['removed']
assert report['native_mlo_removed'] and report['native_lights_preserved']==68
for rel in changed+removed:
    assert sha(D/rel)==baseline[rel],f'Concurrent modification: {rel}'
for rel in changed:
    src=O/rel;dst=D/rel
    assert src.is_file() and dst.resolve().is_relative_to(D.resolve())
    tmp=dst.with_name(dst.name+'.climate-rollback-tmp')
    shutil.copy2(src,tmp);os.replace(tmp,dst)
    assert sha(dst)==sha(src)
for rel in removed:
    dst=D/rel;saved=P/'backup_before_removal'/rel
    assert dst.resolve().is_relative_to(D.resolve())
    assert saved.is_file() and sha(saved)==sha(dst)==baseline[rel]
    # Explicit files only, already backed up; no recursive removal or cache wipe.
    dst.unlink()
preserved=[]
for rel,old_hash in baseline.items():
    if rel in changed+removed:continue
    assert sha(D/rel)==old_hash,f'Unrelated file modified: {rel}'
    preserved.append(rel)
assert all(not (D/rel).exists() for rel in removed)
assert 'clima_' not in (D/'fxmanifest.lua').read_text()
result={**report,'installed':{rel:sha(D/rel) for rel in changed},
    'unchanged_files_verified':preserved,'files_removed_verified':removed,
    'activation':'Server console: ensure cidade_mansao (or restart if running); fully close FiveM and reconnect.',
    'server_restarted':False,'in_game_verified':False}
(P/'installation_verification.json').write_text(json.dumps(result,indent=2))
print('INSTALLED:',len(changed),'changed files;',len(removed),'climate files removed;',len(preserved),'unrelated files preserved')
