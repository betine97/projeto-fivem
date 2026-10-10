import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import try_load_asset
from shapely.geometry import Polygon,box
from collections import Counter
origin=np.array(json.loads((W/'medidas_estudo.json').read_text())['native_origin']);spec=json.loads((W/'encaixe_fachada.json').read_text());poly=Polygon(spec['ground_polygon'])
def walk(b,parent=np.eye(4),off=np.zeros(3)):
 if b is None:return
 tx=np.array(b.composite_transform)@parent
 if hasattr(b,'geometry_primitives'):
  vs=np.array([v.co for v in b.geometry_vertices]);vs=(np.c_[vs,np.ones(len(vs))]@tx)[:,:3]+off
  counts=Counter()
  for t in b.geometry_primitives:
   p=vs[list(t.vertices)];pad=t.radius or 0;lo=p.min(0)-pad;hi=p.max(0)+pad
   if hi[2]<-.8 or lo[2]>2.55:continue
   if not poly.buffer(.30).intersects(box(lo[0],lo[1],hi[0]+.0001,hi[1]+.0001)):continue
   counts[t.primitive_type.name]+=1
   if t.primitive_type.name not in ('TRIANGLE','BOX'):print('PRIMITIVE',t.primitive_type.name,np.round(lo,3),np.round(hi,3))
  print('BOUND_INTERSECTS',dict(counts))
 else:print('BOUND',type(b).__name__,getattr(b,'bb_min',None),getattr(b,'bb_max',None))
 for c in getattr(b,'children',[]):walk(c,tx,off)
for e in json.loads((W/'work/near_house_entities.json').read_text()):
 if not e['name'].endswith('lod'):
  f=W/'work/native'/(e['name']+'.ydr')
  if not f.exists():continue
  a=try_load_asset(f);print('DRAWABLE',e['name'],'bound',type(a.bounds).__name__);walk(a.bounds,off=np.array(e['pos'])-origin)
  if e['name']=='ch2_09b_l2':
   for m in next(iter(a.models.values())):
    for g in m.geometries:
     vs=g.vertex_buffer['Position'].astype(float)+np.array(e['pos'])-origin;count=0;bounds=[]
     for ids in g.index_buffer.reshape(-1,3):
      p=vs[ids];lo=p.min(0);hi=p.max(0)
      if hi[2]>-.795 and lo[2]<2.55 and poly.intersects(box(lo[0],lo[1],hi[0]+.0001,hi[1]+.0001)):count+=1;bounds.extend(p)
     if count:print('TERRAIN_OVERLAP',count,np.min(bounds,0),np.max(bounds,0))
for f in sorted((W/'work/native').glob('*ch2_09b_[0-3].ybn')):
 a=try_load_asset(W/'fivem'/f.name if (W/'fivem'/f.name).exists() else f);print('WORLD',f.name);walk(a,off=-origin)
