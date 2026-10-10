import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
from szio.types import Vector
origin=np.array(json.loads((W/'medidas_estudo.json').read_text())['native_origin']);changes=[]
for e in json.loads((W/'work/near_house_entities.json').read_text()):
 q=np.array(e['pos'])-origin
 if e['name']!='prop_bush_med_03' or not (-7<q[0]<-3 and 9<q[1]<12):continue
 f=W/'work/native'/e['map'];a=try_load_asset(f)
 found=[v for v in a.entities if str(v.archetype_name)==e['name'] and np.linalg.norm(np.array(v.position)-e['pos'])<.01];assert len(found)==1
 ent=found[0];old=list(ent.position);ent.position=Vector(np.array(old)+[0,1.50,0])
 save_asset(a,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),W/'fivem',f.stem)
 changes.append({'map':f.name,'name':e['name'],'old':old,'new':list(ent.position),'reason':'Plant collision protruded through rear wall into room; move this instance outward.'})
assert len(changes)==1
(W/'alteracao_vegetacao.json').write_text(json.dumps(changes,indent=2));print('MOVED_INTRUDING_PLANT',changes)
