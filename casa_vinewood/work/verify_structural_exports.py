"""Check visible side faces and real thickness in the serialized GTA drawables."""
import sys,json,hashlib
from pathlib import Path
from itertools import product
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import try_load_asset
from shapely.geometry import Polygon
from shapely.ops import unary_union
spec=json.loads((W/'espessuras_estruturais.json').read_text());solid={s['name']:s for s in spec['solids']};rows=json.loads((W/'colisoes_fivem.json').read_text())
groups={'ground':'mansao_paredes','upper':'mansao_paredes','outer':'mansao_paredes','slabs':'mansao_pisos','stairs':'mansao_escada','ceil':'mansao_teto'}
triangles={};normal_agreement={};wood_triangles={}
for name in set(groups.values()):
 a=try_load_asset(W/'fivem'/(name+'.ydr'));ts=[];nn=[];wood=[]
 for models in a.models.values():
  for m in models:
   for g in m.geometries:
    p=g.vertex_buffer['Position'][g.index_buffer.reshape(-1,3)].astype(float);n=g.vertex_buffer['Normal'][g.index_buffer.reshape(-1,3)].astype(float).mean(1)
    ts.extend(p);nn.extend(n)
    shader=a.shader_group.shaders[g.shader_index];texture=str(next((x.value for x in shader.parameters if x.name.lower()=='diffusesampler'),''))
    if 'im_wood_panels_05' in texture:wood.extend(p)
 triangles[name]=np.array(ts);normal_agreement[name]=np.array(nn);wood_triangles[name]=np.array(wood)
checks=[];missing=[];reversed_faces=[];bad_normals=[]
def surface_hits(a,b,T):
 d=b-a;e1=T[:,1]-T[:,0];e2=T[:,2]-T[:,0];h=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,h);ok=abs(det)>1e-10;inv=np.divide(1,det,out=np.zeros_like(det),where=ok);s=a-T[:,0];u=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1);v=inv*(q@d);t=inv*np.einsum('ij,ij->i',e2,q)
 return np.flatnonzero(ok&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1.000001)&(t>0)&(t<1)),det,t
for row in rows:
 if row['source'] not in solid:continue
 p=np.array(row['points']);pn=np.cross(p[1]-p[0],p[2]-p[0]);length=np.linalg.norm(pn)
 if length<1e-9:continue
 pn/=length;group=row['group'];center=p.mean(0);T=triangles[group]
 ix,det,t=surface_hits(center+pn*.01,center-pn*.01,T)
 matched=[i for i in ix if abs(t[i]-.5)*.02<.001]
 if not matched:missing.append(row['source']);continue
 facing=[i for i in matched if det[i]>0]
 if not facing:reversed_faces.append(row['source']);continue
 # The exporter may triangulate a quad along its other diagonal. Compare the
 # front-facing surface and its interpolated shading normal, not vertex sets.
 match=min(facing,key=lambda i:abs(t[i]-.5));q=T[match];qn=np.cross(q[1]-q[0],q[2]-q[0]);qn/=np.linalg.norm(qn)
 vn=normal_agreement[group][match];vn/=max(np.linalg.norm(vn),1e-9)
 if np.dot(qn,vn)<.99:
  bad_normals.append(row['source'])
  print('NORMAL_MISMATCH',row['source'],dict(dot=float(np.dot(qn,vn)),exported_triangle=q.tolist(),source_triangle=p.tolist(),geometric_normal=qn.tolist(),shading_normal=vn.tolist()),flush=True)
 checks.append(dict(source=row['source'],position_error_m=float(abs(t[match]-.5)*.02),orientation_matches=True))
wall_checks=[];slab_checks=[]
for s in spec['solids']:
 if s['thickness_m'] is None:continue
 target=s['thickness_m'];ts=np.array([r['points'] for r in rows if r['source']==s['name']])
 assert len(ts),s['name']
 p=ts.reshape(-1,3);size=p.max(0)-p.min(0)
 if s['group'] in ('ground','upper'):
  actual=float(min(size[:2]));wall_checks.append(dict(name=s['name'],target_m=target,actual_m=actual))
 elif s['group']=='outer':
  panel=next(q for q in json.loads((W/'revisao_juntas.json').read_text())['panels'] if q['name']==s['name']);actual=float(size[panel['axis']]);wall_checks.append(dict(name=s['name'],target_m=target,actual_m=actual))
 else:
  actual=float(size[2]);slab_checks.append(dict(name=s['name'],target_m=target,actual_m=actual))
 assert abs(actual-target)<.001,(s['name'],actual,target)
