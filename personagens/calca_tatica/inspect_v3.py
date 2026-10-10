import sys
from pathlib import Path
sys.path.insert(0,str(Path('personagens/catalogo_nativo').resolve()))
import render_catalog as r
from dataclasses import fields
x=r.try_load_asset(r.ROOT/'personagens/calca_tatica/source/lowr_001_r.ydd');d=next(iter(x.drawables.values()))
for m in d.models[0]:
 for g in m.geometries:
  v=g.vertex_buffer;p=v['Position'];n=v['Normal'];uv=v['TexCoord0'];print('dtype',v.dtype,'boneids',g.bone_ids)
  for sign in (-1,1):
   mask=(r.np.sign(p[:,0])==sign)&(p[:,2]<-.55)&(p[:,2]>-.85)&(n[:,1]<-.4)&(sign*n[:,0]>.25)
   print('frontside',sign,uv[mask].min(0),uv[mask].max(0))
print('staticfiles',list((r.ROOT/'server-data/resources/cidade_laboratorio/stream').glob('*.ydr'))[:3])
