"""Conservative overlapping map-box residency across both authored islands."""
from common import *
S=O/'stream';nature=read(O/'dados/implantacao.json');grass=read(O/'dados/rasteira.json');maps=[]
for row in nature['maps']+grass['maps']:
    a=try_load_asset(S/(row['name']+'.ymap'));lo,hi=map(np.asarray,a.streaming_extents)
    maps.append((lo,hi,len(a.entities),'natureza'))
for folder,category in [(R/'server-data/resources/cayo_vizinha/stream','cayo'),(R/'server-data/resources/porto_esperanca/stream','casas'),(O/'terreno','terreno')]:
    for p in folder.glob('*.ymap'):
        override=O/'porto_filtrado'/p.name
        a=try_load_asset(override if override.is_file() else p);lo,hi=map(np.asarray,a.streaming_extents)
        maps.append((lo,hi,len(a.entities),category))
points=np.array([(xx,yy,zz) for xx in range(-4000,3001,100) for yy in range(-2500,6501,100) for zz in [0,20,100,300,600,1000,2000]])
count=np.zeros(len(points),int);categories={}
for lo,hi,n,category in maps:
    resident=n*((points>=lo).all(1)&(points<=hi).all(1));count+=resident
    if category not in categories:categories[category]=np.zeros(len(points),int)
    categories[category]+=resident
i=int(count.argmax());peak=int(count[i]);limit=65000
assert peak<limit-10000,(peak,points[i].tolist())
report=dict(passed=True,estimated_peak_map_entities=peak,native_pool_limit=limit,estimated_margin=limit-peak,camera=points[i].tolist(),maps=len(maps),camera_samples=len(points),peak_by_resource={k:int(v[i]) for k,v in categories.items()},method='Conservative sum of entities in overlapping map streaming boxes; not a live pool reading',in_game_visual_verified=False)
write(O/'dados/validacao_orcamento_render.json',report);print('MAP_RESIDENCY_BUDGET_PASSED',report,flush=True)
