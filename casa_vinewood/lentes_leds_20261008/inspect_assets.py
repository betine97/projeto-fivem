import sys,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
import pymateria.gta5.gen8 as g8
import pymateria.gta5 as pm
from szio.gta5 import try_load_asset
out={}
for name in ['mansao_spot_embutido','mansao_pendentes','mansao_spots_led','mansao_tv']:
 a=g8.Drawable.import_rsc(D/'stream'/(name+'.ydr')).result
 b=try_load_asset(D/'stream'/(name+'.ydr'))
 rows=[]
 for lod,v in a.lods.items():
  for mi,m in enumerate(v.models):
   for gi,g in enumerate(m.geometries):
    vb=g.vb.buffer;pos=vb['POSITION']
    rows.append(dict(lod=str(lod),threshold=v.lod_threshold,mi=mi,gi=gi,shader=next(i for i,s in enumerate(a.shader_group.shaders) if s==g.shader),vertices=len(pos),tris=len(g.ib.indices)//3,min=pos.min(axis=0).tolist(),max=pos.max(axis=0).tolist(),channels=list(vb.dtype.names)))
 out[name]=dict(rows=rows,shaders=[dict(index=i,name=str(s.name),preset=s.preset_filename,params=[dict(name=p.name,value=str(p.value)) for p in s.parameters]) for i,s in enumerate(b.shader_group.shaders)],lights=len(a.lights))
 print(name,'lights',len(a.lights),'shaders',[(str(s.basis_shader),str(s.basis_material)) for s in a.shader_group.shaders])
 print(json.dumps(rows,indent=1))
(P/'audit.json').write_text(json.dumps(out,indent=2))
