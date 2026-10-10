"""Install only the reference-wall assets and the 150% bear rug.

Read shared metadata immediately before changing it. Never restore a stale
manifest/catalog or touch the user's saved furniture positions.
"""
import copy
import hashlib
import json
import os
import shutil
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
assert verified['passed'] and verified['bear_geometry_factor'] == 1.5
assets = verified['files']
for name, expected in assets.items():
    assert digest((P / 'stream' / name).read_bytes()) == expected, name

# Abort before mutation if another task has changed either shared native file.
for name in ['mansao_tapete_urso.ydr', 'mansao_piano_tapetes.ytyp']:
    old = (P / 'backup_antes' / name).read_bytes()
    live = (D / 'stream' / name).read_bytes()
    assert digest(live) in (digest(old), assets[name]), f'Concurrent native change: {name}'
for name, expected in assets.items():
    if name.startswith('mansao_bar_referencia') and (D / 'stream' / name).exists():
        assert digest((D / 'stream' / name).read_bytes()) == expected, name

backup = P / 'backup_preinstall' / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
backup.mkdir(parents=True)
report = {'installed_files': {}, 'backups': str(backup), 'in_game_verified': False,
          'requires_resource_reload': True, 'bear_geometry_factor': 1.5}


def install_bytes(path, data, expected_before):
    before = current(path)
    assert before == expected_before, f'Concurrent change: {path.name}'
    if before == data:
        report['installed_files'][str(path.relative_to(D))] = digest(data)
        return
    if before is not None:
        dest = backup / path.relative_to(D)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(before)
    temp = path.with_name(path.name + '.bar-install.tmp')
    try:
        temp.write_bytes(data)
        assert current(path) == expected_before, f'Concurrent change: {path.name}'
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()
    assert path.read_bytes() == data
    report['installed_files'][str(path.relative_to(D))] = digest(data)


# Prepare and validate all metadata before installing native files.
manifest_path = D / 'fxmanifest.lua'
manifest_before = manifest_path.read_bytes()
manifest = manifest_before.decode('utf-8')
newline = '\r\n' if '\r\n' in manifest else '\n'
additions = []
if "data_file 'DLC_ITYP_REQUEST' 'stream/mansao_bar_referencia.ytyp'" not in manifest:
    additions += ["files { 'stream/mansao_bar_referencia.ytyp' }",
                  "data_file 'DLC_ITYP_REQUEST' 'stream/mansao_bar_referencia.ytyp'"]
if "client_script 'bar_referencia_luzes.lua'" not in manifest:
    additions += ["client_script 'bar_referencia_luzes.lua'"]
if additions:
    manifest = manifest.rstrip('\r\n') + newline * 2 + newline.join(additions) + newline
ast.parse(manifest)
light_path = D / 'bar_referencia_luzes.lua'
light_before = current(light_path)
light_bytes = (P / 'bar_referencia_luzes.lua').read_bytes()
ast.parse(light_bytes.decode('utf-8'))
if light_before is not None:
    assert light_before == light_bytes, 'Unexpected existing bar light script'

catalog_path = D / 'objetos_catalogo.json'
catalog_before = catalog_path.read_bytes()
old_catalog = json.loads(catalog_before)
new_catalog = copy.deepcopy(old_catalog)
bear = [o for o in new_catalog['objects'] if o['model'] == 'mansao_tapete_urso']
assert len(bear) == 1
bear[0]['lo'] = spec['bear_resize']['lo']
bear[0]['hi'] = spec['bear_resize']['hi']
if spec['model'] not in new_catalog['protectedModels']:
    new_catalog['protectedModels'].append(spec['model'])

# Object IDs, poses, rotation, scales and unrelated selection bounds are exact.
restored = copy.deepcopy(new_catalog)
old_bear = next(o for o in old_catalog['objects'] if o['model'] == 'mansao_tapete_urso')
restored_bear = next(o for o in restored['objects'] if o['model'] == 'mansao_tapete_urso')
restored_bear['lo'], restored_bear['hi'] = old_bear['lo'], old_bear['hi']
restored['protectedModels'] = old_catalog['protectedModels']
assert restored == old_catalog
catalog_after = (json.dumps(new_catalog, indent=2, ensure_ascii=False) + '\n').encode('utf-8')

# Capture only this task's target files, not a stale complete resource snapshot.
native_before = {name: current(D / 'stream' / name) for name in assets}
assert current(manifest_path) == manifest_before
assert current(catalog_path) == catalog_before
for name in assets:
    install_bytes(D / 'stream' / name, (P / 'stream' / name).read_bytes(), native_before[name])
install_bytes(light_path, light_bytes, light_before)
install_bytes(catalog_path, catalog_after, catalog_before)
install_bytes(manifest_path, manifest.encode('utf-8'), manifest_before)

for name, expected in assets.items():
    assert digest((D / 'stream' / name).read_bytes()) == expected, name
live_catalog = json.loads(catalog_path.read_bytes())
assert live_catalog == new_catalog
assert manifest_path.read_bytes() == manifest.encode('utf-8')
report['catalog_object_ids_poses_scales_preserved'] = True
report['saved_positions_file_not_modified'] = True
report['new_bar_protected_from_prop_editor'] = True
report['native_hashes_match_validation'] = True
report['shared_manifest_previous_entries_preserved'] = True
report['installed_at'] = datetime.now().astimezone().isoformat()
(P / 'installation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('INSTALLED', len(assets), 'native files; rug 150%; catalog/manifest preserved', flush=True)
