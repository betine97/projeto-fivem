exec((__import__('pathlib').Path(__file__).parent/'inspect_lights.py').read_text().split('for n in')[0])
import pymateria.gta5 as pm
from szio.gta5 import jenkhash
for name in ['default','normal_spec','emissive']:print(name,hex(pm.HashString(name).hash))
for path in [P/'v_res_fa_lamp1on.ydr',D/'stream/mansao_spot_embutido.ydr',D/'stream/mansao_pendentes.ydr']:
    d=g8.Drawable.import_rsc(path).result
    print(path.name,[(hex(s.basis_shader.hash),s.basis_material.string_or_placeholder,hex(s.basis_material.hash)) for s in d.shader_group.shaders])
    a=try_load_asset(path)
    for lod,ms in a.models.items():
        if lod.name!='HIGH':continue
        for m in ms:
            for g in m.geometries:
                if a.shader_group.shaders[g.shader_index].preset_filename=='emissive.sps':
                    print('emission',g.shader_index,[(k,g.vertex_buffer[k].min(0).tolist(),g.vertex_buffer[k].max(0).tolist()) for k in g.vertex_buffer.dtype.names if 'Colour' in k or 'Color' in k])
