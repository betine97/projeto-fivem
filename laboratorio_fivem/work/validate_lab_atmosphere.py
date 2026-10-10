import io
import sys
from pathlib import Path

import numpy as np

sys.path[:0] = [
    r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',
    r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\media_deps',
]
from PIL import Image
from szio.gta5 import try_load_asset
from szio.gta5.drawables import LodLevel

root = Path(__file__).resolve().parents[2]
folder = root / 'laboratorio_fivem/atmosphere_fix'
stream = root / 'laboratorio_fivem/backup_before_atmosphere_fix'

rack = try_load_asset(folder / 'lab_racks.ydr')
old_rack = try_load_asset(stream / 'lab_racks.ydr')
original = old_rack.models[LodLevel.HIGH][0].geometries[0]
assert len(rack.models[LodLevel.HIGH][0].geometries) == 2
assert np.array_equal(rack.models[LodLevel.HIGH][0].geometries[0].index_buffer, original.index_buffer)
assert np.array_equal(rack.models[LodLevel.HIGH][0].geometries[0].vertex_buffer['Position'], original.vertex_buffer['Position'])
net = rack.models[LodLevel.HIGH][0].geometries[1]
assert len(net.index_buffer) == 4608 * 3
net_pos = net.vertex_buffer['Position']
assert net_pos[:, 2].min() >= .29 and 2.95 <= net_pos[:, 2].max() <= 2.97
assert any(np.isclose(net_pos[:, 0], edge, atol=.03).any()
           for edge in (-3.56, -1.40, 1.40, 3.56))
texture = rack.shader_group.embedded_textures['lab_net_color']
alpha = np.asarray(Image.open(io.BytesIO(texture.data.read_bytes())))[:, :, 3]
assert alpha.min() == 0 and alpha.max() > 128

vent = try_load_asset(folder / 'lab_ventilacao.ydr')
assert len(vent.shader_group.shaders) == 10
foil = vent.models[LodLevel.HIGH][0].geometries[-1]
assert len(foil.index_buffer) == 11440 * 3
foil_pos = foil.vertex_buffer['Position']
assert foil_pos[:, 2].min() > 2.71 and foil_pos[:, 2].max() < 3.61

floor = try_load_asset(folder / 'lab_piso.ydr')
puddles = floor.models[LodLevel.HIGH][0].geometries[-1]
assert len(puddles.index_buffer) == 240 * 3
assert np.all(puddles.vertex_buffer['Position'][:, 2] >= .036)

led = try_load_asset(folder / 'lab_leds.ydr')
assert next(p.value[0] for p in led.shader_group.shaders[2].parameters
            if p.name.lower() == 'emissivemultiplier') >= 5

typ = try_load_asset(folder / 'cidade_laboratorio.ytyp')
arch = next(a for a in typ.archetypes if a.name == 'lab_racks')
assert arch.bb_max[2] >= 2.95

print('ATMOSPHERE_VALIDATED net=4608 foil=11440 puddles=5 leds=5.5', flush=True)
