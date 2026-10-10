"""Move the same encroaching landscape instances in base/APA/HEI map variants."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';OUT=W/'fivem';N=W/'work/native'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
from szio.types import Vector
origin=np.array(json.loads((W/'medidas_estudo.json').read_text())['native_origin']);changes=[]
targets=[('long_0','prop_bush_med_03',[-5.255,10.664,-1.079],1.5),('strm_0','prop_plant_cane_02a',[-3.161,11.728,-.570],1.2),('strm_1','prop_pot_plant_02d',[7.171,8.239,-.394],.4)]
for prefix in ('','apa_','hei_'):
 for suffix,name,where,shift in targets:
  f=N/(prefix+'ch2_09b_'+suffix+'.ymap');a=try_load_asset(f);old=[e for e in a.entities if str(e.archetype_name)==name and np.linalg.norm(np.array(e.position)-origin-where)<.01];assert len(old)==1
  e=old[0];before=list(e.position);e.position=Vector(np.array(e.position)+[0,shift,0])
  save_asset(a,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),OUT,f.stem)
  reloaded=try_load_asset(OUT/f.name);assert len(reloaded.entities)==len(a.entities)
  changes.append(dict(map=f.name,name=name,old=before,new=list(e.position),shift_y_m=shift))
(W/'correcao_plantas_camadas.json').write_text(json.dumps(changes,indent=2));print('LANDSCAPE_LAYERS_FIXED',len(changes),flush=True)
