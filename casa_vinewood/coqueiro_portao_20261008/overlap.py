from diagnose import *
sys.path.insert(0,str(R/'casa_vinewood/work/pydeps'))
from shapely.geometry import Polygon
from shapely.ops import unary_union
entities=json.loads((R/'casa_vinewood/work/near_house_entities.json').read_text())
groups={}
for name in ['mansao_fachada_entrada','mansao_garagem_subsolo','ch2_09b_hs05','ch2_09b_hs05_details','ch2_09b_l2']:
 a=try_load_asset(S/(name+'.ydr'));off=np.zeros(3) if name.startswith('mansao') else np.array(next(e['pos'] for e in entities if e['name']==name))-origin
 for m in a.models[LodLevel.HIGH]:
  for g in m.geometries:
   for t in g.vertex_buffer['Position'][g.index_buffer.reshape(-1,3)]+off:
    if not (t[:,0].max()>6.10 and t[:,0].min()<13.12 and t[:,1].max()>8.8 and t[:,1].min()<17.8 and t[:,2].min()<-.75):continue
    for ax in [0,1]:
     if np.ptp(t[:,ax])<.001:
      axes=[i for i in range(3) if i!=ax];poly=Polygon(t[:,axes])
      if poly.area>1e-7:groups.setdefault((ax,round(float(t[0,ax]),3)),{}).setdefault(name,[]).append(poly)
for key,byname in groups.items():
 names=list(byname)
 if len(names)<2:continue
 shapes={n:unary_union(v) for n,v in byname.items()}
 for i,n in enumerate(names):
  for other in names[i+1:]:
   a=shapes[n].intersection(shapes[other]).area
   if a>.005:print('OVERLAP',key,n,other,round(a,5))
