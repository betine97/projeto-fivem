from common import *
from szio.gta5 import LodLevel
from collections import Counter
import dataclasses
D=read(O/'dados/densidade_cayo.json')
for n,r in D['models'].items():
    if r['family'] not in ('tree','subcanopy'):continue
    a=try_load_asset(Path(r['drawable_file']))
    print(n,{k.name:sum(len(g.index_buffer)//3 for m in v for g in m.geometries) for k,v in a.models.items()}, {k.name:v for k,v in a.lod_thresholds.items()})
for name in ['h4_ne_ipl_00','h4_ne_ipl_00_lod','h4_ne_ipl_00_slod']:
    path=P/'cayo_perico/originais/mapas'/(name+'.ymap')
    if not path.exists():continue
    a=try_load_asset(path)
    print('MAP',name,'parent',a.parent_name,'flags',a.flags,'content',a.content_flags,'entities',len(a.entities))
    for e in a.entities[:4]:
        print({k:getattr(e,k).name if hasattr(getattr(e,k),'name') else str(getattr(e,k)) for k in ['archetype_name','flags','parent_index','lod_dist','child_lod_dist','lod_level','priority_level','num_children']})
