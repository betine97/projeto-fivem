import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2]; W=R/'castelo_rockford'; N=W/'originais';N.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset
G=Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V'); cache={}; entities=[];bounds=[]
sources=[s for s in (R/'laboratorio_fivem/work/assets_index.txt').read_text().splitlines() if '/bh1_45.rpf|' in s or s.endswith(('bh1_45.ymap','bh1_45_long_0.ymap','bh1_45_strm_0.ymap','bh1_45_strm_1.ymap'))]
for s in sources:
 p=s.split('|');k='|'.join(p[:-1])
 if k not in cache:
  a=open_rpf(G/p[0])
  for sub in p[1:-1]:a=a.open_nested(sub)
  cache[k]=a
 f=N/Path(p[-1]).name;f.write_bytes(cache[k].read_bytes(p[-1]));a=try_load_asset(f)
 if f.suffix=='.ymap':
  for i,e in enumerate(a.entities):entities.append(dict(map=f.name,index=i,name=str(e.archetype_name),pos=list(e.position),rot=list(e.rotation),scale=[e.scale_xy,e.scale_xy,e.scale_z],parent=e.parent_index))
 if f.suffix=='.ydr':
  vs=[g.vertex_buffer['Position'] for ms in a.models.values() for m in ms for g in m.geometries]
  if vs:
   v=np.concatenate(vs);bounds.append(dict(name=f.stem,lo=v.min(0).tolist(),hi=v.max(0).tolist(),triangles=sum(len(g.index_buffer)//3 for ms in a.models.values() for m in ms for g in m.geometries),textures=sorted(set(str(p.value) for s in a.shader_group.shaders for p in s.parameters if p.name.lower()=='diffusesampler'))))
(W/'entities.json').write_text(json.dumps(entities,indent=2));(W/'bounds.json').write_text(json.dumps(bounds,indent=2));(W/'sources.json').write_text(json.dumps(sources,indent=2))
print('EXTRACTED',len(sources))
for e in entities:
 if e['name'].startswith('bh1_45') and not 'strm' in e['map']:print(e)
for b in bounds:
 if b['name'].endswith(('plot1_ter','plot4a_ter','plot4b_ter','plot3_tera','plot3_terb')):print(b)
