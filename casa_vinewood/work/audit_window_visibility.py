"""Inspect installed glass texture and rays through the facade's glass faces."""
import sys,json,io,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from PIL import Image
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from szio.gta5 import try_load_asset
D=R/'server-data/resources/cidade_mansao/stream';origin=np.array(json.loads((W/'medidas_estudo.json').read_text())['native_origin'])
faces=[];names=[];glass_faces=[];legacy_faces=0;frame_returns=0;glass=try_load_asset(D/'mansao_vidros.ydr');sh=glass.shader_group.shaders[0]
texname=str(next(p.value for p in sh.parameters if p.name.lower()=='diffusesampler'));im=Image.open(io.BytesIO(glass.shader_group.embedded_textures[texname].data.read_bytes())).convert('RGBA');alpha=np.array(im)[:,:,3]
for models in glass.models.values():
 for m in models:
  for g in m.geometries:
   for ids in g.index_buffer.reshape(-1,3):
    p=g.vertex_buffer['Position'][ids].astype(float);n=np.cross(p[1]-p[0],p[2]-p[0]);length=np.linalg.norm(n)
    if length<.2 or abs(n[2]/length)>.2:continue
    # Native Wins includes narrow frame returns as well as actual view panes.
    # Returns are meant to meet solid pilasters; they are not view openings.
    axis=int(np.argmax(np.abs(n))); projected=[i for i in range(3) if i!=axis]
    if np.ptp(p[:,projected],axis=0).min()<.15:frame_returns+=1;continue
    key=tuple(sorted(tuple(np.round(v,5)) for v in p))
    if not any(key==q[0] for q in glass_faces):glass_faces.append((key,p,n/length))
def add(a,offset,label):
 global legacy_faces
 for models in a.models.values():
  for m in models:
   for g in m.geometries:
    s=a.shader_group.shaders[g.shader_index];tex=str(next((p.value for p in s.parameters if p.name.lower()=='diffusesampler'),''));ids=g.index_buffer.reshape(-1,3)
    if 'wins' in tex.lower():legacy_faces+=len(ids)
    # Native leaves and translucent decals do not seal a window.
    if s.render_bucket not in (0,):continue
    vs=g.vertex_buffer['Position'].astype(float)+offset
    for ii in ids:faces.append(vs[ii]);names.append(label+':'+tex)
for e in json.loads((W/'work/near_house_entities.json').read_text()):
 if not (e['name'].startswith('ch2_09b_hs05') or e['name'] in ('ch2_09b_l2','ch2_09b_emissive_05')) or 'lod' in e['name']:continue
 f=D/(e['name']+'.ydr')
 if not f.exists():f=W/'work/native'/f.name
 add(try_load_asset(f),np.array(e['pos'])-origin,e['name'])
for name in ('mansao_paredes','mansao_pisos','mansao_escada','mansao_teto'):add(try_load_asset(D/(name+'.ydr')),np.zeros(3),name)
T=np.array(faces);lo=T.min(1);hi=T.max(1)
def intersections(a,b):
 ix=np.flatnonzero(np.all(hi>=np.minimum(a,b)-.001,1)&np.all(lo<=np.maximum(a,b)+.001,1))
 if not len(ix):return []
 ts=T[ix];direction=b-a;v1=ts[:,1]-ts[:,0];v2=ts[:,2]-ts[:,0];h=np.cross(direction,v2);det=np.einsum('ij,ij->i',v1,h);ok=np.abs(det)>1e-10;inv=np.divide(1,det,out=np.zeros_like(det),where=ok)
 s=a-ts[:,0];u=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,v1);v=inv*(q@direction);t=inv*np.einsum('ij,ij->i',v2,q)
 ok&=(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)&(t>1e-5)&(t<1-1e-5)
 return sorted(set(names[i] for i in ix[ok]))
