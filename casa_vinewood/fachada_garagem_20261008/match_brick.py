import sys,json,collections
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
a=try_load_asset(P/'baseline/stream/ch2_09b_hs05.ydr')
for name in ['os_ml_idwall_0005_c','os_ml_idwall_0005_n']:
    (P/'textures'/(name+'.dds')).write_bytes(a.shader_group.embedded_textures[name].data.read_bytes())
info=[]
for m in a.models[LodLevel.HIGH]:
    for g in m.geometries:
        if g.shader_index!=12:continue
        for ids in g.index_buffer.reshape(-1,3):
            v=g.vertex_buffer['Position'][ids]
            if v[:,1].min()<5.7 or v[:,0].min()>3.7:continue
            info.append({'lo':v.min(0).tolist(),'hi':v.max(0).tolist(),'p':v.tolist(),'uv':g.vertex_buffer['TexCoord0'][ids].tolist()})
(P/'native_brick_faces.json').write_text(json.dumps(info,indent=2))
print('NATIVE_BRICK_NEAR_ENTRY',[(q['lo'],q['hi']) for q in info],flush=True)
