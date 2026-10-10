import sys,json,shutil,numpy as np
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import *
from szio.types import Vector
W=Path(__file__).resolve().parents[1];src=W/'polido';dest=W.parent/'server-data/resources/cidade_laboratorio/stream';backup=W/'backup_pre_polido';backup.mkdir(exist_ok=True)
names=['lab_planta_%02d'%i for i in range(18)]
for n in names:assert (src/(n+'.ydr')).exists(),n
r=json.loads((W/'export_report_hd.json').read_text());y=try_load_asset(dest/'cidade_laboratorio.ytyp')
for arch in y.archetypes:
 if arch.name in names:
  model=next(m for m in r['models'] if m['name']==arch.name);lo=np.array(model['lo']);hi=np.array(model['hi']);arch.bb_min=Vector(lo);arch.bb_max=Vector(hi);arch.bs_center=Vector((lo+hi)/2);arch.bs_radius=float(np.linalg.norm(hi-lo)/2)
save_asset(y,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),src,'cidade_laboratorio')
for f in src.iterdir():
 if f.suffix not in ('.ydr','.ytyp'):continue
 assert try_load_asset(f) is not None,f.name
 if (dest/f.name).exists():shutil.copy2(dest/f.name,backup/f.name)
 shutil.copy2(f,dest/f.name)
report={'plants':54,'unique_plant_models':18,'triangles_per_plant_near':79100,'medium_lod_distance':18,'near_geometry':'authored original','native_validation':True,'in_game_visual_validation':False,'changes':['detailed plants','medium LOD','softer metal normal maps','reduced plant specular','corner trim','balanced local lighting'],'pending':['rain protection','door and floor collision end-to-end test']}
(W/'validacao_polimento.json').write_text(json.dumps(report,indent=2))
print('INSTALLED_POLISHED',len(list(src.glob('*.ydr'))))
