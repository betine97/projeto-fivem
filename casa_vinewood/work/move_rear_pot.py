"""Keep a rear courtyard plant's foliage collision outside the fitted wall."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import try_load_asset,save_asset,AssetTarget,AssetFormat,AssetVersion
from szio.types import Vector
e=next(q for q in json.loads((W/'work/near_house_entities.json').read_text()) if q['name']=='prop_pot_plant_02d')
f=W/'work/native'/e['map'];a=try_load_asset(f)
matches=[q for q in a.entities if str(q.archetype_name)==e['name'] and np.linalg.norm(np.array(q.position)-e['pos'])<.01]
assert len(matches)==1
q=matches[0];old=list(q.position);q.position=Vector(np.array(old)+[0,.40,0])
save_asset(a,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),W/'fivem',f.stem)
(W/'alteracao_vaso_fundos.json').write_text(json.dumps({'file':f.name,'model':e['name'],'old':old,'new':list(q.position),'shift_m':.40,'reason':'Foliage bound crossed the continuous rear wall; shift only this courtyard instance outward.'},indent=2))
print('COURTYARD_POT_MOVED_OUTWARD',f.name,.40,flush=True)
