"""Install only the six validated lighting files, refusing concurrent edits."""
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

p = Path(__file__).resolve().parent
resource = p.parents[1] / 'server-data/resources/cidade_mansao'
project = json.loads((p / 'project.json').read_text(encoding='utf-8'))
targets = project['targets']
expected_targets = {
    'stream/mansao_teto.ydr', 'stream/mansao_pendentes.ydr',
    'stream/mansao_tv.ydr', 'iluminacao_ambiente.json',
    'luzes_pendentes.json', 'iluminacao_decorativa.lua',
}
assert set(targets) == expected_targets and len(targets) == 6
baseline = json.loads((p / 'baseline.json').read_text(encoding='utf-8'))
verification = json.loads((p / 'verification.json').read_text(encoding='utf-8'))
native = json.loads((p / 'codewalker_verification.json').read_text(encoding='utf-8-sig'))
assert verification['passed'] is True
assert {r['model']: r['lights'] for r in native} == {
    'mansao_teto.ydr': 116, 'mansao_pendentes.ydr': 9, 'mansao_tv.ydr': 4,
}
assert all(r['nativeLoaded'] is True for r in native)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def snapshot():
    return {f.relative_to(resource).as_posix(): sha(f)
            for f in resource.rglob('*') if f.is_file()}

before = snapshot()
staged = {rel: sha(p / 'package' / rel) for rel in targets}
for rel in targets:
    assert sha(p / 'backup' / rel) == baseline[rel], f'Backup changed: {rel}'
    assert before[rel] == baseline[rel], f'Concurrent lighting change: {rel}'

installed = []
try:
    for rel in targets:
        destination = resource / rel
        assert sha(destination) == baseline[rel], f'Concurrent lighting change: {rel}'
        temp = destination.with_name(destination.name + '.warm-reference-install.tmp')
        assert not temp.exists(), f'Temporary file exists: {temp}'
        try:
            shutil.copy2(p / 'package' / rel, temp)
            assert sha(temp) == staged[rel]
            assert sha(destination) == baseline[rel], f'Concurrent lighting change: {rel}'
            os.replace(temp, destination)
            installed.append(rel)
        finally:
            if temp.exists():
                temp.unlink()
except Exception:
    for rel in reversed(installed):
        destination = resource / rel
        if sha(destination) == staged[rel]:
            restore = destination.with_name(destination.name + '.warm-reference-restore.tmp')
            shutil.copy2(p / 'backup' / rel, restore)
            os.replace(restore, destination)
    raise

after = snapshot()
assert all(after[rel] == staged[rel] for rel in targets)
concurrent_other = sorted(rel for rel in set(before) | set(after)
                          if rel not in expected_targets and before.get(rel) != after.get(rel))
report = {
    'installed': True,
    'installed_at_utc': datetime.now(timezone.utc).isoformat(),
    'resource': str(resource),
    'only_written_targets': targets,
    'sha256': staged,
    'concurrent_other_changes_observed': concurrent_other,
    'native_validation_passed': True,
    'visual_match_verified': False,
    'server_restarted': False,
    'resource_restarted': False,
    'backup': str(p / 'backup'),
}
(p / 'installation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
