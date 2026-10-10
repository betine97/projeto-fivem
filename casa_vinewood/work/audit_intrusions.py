import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from shapely.geometry import Polygon,box as rect
from shapely.ops import unary_union
from szio.gta5 import try_load_asset
origin=np.array(json.loads((W/'medidas_estudo.json').read_text())['native_origin']);spec=json.loads((W/'encaixe_fachada.json').read_text());poly=Polygon(spec['ground_polygon'])
rows=json.loads((W/'work/entities.json').read_text());components=[]
for e in rows:
 if not e['name'].startswith('ch2_09b_hs05'):continue
 name=e['name'];f=W/'work/native'/(name+'.ydr')
 if not f.exists():continue
 a=try_load_asset(f);off=np.array(e['pos'])-origin
 for m in next(iter(a.models.values())):
  for gi,g in enumerate(m.geometries):
   vs=g.vertex_buffer['Position'].astype(float)+off;ids=g.index_buffer.reshape(-1,3)
   # Split into connected position components (native UV seams duplicate indices).
   parent={}
   def find(x):
    parent.setdefault(x,x)
    if parent[x]!=x:parent[x]=find(parent[x])
    return parent[x]
   keys=[tuple(np.round(p,3)) for p in vs]
   for t in ids:
    root=find(keys[t[0]])
    for i in t[1:]:parent[find(keys[i])]=root
   groups={}
   for t in ids:groups.setdefault(find(keys[t[0]]),[]).append(t)
   sh=a.shader_group.shaders[g.shader_index];mat=next((p.value for p in sh.parameters if p.name.lower()=='diffusesampler'),'')
   for ts in groups.values():
    p=vs[np.array(ts).reshape(-1)];lo=p.min(0);hi=p.max(0)
    if '--gates' in sys.argv and ('extras' in str(mat).lower() or 'doors' in str(mat).lower()) and hi[2]-lo[2]>1 and lo[2]<1:print('GATE_CANDIDATE',name,mat,len(ts),np.round(lo,3),np.round(hi,3))
    if hi[2]<-.79 or lo[2]>2.56:continue
    overlap=poly.intersection(rect(lo[0],lo[1],hi[0]+.0001,hi[1]+.0001)).area
    if overlap<.01:continue
    item={'name':name,'geometry':gi,'material':str(mat),'triangles':len(ts),'lo':lo.tolist(),'hi':hi.tolist(),'floor_overlap_m2':overlap};components.append(item)
    if name!='ch2_09b_hs05' or len(ts)<30:print(name,mat,len(ts),'bounds',np.round(lo,3).tolist(),np.round(hi,3).tolist(),'overlap',round(overlap,2))
floors=try_load_asset(W/'fivem/mansao_pisos.ydr');ts=[]
for m in next(iter(floors.models.values())):
 for g in m.geometries:
  for ids in g.index_buffer.reshape(-1,3):
   p=g.vertex_buffer['Position'][ids].astype(float);n=np.cross(p[1]-p[0],p[2]-p[0])
   if n[2]>1e-7 and np.max(np.abs(p[:,2]+.8))<.01:ts.append(Polygon(p[:,:2]))
cover=unary_union(ts);expected=poly.buffer(-.025,join_style=2);missing=expected.difference(cover);outside=cover.difference(expected)
print('MISSING_FLOOR',missing.area,missing.wkt)
(W/'audit_intrusions.json').write_text(json.dumps({'native_components':components,'ground_floor_missing_area':missing.area,'ground_floor_missing_wkt':missing.wkt},indent=2))
