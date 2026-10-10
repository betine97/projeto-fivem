"""Install only this fixed wall cabinet, preserving current shared metadata."""
import copy
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

P = Path(__file__).resolve().parent
R = P.parent.parent
D = R / 'server-data/resources/cidade_mansao'
sys.path.insert(0, str(R / 'casa_vinewood/work/lua_syntax_deps'))
from luaparser import ast

def digest(data):
    return hashlib.sha256(data).hexdigest()

def current(path):
    return path.read_bytes() if path.exists() else None

verified = json.loads((P / 'verification.json').read_text(encoding='utf-8'))
spec = json.loads((P / 'spec.json').read_text(encoding='utf-8'))
assert verified['passed'] and verified['native_roundtrip']
assets = verified['files']
assert set(assets) == {spec['model'] + suffix for suffix in ['.ydr', '.ytyp', '.ymap', '.ybn']}
for name, expected in assets.items():
    assert digest((P / 'stream' / name).read_bytes()) == expected, name
    live = current(D / 'stream' / name)
    assert live is None or digest(live) == expected, f'Unexpected existing native asset: {name}'

manifest_path = D / 'fxmanifest.lua'
manifest_before = manifest_path.read_bytes()
manifest = manifest_before.decode('utf-8')
newline = '\r\n' if '\r\n' in manifest else '\n'
additions = []
registration = "data_file 'DLC_ITYP_REQUEST' 'stream/mansao_adega_vitrines.ytyp'"
if registration not in manifest:
    additions.extend(["files { 'stream/mansao_adega_vitrines.ytyp' }", registration])
if "client_script 'adega_vitrines_luzes.lua'" not in manifest:
    additions.append("client_script 'adega_vitrines_luzes.lua'")
if additions:
    manifest = manifest.rstrip('\r\n') + newline * 2 + newline.join(additions) + newline
ast.parse(manifest)
light_path = D / 'adega_vitrines_luzes.lua'
light_before = current(light_path)
light_bytes = (P / 'adega_vitrines_luzes.lua').read_bytes()
ast.parse(light_bytes.decode('utf-8'))
assert light_before is None or light_before == light_bytes

catalog_path = D / 'objetos_catalogo.json'
catalog_before = catalog_path.read_bytes()
old_catalog = json.loads(catalog_before)
new_catalog = copy.deepcopy(old_catalog)
if spec['model'] not in new_catalog['protectedModels']:
    new_catalog['protectedModels'].append(spec['model'])
restored = copy.deepcopy(new_catalog)
restored['protectedModels'] = old_catalog['protectedModels']
assert restored == old_catalog
catalog_after = (json.dumps(new_catalog, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
positions_path = D / 'objetos_posicoes.json'
positions_before = current(positions_path)

backup = P / 'backup_preinstall' / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
backup.mkdir(parents=True)
report = {'installed_files': {}, 'backups': str(backup), 'in_game_verified': False,
          'requires_resource_reload': True}

def install_bytes(path, data, expected_before):
    assert current(path) == expected_before, f'Concurrent change: {path.name}'
    if expected_before == data:
        report['installed_files'][str(path.relative_to(D))] = digest(data)
        return
    if expected_before is not None:
        dest = backup / path.relative_to(D)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(expected_before)
    temp = path.with_name(path.name + '.adega-install.tmp')
    try:
        temp.write_bytes(data)
        assert current(path) == expected_before, f'Concurrent change: {path.name}'
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()
    assert path.read_bytes() == data
    report['installed_files'][str(path.relative_to(D))] = digest(data)

native_before = {name: current(D / 'stream' / name) for name in assets}
assert current(manifest_path) == manifest_before and current(catalog_path) == catalog_before
for name in assets:
    install_bytes(D / 'stream' / name, (P / 'stream' / name).read_bytes(), native_before[name])
install_bytes(light_path, light_bytes, light_before)
install_bytes(catalog_path, catalog_after, catalog_before)
install_bytes(manifest_path, manifest.encode('utf-8'), manifest_before)

for name, expected in assets.items():
    assert digest((D / 'stream' / name).read_bytes()) == expected
assert json.loads(catalog_path.read_bytes()) == new_catalog
assert manifest_path.read_bytes() == manifest.encode('utf-8')
report['catalog_object_ids_poses_scales_preserved'] = True
report['saved_positions_file_not_written'] = True
report['saved_positions_unchanged_during_install'] = current(positions_path) == positions_before
report['fixed_cabinet_protected_from_prop_editor'] = True
report['native_hashes_match_validation'] = True
report['shared_manifest_previous_entries_preserved'] = True
report['installed_at'] = datetime.now().astimezone().isoformat()
(P / 'installation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('INSTALLED', len(assets), 'native assets + local lights; existing resource metadata preserved', flush=True)
