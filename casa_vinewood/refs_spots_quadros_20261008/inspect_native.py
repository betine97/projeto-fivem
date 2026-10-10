import sys,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.gta5 import *
def diff(shader):
    return [(p.name,p.value) for p in shader.parameters if isinstance(p.value,str)]
for name in ['ref_spot_48','mansao_quadro_ref_2','mansao_pisos','mansao_teto','mansao_spots_led']:
    a=try_load_asset(P/'stream'/(name+'.ydr'))
    print(name, 'MODELS', [(int(l),len(m),sum(len(g.index_buffer)//3 for x in m for g in x.geometries)) for l,m in a.models.items()])
    print('SHADERS',[(s.preset_filename,diff(s)) for s in a.shader_group.shaders])
    if name=='ref_spot_48':print('SPOT_PARAMETERS',[(s.preset_filename,[(p.name,str(p.value)) for p in s.parameters if not isinstance(p.value,str)]) for s in a.shader_group.shaders])
    print('TEXTURES',[(k,t.width,t.height,len(t.data.read_bytes())) for k,t in a.shader_group.embedded_textures.items()])
    if name in ['mansao_pisos','mansao_teto']:
        a=try_load_asset(R/'server-data/resources/cidade_mansao/stream'/(name+'.ydr'))
        print('BASE_SHADERS',[(s.preset_filename,diff(s)) for s in a.shader_group.shaders])
        print('BASE_BOUND',type(a.bounds).__name__)
print('CURRENT_RESOURCE_FILES',len([p for p in (R/'server-data/resources/cidade_mansao').rglob('*') if p.is_file()]))