checks=[]
for key,p,n in glass_faces:
 tested=[]
 for bary in [(1/3,1/3,1/3),(.6,.2,.2),(.2,.6,.2),(.2,.2,.6)]:
  center=np.array(bary)@p;hits=intersections(center-n*.35,center+n*.35);tested.append({'point':np.round(center,4).tolist(),'opaque_hits':hits})
 checks.append({'triangle':p.tolist(),'normal':n.tolist(),'samples':tested,'clear':all(not q['opaque_hits'] for q in tested)})
blocked=[q for q in checks if not q['clear']]
planes={}
for key,p,n in glass_faces:
 axis=int(np.argmax(np.abs(n))); axes=[i for i in range(3) if i!=axis]
 plane=(axis,round(float(p[:,axis].mean()),3))
 planes.setdefault(plane,[]).append(Polygon(p[:,axes]))
panes=[]
for (axis,coordinate),polys in planes.items():
 union=unary_union(polys); components=[union] if union.geom_type=='Polygon' else list(union.geoms)
 axes=[i for i in range(3) if i!=axis]; normal=np.eye(3)[axis]
 for component in components:
  if component.area<.2:continue
  bounds=component.bounds; samples=[]
  # A divider or a reveal may hide a small part of a pane. Record it without
  # mistaking an actual wall edge for opaque glass across the whole opening.
  for u in np.linspace(bounds[0],bounds[2],11)[1:-1]:
   for z in np.linspace(bounds[1],bounds[3],11)[1:-1]:
    if not component.contains(Point(u,z)):continue
    p=np.zeros(3);p[axis]=coordinate;p[axes]=[u,z]
    hits=intersections(p-normal*.35,p+normal*.35)
    samples.append({'point':np.round(p,4).tolist(),'opaque_hits':hits})
  clear=sum(not s['opaque_hits'] for s in samples)
  panes.append({'axis':axis,'plane':coordinate,'projected_bounds':list(bounds),'area_m2':component.area,'samples':samples,'clear_rays':clear,'rays':len(samples),'has_view_through':bool(clear)})
transparent=bool(sh.render_bucket==1 and alpha.max()<128)
sealed=[p for p in panes if not p['has_view_through']]
overlay_hits=[h for p in panes for s in p['samples'] for h in s['opaque_hits'] if 'emissive' in h or 'wins' in h.lower()]
result={'installed_file_sha256':hashlib.sha256((D/'mansao_vidros.ydr').read_bytes()).hexdigest(),'glass_shader':str(sh.name),'render_bucket':sh.render_bucket,'texture_alpha_min':int(alpha.min()),'texture_alpha_max':int(alpha.max()),'transparent_material':transparent,'remaining_native_opaque_window_triangles':legacy_faces,'frame_return_triangles_excluded':frame_returns,'glass_triangles_inspected':len(checks),'rays_tested':len(checks)*4,'opaque_obstructions':blocked,'window_panes':panes,'sealed_panes':len(sealed),'opaque_window_overlay_hits':len(overlay_hits),'passed':bool(transparent and legacy_faces==0 and not sealed and not overlay_hits),'in_game_test':False,'method':'Installed GEN8 models, embedded texture alpha, bidirectional facade rays; opaque wall/reveal intersections recorded separately.'}
(W/'audit_janelas.json').write_text(json.dumps(result,indent=2));print('GLASS_ALPHA',alpha.min(),alpha.max(),'BUCKET',sh.render_bucket,'ORIGINAL_WINDOW_GEOMETRY',legacy_faces,'TESTED',len(checks),'BLOCKED',len(blocked))
from collections import Counter
print('OBSTRUCTIONS',Counter(h for q in blocked for s in q['samples'] for h in s['opaque_hits']))
for q in blocked[:8]:print('BLOCKED_WINDOW_SAMPLE',q['samples'])
print('PANE_VIEW_CHECK',len(panes),'panes;',len(sealed),'sealed;',len(overlay_hits),'window overlay hits; passed',result['passed'])
