import sys,json,math,shutil,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';OUT=W/'decor_fivem';D=R/'server-data/resources/cidade_mansao'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
from szio.gta5.maps import *
from szio.gta5.entities import *
from szio.types import Vector,Quaternion
cfg=json.loads((W/'decoracao_iluminacao.json').read_text());origin=np.array(cfg['origin']);bounds=json.loads((W/'work/decor_export_bounds.json').read_text());lo=np.array(bounds['lo']);hi=np.array(bounds['hi'])
targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
a=try_load_asset(OUT/'mansao_spots_led.ydr');assert a is not None;a.bounds=None;save_asset(a,targets,OUT,'mansao_spots_led')
ar=Archetype('mansao_spots_led',ArchetypeType.BASE,32,150,0,150,'','','','mansao_spots_led',Vector(lo),Vector(hi),Vector((lo+hi)/2),float(np.linalg.norm(hi-lo)/2),'mansao_spots_led',ArchetypeAssetType.DRAWABLE,[])
rug=cfg['rug'];rl=np.array(rug['lo']);rh=np.array(rug['hi']);rname=rug['model']
a=try_load_asset(OUT/(rname+'.ydr'));assert a is not None;a.bounds=None;save_asset(a,targets,OUT,rname)
rar=Archetype(rname,ArchetypeType.BASE,32,150,0,150,'','','',rname,Vector(rl),Vector(rh),Vector((rl+rh)/2),float(np.linalg.norm(rh-rl)/2),rname,ArchetypeAssetType.DRAWABLE,[])
save_asset(AssetMapTypes(name='mansao_decoracao',archetypes=[ar,rar]),targets,OUT,'mansao_decoracao')
entities=[Entity('mansao_spots_led',Vector(origin),Quaternion((1,0,0,0)),1,1,EntityFlags.IS_STATIC,0,-1,150,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[])]
for p in cfg['plants']:
 entities.append(Entity(p['model'],Vector(origin+np.array(p['position'])),Quaternion((1,0,0,0)),p['scale'],p['scale'],EntityFlags.IS_STATIC,0,-1,100,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[]))
entities.append(Entity(rname,Vector(origin),Quaternion((1,0,0,0)),1,1,EntityFlags.IS_STATIC,0,-1,150,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[]))
for p in cfg['paintings']:
 entities.append(Entity(p['model'],Vector(origin+np.array(p['position'])),Quaternion(p['quaternion']),p['scale'],p['scale'],EntityFlags.IS_STATIC,0,-1,100,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[]))
save_asset(AssetMapData(name='mansao_decoracao',content_flags=MapContentFlags.HAS_ENTITIES_HD|MapContentFlags.HAS_PHYSICS,entities=entities,streaming_extents=(Vector(origin-170),Vector(origin+170)),entities_extents=(Vector(origin+np.minimum(lo,[-10,-16,-.8])),Vector(origin+np.maximum(hi,[15,10,6.6])))),targets,OUT,'mansao_decoracao')
print('DECOR_PACKAGE_READY',len(entities),'entities',flush=True)
