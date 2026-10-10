import sys,json
from pathlib import Path
sys.path=[p for p in sys.path if Path(p).resolve()!=Path(__file__).resolve().parent]
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',str(Path('laboratorio_fivem/work/pydeps').resolve())]
import numpy as np
from szio.gta5 import try_load_asset
root=Path(__file__).resolve().parents[1]
source=next(iter(try_load_asset(root.parent/'calca_bege/source/mp_m_freemode_01_male_apt01^feet_001_r.ydd').drawables.values()))
target=next(iter(try_load_asset(root/'sapatos/exports/feet_001_u.ydd').drawables.values()))
def geometries(drawable,models):
 indices={i for i,s in enumerate(drawable.shader_group.shaders) if any(p.name=='diffusesampler' and p.value=='feet_diff_001_a_whi' for p in s.parameters)}
 return [g for m in models for g in m.geometries if g.shader_index in indices]
source_high=next(v for k,v in source.models.items() if k.name=='HIGH')
original=geometries(source,source_high)
def positions(gs):return np.unique(np.concatenate([g.vertex_buffer['Position'] for g in gs]),axis=0)
expected=positions(original);triangles=sum(len(g.index_buffer)//3 for g in original);report={}
for lod,models in target.models.items():
 gs=geometries(target,models);actual=positions(gs);count=sum(len(g.index_buffer)//3 for g in gs)
 distances=np.linalg.norm(expected[:,None,:]-actual[None,:,:],axis=2)
 error=max(float(distances.min(0).max()),float(distances.min(1).max()))
 assert error<.000002,(lod.name,error)
 assert count==triangles,(lod.name,triangles,count)
 report[lod.name]={'native_foot_positions_unchanged':True,'unique_positions':len(actual),'triangles':count,'max_position_error_m':error}
(root/'work/complete_native_foot_verified.json').write_text(json.dumps(report,indent=2))
print('COMPLETE_FOOT_PRESERVED_IN_ALL_LODS',json.dumps(report),flush=True)
