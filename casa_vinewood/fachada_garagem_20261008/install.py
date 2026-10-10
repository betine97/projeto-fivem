"""Install only the measured facade and garage changes, with byte guards and backup."""
import sys, json, hashlib, copy, os
from pathlib import Path
from datetime import datetime

P = Path(__file__).resolve().parent
W = P.parent
R = W.parent
D = R / 'server-data/resources/cidade_mansao'
sys.path.insert(0, str(W / 'work/lua_syntax_deps'))
from luaparser import ast

spec = json.loads((P / 'spec.json').read_text())
verification = json.loads((P / 'verification.json').read_text())
original = json.loads((P / 'baseline_hashes.json').read_text())
assert verification['passed'] and verification['native_roundtrip']
assert verification['checks']['clear_exterior_stair_arrival']

def digest(data):
    return hashlib.sha256(data).hexdigest()

def current(path):
    return path.read_bytes() if path.exists() else None

def snapshot():
    return {f.relative_to(D).as_posix(): digest(f.read_bytes())
            for f in D.rglob('*') if f.is_file()}

baseline = snapshot()
targets = {}
for name, expected_hash in verification['files'].items():
    data = (P / 'stream' / name).read_bytes()
    assert digest(data) == expected_hash, ('Staged asset changed after validation', name)
    path = D / 'stream' / name
    before = current(path)
    key = path.relative_to(D).as_posix()
    if before != data:
        assert (before is None and key not in original) or (
            before is not None and digest(before) == original.get(key)), ('Native asset changed concurrently', key)
    targets[path] = (before, data)

gate_config = {
    'version': 1, 'origin': spec['origin'], 'gate_model': spec['models'][3],
    'gate_hinge': spec['gate_hinge'], 'interaction': [9.6, 9.44, -3.0],
    'floor_z': spec['garage_floor'], 'ceiling_z': spec['garage_ceiling'],
    'parking_spaces': spec['garage_spaces'], 'interaction_key': 'E',
}
for name in ['garagem_client.lua', 'garagem_server.lua']:
    data = (P / name).read_bytes()
    ast.parse(data.decode('utf-8'))
    path = D / name
    before = current(path)
    assert before is None or before == data, ('Conflicting garage script', name)
    targets[path] = (before, data)
