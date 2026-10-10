"""Check walking clearance against the actual reloaded native files."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import try_load_asset
from szio.gta5.bounds import BoundPrimitiveType,BoundType
from shapely.geometry import Polygon,Point,box
from shapely.ops import unary_union
BASELINE='--baseline' in sys.argv
OUT=W/('backup_antes_limpeza/fivem' if BASELINE else 'fivem')
spec=json.loads((W/'medidas_estudo.json').read_text());origin=np.array(spec['native_origin']);O=np.array(spec['interior_origin_relative_native'])
faces=[];labels=[];smooth=[];checked_props=[]
SIGNS=np.array([(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
FACES=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
def visit(b,parent=np.eye(4),offset=np.zeros(3),label=''):
 if b is None:return
 tx=np.array(b.composite_transform)@parent
 for c in getattr(b,'children',[]):
  if c is not None:visit(c,tx,offset,label)
 if not hasattr(b,'geometry_primitives'):
  if b.bound_type==BoundType.COMPOSITE:return
  mn=np.array(b.bb_min);mx=np.array(b.bb_max);center=(mn+mx)/2
  if b.bound_type==BoundType.BOX:
   corners=center+SIGNS*(mx-mn)*.5;corners=(np.c_[corners,np.ones(8)]@tx)[:,:3]+offset
   for ids in FACES:faces.append(corners[list(ids)]);labels.append(label+':BOX')
  elif b.bound_type in (BoundType.SPHERE,BoundType.CAPSULE,BoundType.CYLINDER):
   if b.bound_type==BoundType.SPHERE:ps=np.array([center]);pad=b.sphere_radius
   else:
    pad,length=b.capsule_radius_length if b.bound_type==BoundType.CAPSULE else b.cylinder_radius_length
    ps=np.array([center+[0,-length*.5,0],center+[0,length*.5,0]])
   ps=(np.c_[ps,np.ones(len(ps))]@tx)[:,:3]+offset;smooth.append((b.bound_type.name,ps,pad,label))
  else:raise AssertionError(f'Unsupported collision {b.bound_type} in {label}')
  return
 vs=np.array([v.co for v in b.geometry_vertices]);vs=(np.c_[vs,np.ones(len(vs))]@tx)[:,:3]+offset
 for i,t in enumerate(b.geometry_primitives):
  p=vs[list(t.vertices)]
  if np.any(p.max(0)<[-10,-16.5,-1.5]) or np.any(p.min(0)>[15.5,10.5,7]):continue
  if t.primitive_type==BoundPrimitiveType.TRIANGLE:ts=[p]
  elif t.primitive_type==BoundPrimitiveType.BOX:
   v1,v2,v3,v4=p;e=((v3+v4)-(v1+v2))*.5;v=p.mean(0)+SIGNS@np.array([e,v3-e-v1,v4-e-v1])*.5;ts=[v[list(ids)] for ids in FACES]
  else:smooth.append((t.primitive_type.name,p,t.radius or 0,f'{label}:{i}'));continue
  for tri in ts:faces.append(tri);labels.append(f'{label}:{i}')
collision_sources=sorted((W/'work/native').glob('*ch2_09b_[0-3].ybn'))
assert len(collision_sources)==24,'Extract base, mpheist and patched mpapartment collisions before verifying.'
for p in collision_sources:
 f=OUT/p.name;visit(try_load_asset(f if f.exists() else p),offset=-origin,label=p.name)
models=json.loads((W/'exportacao_fivem.json').read_text())['models']
for m in models:visit(try_load_asset(OUT/(m['name']+'.ydr')).bounds,label=m['name'])
from audit_vegetation_visual import mapped
props=json.loads((W/'work/near_house_entities.json').read_text())
props += [e for e in json.loads((W/'work/dlc_near_house_props.json').read_text()) if np.all(np.array(e['pos'])-origin >= [-13,-18,-12]) and np.all(np.array(e['pos'])-origin <= [17,12,8])]
props += [q['original'] for q in json.loads((W/'audit_vegetacao_todas_camadas.json').read_text())['instances']]
seen_props=set()
for e in props:
 original=e.copy();e=mapped(e)
 key=(e['name'],*np.round(e['pos'],4),*np.round(e.get('scale',[1,1,1]),4))
 if key in seen_props:continue
 seen_props.add(key)
 p=W/'work/native'/(e['name']+'.ydr')
 if not p.exists():continue
 f=OUT/p.name;a=try_load_asset(f if f.exists() else p)
 if a.bounds is None:continue
 # GTA map entity rotations are inverse quaternions; row-vector matrices below.
 w,x,y,z=np.array(e['rot'],float);x,y,z=-x,-y,-z
 rot=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
 tx=np.eye(4);tx[:3,:3]=np.diag(e.get('scale',[1,1,1]))@rot.T;checked_props.append(e['name']);visit(a.bounds,tx,np.array(e['pos'])-origin,e['name'])
T=np.array(faces);low=T.min(1);high=T.max(1);norm=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0])
SL=np.array([p.min(0)-r for _,p,r,_ in smooth]);SH=np.array([p.max(0)+r for _,p,r,_ in smooth])
def smooth_distance(q,item):
 kind,ps,r,label=item
 if kind=='SPHERE':return max(0,np.linalg.norm(q-ps[0])-r)
 a,b=ps;ab=b-a;length=np.linalg.norm(ab)
 if length<1e-8:return max(0,np.linalg.norm(q-a)-r)
 t=np.dot(q-a,ab)/(length*length)
 if kind=='CAPSULE':return max(0,np.linalg.norm(q-a-np.clip(t,0,1)*ab)-r)
 radial=max(0,np.linalg.norm(q-a-t*ab)-r);axial=max(0,-t*length,(t-1)*length)
 return np.hypot(radial,axial)
def blockers(p,custom_only=False,native_only=False):
 result=[]
 for height,radius in [(.35,.28),(.85,.30),(1.50,.28)]:
  q=p+[0,0,height];ix=np.flatnonzero(np.all(high>=q-radius,1)&np.all(low<=q+radius,1))
  if custom_only:ix=np.array([i for i in ix if labels[i].startswith('mansao_')],dtype=int)
  if native_only:ix=np.array([i for i in ix if not labels[i].startswith('mansao_')],dtype=int)
  if len(ix):result.extend(labels[i] for i in ix[distance(q,T[ix])<radius-.005])
  if not custom_only:
   for i in np.flatnonzero(np.all(SH>=q-radius,1)&np.all(SL<=q+radius,1)):
    if smooth_distance(q,smooth[i])<radius-.005:result.append(smooth[i][3])
 return sorted(set(result))
def distance(p,ts):
 a,b,c=ts[:,0],ts[:,1],ts[:,2];n=np.cross(b-a,c-a);nn=np.einsum('ij,ij->i',n,n);ds=np.einsum('ij,ij->i',p-a,n);proj=p-ds[:,None]*n/np.maximum(nn[:,None],1e-20)
 inside=(nn>1e-15)
 for u,v in [(a,b),(b,c),(c,a)]:inside&=np.einsum('ij,ij->i',np.cross(v-u,proj-u),n)>=-1e-8
 best=np.where(inside,np.abs(ds)/np.sqrt(np.maximum(nn,1e-20)),np.inf)
 for u,v in [(a,b),(b,c),(c,a)]:
  e=v-u;q=np.clip(np.einsum('ij,ij->i',p-u,e)/np.maximum(np.einsum('ij,ij->i',e,e),1e-20),0,1);best=np.minimum(best,np.linalg.norm(p-u-q[:,None]*e,axis=1))
 return best
def support(p):
 mask=(norm[:,2]>1e-7)&(low[:,0]<=p[0]+.005)&(high[:,0]>=p[0]-.005)&(low[:,1]<=p[1]+.005)&(high[:,1]>=p[1]-.005);ix=np.flatnonzero(mask);n=norm[ix];ts=T[ix]
 z=ts[:,0,2]-(n[:,0]*(p[0]-ts[:,0,0])+n[:,1]*(p[1]-ts[:,0,1]))/n[:,2]
 for i,h in zip(ix,z):
  if abs(h-p[2])<.015 and distance(np.array([p[0],p[1],h]),T[i:i+1])[0]<.007:return True
 return False
routes={}
def route(name,points,need_support=True):
 samples=[]
 for a,b in zip(points,points[1:]):
  a=np.array(a);b=np.array(b);steps=max(1,int(np.linalg.norm(b-a)/.08));samples.extend(a+(b-a)*i/steps for i in range(steps+1))
 blocks=[];missing=[]
 for p in samples:
  if need_support and not support(p):missing.append(np.round(p,3).tolist())
  for object_name in blockers(p):blocks.append({'point':np.round(p,3).tolist(),'object':object_name})
 routes[name]={'samples':len(samples),'blocked':blocks[:8],'missing_floor':missing[:8],'passed':not blocks and not missing}
route('entrada_original',[(5.85,-12.90,-.8),(7.10,-12.90,-.8),(7.7,-11.9,-.8)])
route('sacada_esquerda',[(-8.5,-5.17,-.8),(-9.77,-5.17,-.8)])
route('sacada_direita',[(13.6,-5.17,-.8),(15,-5.17,-.8)])
route('sala_deck',[(-5.53,-12.4,-.8),(-5.53,-13.60,-.8)])
route('porta_fundos',[(-2.20,6.98,-.8),(-.40,6.98,-.8)])
route('sala_perto_vidro',[(-7.75,-12.60,-.8),(.85,-12.60,-.8),(.85,-11.10,-.8)])
route('sala_cruzando_poste_original',[(-7,-6.45,-.8),(-5.7,-6.45,-.8)])
route('cozinha_cruzando_poste_original',[(10.7,-6.45,-.8),(12,-6.45,-.8)])
route('portao_entrada_rua',[(2.30,8.10,-.8),(2.30,6.65,-.8),(.10,6.65,-.8),(-.40,6.98,-.8),(-2.20,6.98,-.8)])
route('escada_completa',[(.4,1.45,-.8),(.4,4.45,1.004),(.4,5.05,1.004),(1.8,5.05,1.004),(1.8,4.45,1.004),(1.8,1.75,2.808),(1.8,1.40,2.808)])
for door in spec['door_openings']:
 if door['key'] not in ['ground','upper']:continue
 if door['name']=='Hall para Escada':continue # Checked along the actual sloped walking path above.
 a,b,z0,z1=door['opening'];center=(a+b)*.5;fixed=door['fixed'];z=z0
 pts=[(center,fixed-.45,z),(center,fixed+.45,z)] if door['axis']=='X' else [(fixed-.45,center,z),(fixed+.45,center,z)]
 pts=[(np.array(p)+O).tolist() for p in pts];route(door['name'],pts)
route('Suite master lado hall',[(-2,2.05,2.808),(-1.10,2.05,2.808)])
fit=json.loads((W/'encaixe_fachada.json').read_text());grid=[];scanned=0;eligible=0;coverage=[]
for level,z in [('ground_polygon',-.8),('upper_polygon',2.808)]:
 poly=Polygon(fit[level]).buffer(-.36,join_style=2)
 floor=Polygon(fit[level]).buffer(-.025,join_style=2)
 if z>0:floor=floor.difference(box(-9.3,-13.3,6.4,-3.85)).difference(box(-.3,1.65,2.5,5.7))
 cover=unary_union([Polygon(t[:,:2]) for t,n,label in zip(T,norm,labels) if label.startswith('mansao_pisos:') and n[2]>1e-7 and np.max(np.abs(t[:,2]-z))<.01]);missing=floor.difference(cover.buffer(.002,join_style=2)).area
 coverage.append({'floor_z':z,'expected_m2':floor.area,'missing_m2_with_2mm_quantization_tolerance':missing,'passed':missing<1e-4})
 x0,y0,x1,y1=poly.bounds
 for x in np.arange(x0,x1,.25):
  for y in np.arange(y0,y1,.25):
   if not poly.covers(Point(x,y)):continue
   p=np.array([x,y,z]);scanned+=1
   if not support(p) or blockers(p,custom_only=True):continue
   eligible+=1;hits=blockers(p,native_only=True)
   if hits:grid.append({'point':np.round(p,3).tolist(),'objects':hits})
result={'serialized_files_checked':True,'collision_primitive_types_checked':['TRIANGLE','BOX','SPHERE','CAPSULE','CYLINDER'],'nearby_entity_collisions_checked':checked_props,'in_game_test':False,'routes':routes,'full_floor_scan':{'spacing_m':.25,'scanned':scanned,'free_custom_geometry_samples':eligible,'unexplained_native_obstacles':grid,'passed':not grid},'floor_coverage':coverage,'passed':all(q['passed'] for q in routes.values()) and not grid and all(q['passed'] for q in coverage)}
result['collision_files_checked']=[p.name for p in collision_sources]
(W/('verificacao_antes_limpeza.json' if BASELINE else 'verificacao_encaixe.json')).write_text(json.dumps(result,indent=2))
for name,q in routes.items():
 print(name,'PASS' if q['passed'] else 'FAIL',q['blocked'][:2],q['missing_floor'][:2],flush=True)
print('FULL_FLOOR_SCAN',scanned,'points;',eligible,'free;',len(grid),'unexplained blocks',grid[:8],flush=True)
print('FLOOR_COVERAGE',coverage,flush=True)
if not BASELINE:assert result['passed'],'Walking checks failed'
