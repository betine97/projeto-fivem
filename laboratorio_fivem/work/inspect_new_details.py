import sys
from pathlib import Path

sys.path.insert(0, r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset
from szio.gta5.drawables import LodLevel

stream = Path(__file__).resolve().parents[2] / 'server-data/resources/cidade_laboratorio/stream'
for name in ('lab_racks', 'lab_ventilacao', 'lab_piso', 'lab_leds', 'lab_planta_00'):
    a = try_load_asset(stream / (name + '.ydr'))
    print('\nASSET', name, 'shaders', len(a.shader_group.shaders), 'textures', list(a.shader_group.embedded_textures))
    for i, sh in enumerate(a.shader_group.shaders):
        print('SHADER', i, getattr(sh, 'name', ''), getattr(sh, 'filename', ''), [(p.name, str(getattr(p, 'value', None))[:55]) for p in sh.parameters])
    for mi, m in enumerate(a.models[LodLevel.HIGH]):
        for gi, g in enumerate(m.geometries):
            p = g.vertex_buffer['Position']
            print('GEOM', mi, gi, 'shader', g.shader_index, 'verts', len(p), 'tri', len(g.index_buffer)//3, 'bbox', p.min(0).round(2).tolist(), p.max(0).round(2).tolist(), 'dtype', g.vertex_buffer.dtype.names)