path = D / 'garagem_acesso.json'
data = (json.dumps(gate_config, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
assert current(path) is None or current(path) == data
targets[path] = (current(path), data)

manifest_path = D / 'fxmanifest.lua'
manifest_before = manifest_path.read_bytes()
manifest = manifest_before.decode('utf-8')
newline = '\r\n' if '\r\n' in manifest else '\n'
registration = "data_file 'DLC_ITYP_REQUEST' 'stream/mansao_acesso_garagem.ytyp'"
if registration not in manifest:
    block = ["-- Main entry and underground garage, using regular map entities.",
             "files { 'stream/mansao_acesso_garagem.ytyp', 'garagem_acesso.json' }",
             registration, "client_script 'garagem_client.lua'", "server_script 'garagem_server.lua'"]
    manifest = manifest.rstrip('\r\n') + newline * 2 + newline.join(block) + newline
assert all(line in manifest for line in [registration,
    "client_script 'garagem_client.lua'", "server_script 'garagem_server.lua'"])
ast.parse(manifest)
targets[manifest_path] = (manifest_before, manifest.encode('utf-8'))

cfg_path = D / 'portas_madeira.json'
cfg_before = cfg_path.read_bytes()
old = json.loads(cfg_before)
cfg = copy.deepcopy(old)
assert cfg['origin'] == spec['origin']
existing = next((d for d in cfg['doors'] if d['model'] == spec['models'][2]), None)
if existing is None:
    ident = len(cfg['doors']) + 1
    assert [d['id'] for d in cfg['doors']] == list(range(1, ident))
    cfg['doors'].append({
        'id': ident, 'name': 'Entrada principal', 'model': spec['models'][2],
        'hinge': spec['door_hinge'], 'closed_heading': 0, 'open_heading': -90,
        'width_m': spec['door_width'], 'height_m': spec['door_height'],
        'leaf_thickness_m': .058, 'opening_center': [4.645, 7.45, .68],
        'opening_bounds': [3.90, 5.43, 7.19, 7.71, -.8, 2.27],
    })
    cfg['prototypes'].append({'name': spec['models'][2], 'width_m': spec['door_width'],
        'height_m': spec['door_height'], 'thickness_m': .058})
else:
    assert existing['hinge'] == spec['door_hinge'] and existing['open_heading'] == -90
restored = copy.deepcopy(cfg)
restored['doors'] = old['doors']
restored['prototypes'] = old['prototypes']
assert restored == old
targets[cfg_path] = (cfg_before, (json.dumps(cfg, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))

cat_path = D / 'objetos_catalogo.json'
cat_before = cat_path.read_bytes()
oldcat = json.loads(cat_before)
cat = copy.deepcopy(oldcat)
for name in spec['models']:
    if name not in cat['protectedModels']:
        cat['protectedModels'].append(name)
restored = copy.deepcopy(cat)
restored['protectedModels'] = oldcat['protectedModels']
assert restored == oldcat
targets[cat_path] = (cat_before, (json.dumps(cat, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))

for name in ['portas_client.lua', 'portas_server.lua']:
    ast.parse((D / name).read_text(encoding='utf-8'))
for path, (before, data) in targets.items():
    assert current(path) == before, ('Concurrent update during preflight', path)
print('GARAGE_INSTALL_PREFLIGHT_OK', len(targets), 'files', flush=True)
if '--check' in sys.argv:
    sys.exit(0)

backup = P / 'backup_preinstall' / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
backup.mkdir(parents=True)
for path, (before, data) in targets.items():
    if before is not None:
        q = backup / path.relative_to(D)
        q.parent.mkdir(parents=True, exist_ok=True)
        q.write_bytes(before)

installed = []
for path, (before, data) in targets.items():
    assert current(path) == before, ('Concurrent update before write', path)
    if before != data:
        temp = path.with_name(path.name + '.garage.tmp')
        try:
            temp.write_bytes(data)
            assert current(path) == before
            os.replace(temp, path)
        finally:
            if temp.exists():
                temp.unlink()
    assert path.read_bytes() == data
    installed.append(path.relative_to(D).as_posix())

after = snapshot()
target_names = set(installed)
unrelated_changes = [name for name, h in baseline.items()
                    if name not in target_names and after.get(name) != h]
assert not unrelated_changes, ('Unrelated changes during install', unrelated_changes)
assert json.loads(cfg_path.read_bytes()) == cfg
assert json.loads(cat_path.read_bytes()) == cat
assert json.loads((D / 'garagem_acesso.json').read_bytes()) == gate_config
report = {
    'installed_files': {name: after[name] for name in installed}, 'backup': str(backup),
    'unrelated_files_unchanged': len(baseline) - len(target_names.intersection(baseline)),
    'saved_positions_unchanged': after.get('objetos_posicoes.json') == baseline.get('objetos_posicoes.json'),
    'previous_door_entries_preserved': True, 'catalog_object_positions_preserved': True,
    'existing_internal_stair_and_floor_unchanged': all(after.get('stream/' + n + '.ydr') ==
        baseline.get('stream/' + n + '.ydr') for n in ['mansao_escada', 'mansao_pisos']),
    'general_illumination_files_unchanged': all(after.get(n) == baseline.get(n) for n in [
        'iluminacao_decorativa.lua', 'iluminacao_ambiente.json', 'luzes_pendentes.lua',
        'luzes_pendentes.json', 'stream/mansao_teto.ydr', 'stream/mansao_pendentes.ydr']),
    'requires_resource_reload': True, 'in_game_verified': False,
    'installed_at': datetime.now().astimezone().isoformat(),
}
(P / 'installation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
assert report['existing_internal_stair_and_floor_unchanged']
assert report['general_illumination_files_unchanged']
print('GARAGE_INSTALLED', len(installed), 'files; untouched', report['unrelated_files_unchanged'], 'files', flush=True)
