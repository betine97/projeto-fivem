import json,hashlib,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao';O=P/'package';B=P/'backup'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
baseline=json.loads((P/'baseline.json').read_text())
assert json.loads((P/'verification.json').read_text())['passed']
assert json.loads((P/'native_validation.json').read_text(encoding='utf-8-sig'))['passed']
files=[f for f in O.rglob('*') if f.is_file()];changed=[f.relative_to(O).as_posix() for f in files]
for rel in changed:
 if rel in baseline:assert sha(D/rel)==baseline[rel],('Concurrent target changed',rel)
 else:assert not (D/rel).exists(),('New target already exists',rel)
for f in files:
 rel=f.relative_to(O);dst=B/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 if (D/rel).exists():shutil.copy2(D/rel,dst)
for f in files:shutil.copy2(f,D/f.relative_to(O))
assert all(sha(D/f.relative_to(O))==sha(f) for f in files)
untouched=[rel for rel in baseline if rel not in changed]
assert all(sha(D/rel)==baseline[rel] for rel in untouched),'Unrelated concurrent edit detected'
(P/'installation.json').write_text(json.dumps({'installed':True,'changed':changed,'unrelated_files_preserved':len(untouched),'palm_exclusions_hd_and_lod':True,'restart_required':True,'in_game_verified':False},indent=2))
print('INSTALLED',len(files),'files;',len(untouched),'unrelated files preserved')
