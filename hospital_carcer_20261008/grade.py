from locate import *

sys.path.insert(0,str(R/'casa_vinewood/work/pydeps'))
from shapely.geometry import MultiPoint
e=next(e for e in json.loads((P/'entities.json').read_text()) if e['name']=='bh1_22_base');a=try_load_asset(N/'bh1_22_base.ydr')
for m in a.models[LodLevel.HIGH]:
 for g in m.geometries:
  v=g.vertex_buffer['Position']+e['pos'];print(g.shader_index,len(g.index_buffer)//3,np.round(v.min(0),2),np.round(v.max(0),2))
pts=np.concatenate([g.vertex_buffer['Position'] for m in a.models[LodLevel.HIGH] for g in m.geometries])+e['pos']
h=MultiPoint(pts[:,:2]).convex_hull;print('HULL',list(h.exterior.coords));(P/'base_hull.json').write_text(json.dumps(list(h.exterior.coords)))