assert not missing and not reversed_faces and not bad_normals,dict(missing=sorted(set(missing)),reversed=sorted(set(reversed_faces)),bad_normals=sorted(set(bad_normals)))
# Front-face rays test the exact end cap shown edge-on in the user's prints.
# Two-sided visibility tests from previous revisions could miss wrong winding.
T=triangles['mansao_pisos'];front_tests=[]
def front_hit(a,b):
 d=b-a;e1=T[:,1]-T[:,0];e2=T[:,2]-T[:,0];h=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,h);ok=det>1e-9;inv=np.divide(1,det,out=np.zeros_like(det),where=ok);s=a-T[:,0];u=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1);v=inv*(q@d);t=inv*np.einsum('ij,ij->i',e2,q)
 return bool(np.any(ok&(u>=0)&(v>=0)&(u+v<=1)&(t>0)&(t<1)))
for name,a,b in [('borda escada esquerda',[0.,3.8,2.5],[-.6,3.8,2.5]),('borda escada direita',[2.2,3.8,2.5],[2.8,3.8,2.5]),('borda escada fundos',[.5,5.4,2.5],[.5,6.,2.5]),('borda mezanino',[0,-4.3,2.5],[0,-3.4,2.5])]:
 found=front_hit(np.array(a),np.array(b));front_tests.append(dict(name=name,visible_front_face=found));assert found,name
overlaps=[]
for z in (2.358,2.808):
 surfaces=[]
 for group in ('mansao_pisos','mansao_escada'):
  # Metal guardrail bases correctly meet the floor; compare the wooden walking
  # surfaces and their undersides, where coincident faces cause z-fighting.
  surfaces.append(unary_union([Polygon(p[:,:2]) for p in wood_triangles[group] if np.max(abs(p[:,2]-z))<.00001]))
 area=surfaces[0].intersection(surfaces[1]).area
 overlaps.append(dict(level_z=z,coincident_surface_m2=area));assert area<.00001,('Stair arrival z-fighting',z,area)
outer_surfaces={'terreo':{},'superior':{}}
panel_axes={p['name']:p['axis'] for p in json.loads((W/'revisao_juntas.json').read_text())['panels']}
for row in rows:
 name=row['source'];level='terreo' if name.startswith('Revestimento continuo terreo') else 'superior' if name.startswith('Revestimento continuo superior') else None
 if not level:continue
 p=np.array(row['points']);n=np.cross(p[1]-p[0],p[2]-p[0]);length=np.linalg.norm(n)
 if length<1e-9:continue
 axis=panel_axes[name]
 if abs(n[axis])/length<.99:continue
 key=(axis,round(float(p[:,axis].mean()),4),int(n[axis]>0));projection=(1,2) if axis==0 else (0,2)
 outer_surfaces[level].setdefault(key,[]).append(Polygon(p[:,projection]))
outer_overlap=sum(unary_union(outer_surfaces['terreo'][k]).intersection(unary_union(outer_surfaces['superior'][k])).area for k in outer_surfaces['terreo'].keys()&outer_surfaces['superior'].keys())
assert outer_overlap<1e-6,('Overlapping wall levels',outer_overlap)
report=dict(passed=True,structural_solids=spec['solid_count'],visible_triangles_checked=len(checks),missing_triangles=len(missing),reversed_triangles=len(reversed_faces),incorrect_shading_normals=len(bad_normals),wall_thickness_checks=wall_checks,slab_thickness_checks=slab_checks,front_face_edge_tests=front_tests,stair_arrival_surface_overlap=overlaps,max_position_error_m=max(q['position_error_m'] for q in checks),drawable_sha256={name+'.ydr':hashlib.sha256((W/'fivem'/(name+'.ydr')).read_bytes()).hexdigest() for name in sorted(set(groups.values()))},in_game_verified=False)
report['outer_level_coincident_surface_m2']=outer_overlap
(W/'verificacao_espessuras_exportadas.json').write_text(json.dumps(report,indent=2));print('EXPORTED_SOLID_THICKNESS',len(wall_checks),'walls;',len(slab_checks),'slabs;',len(checks),'visible triangles;',len(front_tests),'front-facing edge checks passed',flush=True)
