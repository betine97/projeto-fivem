import sys,json,io
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from PIL import Image
from szio.gta5 import try_load_asset
D=R/'server-data/resources/cidade_mansao/stream'
for name in ['mansao_vidros','ch2_09b_hs05','ch2_09b_hs05_details','ch2_09b_emissive_05']:
 a=try_load_asset(D/(name+'.ydr'));print('ASSET',name)
 for i,s in enumerate(a.shader_group.shaders):
  print('SHADER',i,s.name,s.render_bucket,[(p.name,str(p.value)) for p in s.parameters] if name=='mansao_vidros' else [(p.name,str(p.value)) for p in s.parameters if p.name.lower()=='diffusesampler'])
 if name=='mansao_vidros':
  for name,t in a.shader_group.embedded_textures.items():
   im=Image.open(io.BytesIO(t.data.read_bytes())).convert('RGBA');px=np.array(im);print('TEXTURE',name,im.size,'RGBA',px.reshape(-1,4).min(0),px.reshape(-1,4).max(0))
  for models in a.models.values():
   for m in models:
    for g in m.geometries:print('GEOMETRY',g.shader_index,len(g.index_buffer)//3,g.vertex_buffer.dtype.names)
