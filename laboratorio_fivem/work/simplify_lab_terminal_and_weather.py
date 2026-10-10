"""Remove the chair, use native GTA puddles, and seal the lab from rain."""
import copy
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import AssetFormat, AssetTarget, AssetVersion, save_asset, try_load_asset
from szio.gta5.entities import Entity, EntityFlags, EntityLodLevel, EntityPriorityLevel
from szio.types import Quaternion, Vector

root = Path(__file__).resolve().parents[2]
lab = root / 'laboratorio_fivem'
stream = root / 'server-data/resources/cidade_laboratorio/stream'
native = lab / 'work/native_water_inspect'
out = lab / 'terminal_weather_fix'
out.mkdir(exist_ok=True)
target = (AssetTarget(AssetFormat.NATIVE, AssetVersion.GEN8),)

placement = json.loads((lab / 'placement.json').read_text())
origin = np.asarray(placement['origin'])
basis = np.asarray(placement['basis'])
heading = math.radians(placement['heading'])


def world_entity(name, loc, theta=0.0, scale=1.0, draw_distance=100):
    angle = -(heading + theta) / 2
    position = Vector(origin + basis @ np.asarray(loc))
    rotation = Quaternion((math.cos(angle), 0, 0, math.sin(angle)))
    return Entity(name, position, rotation, scale, scale,
                  EntityFlags.IS_STATIC, 0, -1, draw_distance, 0,
                  EntityLodLevel.ORPHANHD, EntityPriorityLevel.REQUIRED,
                  0, 255, 255, 0, [])


def bounds(drawable):
    xyz = np.concatenate([geom.vertex_buffer['Position']
                          for models in drawable.models.values()
                          for model in models for geom in model.geometries])
    return xyz.min(0), xyz.max(0)


ymap = try_load_asset(stream / 'cidade_laboratorio.ymap')
previous_count = len(ymap.entities)
assert sum(entity.archetype_name == 'prop_off_chair_04b'
           for entity in ymap.entities) <= 1
ymap.entities = [entity for entity in ymap.entities
                 if entity.archetype_name not in
                 {'prop_off_chair_04b', 'lab_pocas', 'lab_chuva'}]
assert len(ymap.entities) in (previous_count - 1, previous_count - 6)

# This drawable and all three of its embedded textures come directly from GTA V.
puddle = try_load_asset(native / 'po1_02_puddle.ydr')
puddle.name = 'lab_pocas.#dr'
save_asset(puddle, target, out, 'lab_pocas')
patches = [(-.75, -3.82, .066, .15), (.87, -1.81, .053, 1.1),
           (-.72, .20, .066, 2.2), (.75, 2.33, .058, .8),
           (-.39, 4.00, .045, 1.7)]
for x, y, scale, theta in patches:
    ymap.entities.append(world_entity('lab_pocas', [x, y, .045], theta, scale, 90))

# GTA's rain-blocking drawable uses a very faint cutout material. Reuse its
# native shader and embedded texture on two sealed roof panels. The authored
# ceiling and collision below them already cover both areas physically.
rain = try_load_asset(native / 'dt1_03_rain_blocker.ydr')
rain.name = 'lab_chuva.#dr'
geometry = rain.models[0][0].geometries[0]
vertices = np.zeros(8, dtype=geometry.vertex_buffer.dtype)
panels = [(-4.32, -6.32, 4.32, 6.32, 3.82),
          (-4.02, -8.32, 1.92, -5.87, 3.54)]
for index, (left, front, right, rear, z) in enumerate(panels):
    offset = index * 4
    vertices['Position'][offset:offset+4] = [
        (left, front, z), (right, front, z),
        (right, rear, z), (left, rear, z)]
    vertices['Normal'][offset:offset+4] = (0, 0, 1)
    vertices['Colour0'][offset:offset+4] = (255, 255, 255, 255)
    vertices['TexCoord0'][offset:offset+4] = (.5, .5)
geometry.vertex_buffer = vertices
geometry.index_buffer = np.asarray([0, 1, 2, 0, 2, 3,
                                    4, 5, 6, 4, 6, 7], dtype=np.uint16)
save_asset(rain, target, out, 'lab_chuva')
ymap.entities.append(world_entity('lab_chuva', [0, 0, 0], 0, 1, 120))

typ = try_load_asset(stream / 'cidade_laboratorio.ytyp')
template = next(item for item in typ.archetypes if item.name == 'lab_piso')
for name, asset in [('lab_pocas', puddle), ('lab_chuva', rain)]:
    archetype = copy.deepcopy(template)
    archetype.name = name
    archetype.asset_name = name
    low, high = bounds(asset)
    archetype.bb_min = Vector(low)
    archetype.bb_max = Vector(high)
    archetype.bs_center = Vector((low + high) / 2)
    archetype.bs_radius = float(np.linalg.norm(high - low) / 2)
    typ.archetypes = [item for item in typ.archetypes if item.name != name]
    typ.archetypes.append(archetype)
save_asset(typ, target, out, 'cidade_laboratorio')
save_asset(ymap, target, out, 'cidade_laboratorio')

# The old floor had synthetic water meshes. The backup is the original floor
# before those were added; copying it avoids z-fighting and duplicate puddles.
floor = lab / 'backup_before_atmosphere_fix/lab_piso.ydr'
assert floor.is_file()
(out / 'lab_piso.ydr').write_bytes(floor.read_bytes())

for filename in ('lab_pocas.ydr', 'lab_chuva.ydr', 'cidade_laboratorio.ymap',
                 'cidade_laboratorio.ytyp', 'lab_piso.ydr'):
    assert try_load_asset(out / filename) is not None, filename
check_map = try_load_asset(out / 'cidade_laboratorio.ymap')
names = [entity.archetype_name for entity in check_map.entities]
assert names.count('prop_off_chair_04b') == 0
assert names.count('lab_pocas') == 5
assert names.count('lab_chuva') == 1
print('TERMINAL_WEATHER_OK', len(names), 'entities', len(panels),
      'rain panels', names.count('lab_pocas'), 'native puddles', flush=True)
