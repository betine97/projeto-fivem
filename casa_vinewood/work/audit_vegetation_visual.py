"""Find plant/ornament geometry inside the mansion using installed map transforms."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';OUT=W/'fivem';N=W/'work/native'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps'),str(R/'laboratorio_fivem/work'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from shapely.geometry import Polygon,Point
from clip_geometry import subtract_box
from szio.gta5 import try_load_asset
origin=np.array(json.loads((W/'medidas_estudo.json').read_text())['native_origin']);spec=json.loads((W/'encaixe_fachada.json').read_text())
def cells(poly,z0,z1):
 ps=list(poly.exterior.coords);xs=sorted({p[0] for p in ps});ys=sorted({p[1] for p in ps})
 return [(np.array([x0,y0,z0]),np.array([x1,y1,z1])) for x0,x1 in zip(xs,xs[1:]) for y0,y1 in zip(ys,ys[1:]) if poly.covers(Point((x0+x1)/2,(y0+y1)/2))]
volumes=cells(Polygon(spec['ground_polygon']).buffer(-.015,join_style=2),-.80,2.558)+cells(Polygon(spec['upper_polygon']).buffer(-.015,join_style=2),2.558,6.489)
def rotation(q):
 w,x,y,z=q;x,y,z=-x,-y,-z
 return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def mapped(e):
 f=OUT/e['map']
 source=N/e['map']
 if source.exists():
  original=try_load_asset(source)
  ix=next((i for i,q in enumerate(original.entities) if str(q.archetype_name)==e['name'] and np.linalg.norm(np.array(q.position)-e['pos'])<.01),None)
  if ix is not None:
   q=(try_load_asset(f) if f.exists() else original).entities[ix]
   assert str(q.archetype_name)==e['name']
   return dict(e,pos=list(q.position),rot=list(q.rotation),scale=[q.scale_xy,q.scale_xy,q.scale_z],entity_index=ix)
 if f.exists():
  qs=[q for q in try_load_asset(f).entities if str(q.archetype_name)==e['name']]
  if qs:
   q=min(qs,key=lambda q:np.linalg.norm(np.array(q.position)-e['pos']))
   if np.linalg.norm(np.array(q.position)-e['pos'])<10:return dict(e,pos=list(q.position),rot=list(q.rotation))
 return e
def visual_points(e):
 f=OUT/(e['name']+'.ydr')
 if not f.exists():f=N/f.name
 if not f.exists():return []
 a=try_load_asset(f);rot=rotation(e['rot']);off=np.array(e['pos'])-origin;ts=[]
 for models in a.models.values():
  for m in models:
   for g in m.geometries:
    vs=(g.vertex_buffer['Position'].astype(float)*np.array(e.get('scale',[1,1,1])))@rot.T+off
    ts.extend(vs[g.index_buffer.reshape(-1,3)])
 return ts
def intrusion_area(ts):
 area=0.;count=0
 for tri in ts:
  p=list(tri);lo=tri.min(0);hi=tri.max(0)
  for a,b in volumes:
   if np.any(hi<a) or np.any(lo>b):continue
   # Area removed by the architectural volume is the actual interior intrusion.
   out,hit=subtract_box(p,a,b)
   if not hit:continue
   def ar(q):return sum(np.linalg.norm(np.cross(q[i]-q[0],q[i+1]-q[0]))*.5 for i in range(1,len(q)-1))
   removed=ar(p)-sum(ar(q) for q in out)
   if removed>1e-6:area+=removed;count+=1
 return area,count
if __name__=='__main__':
 report=[]
 for original in json.loads((W/'work/near_house_entities.json').read_text()):
  if not any(k in original['name'] for k in ['plant','bush','pot','tree']):continue
  e=mapped(original);ts=visual_points(e)
  if not len(ts):continue
  vs=np.array(ts).reshape(-1,3);area,count=intrusion_area(ts)
  print(e['name'], 'position',np.round(np.array(e['pos'])-origin,3).tolist(),'bounds',np.round(vs.min(0),3).tolist(),np.round(vs.max(0),3).tolist(),'inside_area',round(area,4),'triangles',count,flush=True)
  report.append({'original':original,'installed':e,'visual_lo':vs.min(0).tolist(),'visual_hi':vs.max(0).tolist(),'inside_area_m2':area,'inside_triangles':count})
 (W/'audit_vegetacao_visual.json').write_text(json.dumps(report,indent=2))
