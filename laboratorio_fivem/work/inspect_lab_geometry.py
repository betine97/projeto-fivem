import sys,numpy as np
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset
src=Path(__file__).resolve().parents[2]/'server-data/resources/cidade_laboratorio/stream'
for name in ('lab_equipamentos','lab_ventilacao'):
 a=try_load_asset(src/(name+'.ydr'))
 print('\n',name,'shaders',len(a.shader_group.shaders),flush=True)
 print('lods',list(a.models),flush=True)
 for lod,models in a.models.items():
  for m in models:
   for i,g in enumerate(m.geometries):
    key=next(k for k in g.vertex_buffer.dtype.names if k.lower()=='position')
    p=g.vertex_buffer[key];lo=p.min(0);hi=p.max(0)
    if name=='lab_equipamentos':
     t=g.index_buffer.reshape(-1,3);v=p[t];inside=np.all((v[:,:,0]>=1)&(v[:,:,0]<=2)&(v[:,:,1]>=5)&(v[:,:,1]<=5.5)&(v[:,:,2]>.995),axis=1)
     if inside.any():print(lod,i,'shader',g.shader_index,'triangles',len(t),'top-box-triangles',inside.sum(),'bbox',lo.tolist(),hi.tolist(),flush=True)
    else:print(lod,i,'shader',g.shader_index,'triangles',len(g.index_buffer)//3,'bbox',np.round(lo,2).tolist(),np.round(hi,2).tolist(),flush=True)
