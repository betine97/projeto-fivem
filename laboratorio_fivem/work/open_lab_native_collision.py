"""Retire the two native solid volumes covering the custom lab."""
import sys, json, numpy as np
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset,save_asset,AssetTarget,AssetFormat,AssetVersion
from szio.gta5.bounds import BoundPrimitiveType
from szio.types import Vector

w=Path(__file__).resolve().parent
p=json.loads((w.parent/'placement.json').read_text());origin=np.array(p['origin']);basis=np.array(p['basis'])
src=w/'base_assets/ch3_08_36.ybn';out=w.parent/'collision_fix';out.mkdir(exist_ok=True)
asset=try_load_asset(src)
cut_lo=np.array([-4.35,-8.50,-.30]);cut_hi=np.array([4.35,6.30,3.80])
changed=[]

def patch(b):
 for child in getattr(b,'children',[]):patch(child)
 if not hasattr(b,'geometry_primitives'):return
 tx=np.array(b.composite_transform);kept=[]
 for i,t in enumerate(b.geometry_primitives):
  if t.primitive_type!=BoundPrimitiveType.BOX or i not in (337,550):kept.append(t);continue
  q=np.array([list(b.geometry_vertices[j].co)+[1] for j in t.vertices])@tx
  local=(q[:,:3]-origin)@basis;lo=local.min(0);hi=local.max(0)
  if not (np.all(hi>cut_lo) and np.all(lo<cut_hi)):kept.append(t);continue
  changed.append({'primitive_index':i,'original_min':lo.tolist(),'original_max':hi.tolist()})
 b.geometry_primitives=kept
patch(asset)
assert {x['primitive_index'] for x in changed}=={337,550},changed
save_asset(asset,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),out,src.stem)
check=try_load_asset(out/src.name);assert check is not None
report={'source':src.name,'clear_min':cut_lo.tolist(),'clear_max':cut_hi.tolist(),'changed':changed,'roundtrip_valid':True}
(w.parent/'validacao_colisao_nativa.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
