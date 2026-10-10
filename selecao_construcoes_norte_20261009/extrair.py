"""Read stock GTA assets into this isolated preview folder; never edit the game."""
import json, sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
sys.path[:0] = [str(ROOT/'laboratorio_fivem/work/pydeps'), r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.rpf import open_rpf
from szio.vfs import VPath
from szio.gta5 import try_load_asset

GAME = Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V')
NATIVE = OUT/'native'; NATIVE.mkdir(exist_ok=True)
TEXTURES = OUT/'textures'; TEXTURES.mkdir(exist_ok=True)
names = ['cs1_05_house_01', 'cs1_05_house_02', 'cs1_05_house_03', 'cs1_05_house_04',
         'cs2_01_deshous1', 'cs2_01_deshous4', 'cs2_01_deshous_2', 'cs2_01_house5',
         'cs4_04_desert_house', 'cs4_06_smallhouse', 'cs3_04_house01', 'cs3_04_house02']
lines = (ROOT/'laboratorio_fivem/work/assets_index.txt').read_text().splitlines()
cache = {}
def archive(parts):
    key = '|'.join(parts[:-1])
    if key not in cache:
        r = open_rpf(GAME/parts[0])
        for sub in parts[1:-1]: r = r.open_nested(sub)
        cache[key] = r
    return cache[key]

rows, required, regions = {}, set(), set()
for name in names:
    line = next(s for s in lines if s.endswith('|'+name+'.ydr'))
    parts = line.split('|'); target = NATIVE/(name+'.ydr')
    target.write_bytes(archive(parts).read_bytes(parts[-1]))
    asset = try_load_asset(target)
    diffuse = set()
    for shader in asset.shader_group.shaders:
        for param in shader.parameters:
            if 'diffuse' in str(param.name).lower() and isinstance(param.value, str):
                diffuse.add(param.value)
    required.update(diffuse)
    regions.add('|'.join(parts[:-1]))
    embedded = asset.shader_group.embedded_textures
    if embedded:
        for n, tex in embedded.items():
            if str(n).lower() in {v.lower() for v in required}:
                (TEXTURES/(str(n)+'.dds')).write_bytes(tex.data.read_bytes())
    rows[name] = dict(model=name, source=line, diffuse_textures=sorted(diffuse), placements=[],
                      native_parts=1, collision_verified=False, in_game_verified=False)
    print('MODEL', name, len(diffuse), flush=True)

# Original positions and archetype metadata establish provenance and dependencies.
prefixes = {name[:6] for name in names}
for line in lines:
    parts = line.split('|'); stem = Path(parts[-1]).stem
    if line.endswith('.ymap') and any(stem.startswith(prefix) for prefix in prefixes):
        a = try_load_asset(VPath(GAME, line.replace('|','/')))
        for entity in a.entities:
            name = str(entity.archetype_name)
            if name in rows:
                rows[name]['placements'].append(dict(map=parts[-1], position=list(entity.position), rotation=list(entity.rotation)))

# Export only texture images referenced by candidates, from their original archives.
pending = {name.lower() for name in required}
pending -= {p.stem.lower() for p in TEXTURES.glob('*.dds')}
for region in sorted(regions):
    parent = VPath(GAME, region.replace('|','/'))
    paths = sorted((p for p in parent.iterdir() if p.suffix.lower()=='.ytd'), key=lambda p: ('+hi' not in p.name, p.name))
    for p in paths:
        if not pending: break
        try:
            td = try_load_asset(p)
            for name, tex in td.textures.items():
                name = str(name)
                if name.lower() in pending:
                    (TEXTURES/(name+'.dds')).write_bytes(tex.data.read_bytes())
                    pending.remove(name.lower())
        except Exception as ex:
            print('TEXTURE_READ_ERROR', p.name, str(ex)[:120], flush=True)
    print('TEXTURES_PENDING', region.split('|')[-1], len(pending), flush=True)

for row in rows.values():
    row['missing_diffuse'] = [name for name in row['diffuse_textures'] if name.lower() in pending]
(OUT/'candidatos.json').write_text(json.dumps(list(rows.values()), indent=2), encoding='utf-8')
print('CANDIDATES_EXTRACTED', len(rows), 'missing_textures', len(pending), flush=True)
