from locate import *
sys.path.insert(0,str(R/'casa_vinewood/work/pydeps'))
from shapely.geometry import Polygon
from shapely import constrained_delaunay_triangles
origin=np.array([-475.,-322.,35.2]);h=np.array(json.loads((P/'base_hull.json').read_text()))[:-1];outer=Polygon(h).simplify(.12,preserve_topology=True);coords=np.array(outer.exterior.coords)[:-1]
e=next(e for e in json.loads((P/'entities.json').read_text()) if e['name']=='bh1_22_base');a=try_load_asset(N/'bh1_22_base.ydr');vs=np.concatenate([g.vertex_buffer['Position'] for m in a.models[LodLevel.HIGH] for g in m.geometries])+e['pos'];ground=vs[(vs[:,2]>31)&(vs[:,2]<35)]
heights=[]
for p in coords:
 d=np.linalg.norm(ground[:,:2]-p,axis=1);near=ground[d<max(.1,d.min()+.05)];heights.append(float(near[:,2].max()))
inner=Polygon([(-508,-344),(-442,-344),(-442,-300),(-508,-300)])
print('INSIDE',outer.contains(inner),outer.area,heights)
zs={tuple(p):z for p,z in zip(coords,heights)};tris=[]
for t in constrained_delaunay_triangles(Polygon(coords,holes=[inner.exterior.coords])).geoms:
 q=[]
 for p in list(t.exterior.coords)[:3]:
  z=zs.get(tuple(p),35.2);q.append((np.array([*p,z])-origin).tolist())
 tris.append(q)
(P/'plaza.json').write_text(json.dumps({'triangles':tris,'polygon':list(outer.exterior.coords),'edge_heights':heights},indent=2))
