import sys,json,math
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(R/'casa_vinewood/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from shapely.geometry import shape,Point
from szio.gta5 import try_load_asset
from szio.gta5.bounds import BoundPrimitiveType
plan=json.loads((P/'implantacao.json').read_text());road=shape(plan['road']);court=shape(plan['court']);line=shape(plan['centerline']);approach=shape(plan['approach']);anchor=np.array(plan['anchor']);a=math.radians(plan['rotation']);rot=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
signs=np.array([(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
def boxcorners(q):
 v1,v2,v3,v4=q;center=np.mean(q,axis=0);a1=((v3+v4)-(v1+v2))*.5;edges=np.array([a1,v3-a1-v1,v4-a1-v1])
 if np.linalg.det(edges)<0:edges=edges[[0,2,1]]
 return center+signs@edges*.5
def walk(b,parent=np.eye(4)):
 tx=np.asarray(b.composite_transform)@parent
 for c in getattr(b,'children',[]):
  if c:yield from walk(c,tx)
 if not hasattr(b,'geometry_primitives'):return
 for p in b.geometry_primitives:
  ps=np.array([b.geometry_vertices[i].co for i in p.vertices]);ps=(np.c_[ps,np.ones(len(ps))]@tx)[:,:3]
  if p.primitive_type==BoundPrimitiveType.TRIANGLE:yield ps
  elif p.primitive_type==BoundPrimitiveType.BOX:
   q=boxcorners(ps)
   for ids in faces:yield q[list(ids)]
tris=[]
for f in (P/'terrain/stream').glob('*.ybn'):tris.extend(walk(try_load_asset(f)))
origin=np.array(json.loads((R/'castelo_rockford/medidas.json').read_text())['origin'])
main=try_load_asset(P/'terrain/stream/bh1_45_plot4a_ter_dcs.ydr')
if main.bounds:tris.extend(t+origin for t in walk(main.bounds))
for f in (P/'package/stream').glob('*.ydr'):
 model=try_load_asset(f)
 if model.bounds:tris.extend(t@rot.T+anchor for t in walk(model.bounds))
tri=np.array(tris);bounds=road.buffer(3).bounds
mask=(tri[:,:,:2].max(1)[:,0]>bounds[0])&(tri[:,:,:2].min(1)[:,0]<bounds[2])&(tri[:,:,:2].max(1)[:,1]>bounds[1])&(tri[:,:,:2].min(1)[:,1]<bounds[3]);tri=tri[mask]
v0=tri[:,0];e1=tri[:,1]-v0;e2=tri[:,2]-v0
authored=np.load(P/'colisoes.npz')['crf_implantacao_arquitetura']@rot.T+anchor
def authored_height(x,y):
 a=authored[:,0,:2];e=authored[:,1,:2]-a;f=authored[:,2,:2]-a;v=np.array([x,y])-a;det=e[:,0]*f[:,1]-e[:,1]*f[:,0];ok=abs(det)>1e-8;u=np.zeros(len(a));w=u.copy();u[ok]=(v[ok,0]*f[ok,1]-v[ok,1]*f[ok,0])/det[ok];w[ok]=(e[ok,0]*v[ok,1]-e[ok,1]*v[ok,0])/det[ok];valid=ok&(u>=-1e-5)&(w>=-1e-5)&(u+w<=1.00001);zz=authored[:,0,2]+u*(authored[:,1,2]-authored[:,0,2])+w*(authored[:,2,2]-authored[:,0,2]);assert valid.any();return float(max(zz[valid]))
def ray(start,direction,max_distance):
 d=np.array(direction,dtype=float);d/=np.linalg.norm(d);h=np.cross(np.broadcast_to(d,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h);inv=np.zeros_like(det);ok=abs(det)>1e-9;inv[ok]=1/det[ok];ss=np.array(start)-v0;u=inv*np.einsum('ij,ij->i',ss,h);q=np.cross(ss,e1);v=inv*(q@d);tt=inv*np.einsum('ij,ij->i',e2,q);valid=ok&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1.000001)&(tt>.004)&(tt<=max_distance)
 return float(np.min(tt[valid])) if valid.any() else None
def height(x,y):
 t=max(0,min(1,approach.project(Point(x,y))/plan['ramp_length_m']));return plan['gate_height']+.03+(66.5-plan['gate_height']-.03)*t
samples=[];checks=0
for route in [line,approach]:
 for distance in np.arange(.5,route.length-.4,.8):
  point=np.array(route.interpolate(distance).coords[0]);a=np.array(route.interpolate(max(0,distance-.1)).coords[0]);b=np.array(route.interpolate(min(route.length,distance+.1)).coords[0]);direction=b-a;direction/=np.linalg.norm(direction);side=np.array([-direction[1],direction[0]])
  for lateral in [-.9,0,.9]:
   xy=point+side*lateral;z=authored_height(*xy);hit=ray([*xy,z+.3],[0,0,-1],.65)
   assert hit is not None and abs(hit-.3)<.018,('wheel ground',distance,lateral,xy.tolist(),z,hit)
   # Vehicle body corridors above the road, with half-width 0.9 m.
   for h in [.55,1.35]:
    body=ray([*xy,z+h],[*direction,0],1.2)
    assert body is None,('vehicle obstruction',distance,lateral,xy.tolist(),body)
   checks+=3
  samples.append([*point,height(*point)])
assert road.intersection(court.buffer(.45)).area<.001
assert shape(plan['footprint']).intersection(court).area<.001
mesh=json.loads((P/'extracao.json').read_text())['objects']
for o in mesh:
 assert 'porta aberta' not in o['name'] and not o['name'].startswith(('Almofada porta','Macaneta bronze'))
 assert not o['name'].startswith(('SUITE ','Equipe E ','Equipe D ','Mesa banquete','Cadeira banquete','Cozinha bancada','Banheiro bancada','Ilha cozinha','Tampo ilha','Base microfone','Copo agua','Tela reuniao'))
report={'passed':True,'road_physics_checks':checks,'route_points':len(samples),'width_m':5,'court_overlap_m2':0,'doors_and_unwanted_furniture_absent':True,'sampled_route':samples,'in_game_verified':False}
(P/'trajeto_verificacao.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('ROAD_VERIFIED',checks,'wheel/body rays; court preserved; no unwanted furniture or doors',flush=True)
