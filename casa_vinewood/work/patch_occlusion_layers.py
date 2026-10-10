"""Remove only the mansion's volume from all overlapping native occluder layers."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';OUT=W/'fivem'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps'),str(R/'laboratorio_fivem/work'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from shapely.geometry import Polygon
from clip_geometry import subtract_box
from szio.gta5 import try_load_asset,save_asset,AssetTarget,AssetFormat,AssetVersion
from szio.gta5.maps import MapModelOccluder,MapModelOccluderFlags
origin=np.array(json.loads((W/'medidas_estudo.json').read_text())['native_origin'])
original=json.loads((W/'alteracoes_nativas.json').read_text())
cuts=[(np.array(q['lo']),np.array(q['hi'])) for q in original['cuts_native']]
spec=json.loads((W/'encaixe_fachada.json').read_text())
foot=Polygon(spec['ground_polygon']).union(Polygon(spec['upper_polygon'])).buffer(.88,join_style=2)
SIGNS=np.array([(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
def clip(p):
 pieces=[p];changed=False
 for lo,hi in cuts:
  fresh=[]
  for q in pieces:
   if np.any(np.max(q,axis=0)<lo) or np.any(np.min(q,axis=0)>hi):fresh.append(q);continue
   ps,hit=subtract_box(q,lo,hi);fresh.extend(ps);changed|=hit
  pieces=fresh
 return pieces,changed
def triangles(p):
 for i in range(1,len(p)-1):
  t=np.array([p[0],p[i],p[i+1]])
  if np.linalg.norm(np.cross(t[1]-t[0],t[2]-t[0]))>1e-7:yield t
def chunks(ts,flags):
 chunk=[];points=set()
 def emit(q):
  v=np.array(q).reshape(-1,3);unique,inv=np.unique(np.round(v,5),axis=0,return_inverse=True)
  return MapModelOccluder(flags,unique.astype(np.float32),inv.reshape(-1,3).astype(np.uint8))
 for t in ts:
  keys={tuple(np.round(v,5)) for v in t}
  if chunk and len(points|keys)>250:yield emit(chunk);chunk=[];points=set()
  chunk.append(t);points|=keys
 if chunk:yield emit(chunk)
report={'maps_scanned':0,'patched':[],'runtime_guard_volume_local':[[-12.5,-18.5,-2],[17,12,9]],'in_game_verified':False}
for f in sorted((W/'work/occlusion_sources').glob('*.ymap')):
 if 'ch2' not in f.name:continue
 # Preserve an already corrected base file, then add the missing DLC variants.
 a=try_load_asset(OUT/f.name if (OUT/f.name).exists() else f);new=[];changes=0;boxes=[];box_changes=0
 report['maps_scanned']+=1
 for o in a.model_occluders:
  vs=o.vertices.astype(float)-origin
  if not any(np.all(vs.max(0)>=lo) and np.all(vs.min(0)<=hi) for lo,hi in cuts):new.append(o);continue
  ts=[];changed=False
  for ids in o.indices:
   ps,hit=clip(list(vs[ids]));changed|=hit
   for q in ps:ts.extend(t+origin for t in triangles(q))
  if changed:new.extend(chunks(ts,o.flags));changes+=1
  else:new.append(o)
 for o in a.box_occluders:
  center=np.array(o.center)-origin;size=np.array(o.size)*.5;c,s=o.cos_sin_z
  pts=SIGNS*size;pts[:,:2]=pts[:,:2]@np.array([[s,c],[-c,s]]);pts+=center
  shape=Polygon(pts[[0,1,2,3],:2])
  overlap=shape.intersects(foot) and pts[:,2].max()>-1 and pts[:,2].min()<7
  if overlap:box_changes+=1
  else:boxes.append(o)
 if changes or box_changes:
  a.model_occluders=new;a.box_occluders=boxes
  save_asset(a,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),OUT,f.stem)
  b=try_load_asset(OUT/f.name);assert len(b.box_occluders)==len(boxes)
  report['patched'].append({'file':f.name,'model_occluders_clipped':changes,'box_occluders_removed':box_changes})
  print('PATCHED_OCCLUSION_LAYER',report['patched'][-1],flush=True)
def overlap_counts(a):
 box_hits=[];model_hits=0
 for o in a.box_occluders:
  center=np.array(o.center)-origin;size=np.array(o.size)*.5;c,s=o.cos_sin_z
  pts=SIGNS*size;pts[:,:2]=pts[:,:2]@np.array([[s,c],[-c,s]]);pts+=center
  if Polygon(pts[[0,1,2,3],:2]).intersects(foot) and pts[:,2].max()>-1 and pts[:,2].min()<7:
   box_hits.append({'center_local':center.tolist(),'size_m':list(o.size)})
 for o in a.model_occluders:
  vs=o.vertices.astype(float)-origin
  if not any(np.all(vs.max(0)>=lo) and np.all(vs.min(0)<=hi) for lo,hi in cuts):continue
  if any(clip(list(vs[ids]))[1] for ids in o.indices):model_hits+=1
 return {'boxes':len(box_hits),'models':model_hits,'box_locations':box_hits}
report['layers']=[]
for f in sorted((W/'work/occlusion_sources').glob('*ch2*.ymap')):
 before=overlap_counts(try_load_asset(f));after=overlap_counts(try_load_asset(OUT/f.name if (OUT/f.name).exists() else f))
 if before['boxes'] or before['models']:
  report['layers'].append({'file':f.name,'before':before,'after':after})
report['passed']=all(q['after']['boxes']==0 and q['after']['models']==0 for q in report['layers'])
assert report['passed'],'Native occlusion still occupies the mansion.'
(W/'correcao_oclusao.json').write_text(json.dumps(report,indent=2))
print('OCCLUSION_SCAN_AND_PATCH_OK',report['maps_scanned'],'maps;',len(report['patched']),'patched',flush=True)
