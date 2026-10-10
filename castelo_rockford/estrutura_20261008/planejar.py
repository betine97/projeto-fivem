import sys,json,math
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(R/'casa_vinewood/work/pydeps')]
import numpy as np
from shapely.geometry import Polygon,Point,box,LineString,mapping
from shapely import affinity
from shapely.ops import unary_union,nearest_points
from PIL import Image,ImageDraw
anchor=[-944.5,206.5,66.47];angle=-30.
def world(p):return affinity.translate(affinity.rotate(p,angle,origin=(0,0)),*anchor[:2])
foot=unary_union([box(-14,-10,14,10)]+[Point(x,y).buffer(3.1,quad_segs=10) for x in [-11.5,11.5] for y in [-8,8]])
# The drive bypasses the stairs with a continuous five metre carriageway.
obstacle=unary_union([foot,box(-4.25,-14.35,4.25,-9.8)])
inner=obstacle.buffer(1.3,quad_segs=12);outer=obstacle.buffer(6.3,quad_segs=12)
ring=world(outer.difference(inner));center=world(obstacle.buffer(3.8,quad_segs=12)).exterior
gate=(-970.22,184.22);join=nearest_points(center,Point(-959,194))[0]
approach=LineString([gate,(-976,186.0),(-977,188.0),(-974,190.0),(-970,190.5),(-965,191.0),tuple(join.coords[0])])
stem=approach.buffer(2.5,quad_segs=12,cap_style=2)
# Rear garage retains its original world placement and four stalls.
oldgarage=affinity.translate(affinity.rotate(box(6.64,17,20.36,25),60,origin=(0,0)),-946,207)
garageapron=affinity.translate(affinity.rotate(box(6.5,14.6,20.5,17.05),60,origin=(0,0)),-946,207)
road=unary_union([ring,stem,garageapron])
apron=world(inner.difference(foot))
affected=unary_union([world(outer.buffer(.38)),stem.buffer(.12),oldgarage.buffer(.05),garageapron])
d=json.loads((R/'castelo_rockford/modelo/quadra_original_local.json').read_text());court=affinity.translate(affinity.rotate(unary_union([Polygon(p) for p in d['polygon']]),60,origin=(0,0)),-946,207)
assert road.intersection(court.buffer(.45)).area<.001
assert world(foot).intersection(court).area<.001
terrain=np.load(P/'terreno.npz');tri=terrain['triangles'];ids=terrain['shaders'];ground=tri[np.isin(ids,[4,6,7,9,19])]
norm=np.cross(ground[:,1]-ground[:,0],ground[:,2]-ground[:,0]);ground=ground[abs(norm[:,2])>.1]
def original_height(x,y):
 pp=np.array([x,y]);a=ground[:,0,:2];e=ground[:,1,:2]-a;f=ground[:,2,:2]-a;v=pp-a;det=e[:,0]*f[:,1]-e[:,1]*f[:,0];ok=abs(det)>1e-8
 u=np.zeros(len(a));w=u.copy();u[ok]=(v[ok,0]*f[ok,1]-v[ok,1]*f[ok,0])/det[ok];w[ok]=(e[ok,0]*v[ok,1]-e[ok,1]*v[ok,0])/det[ok]
 mask=ok&(u>=-1e-5)&(w>=-1e-5)&(u+w<=1.00001)
 zz=ground[:,0,2]+u*(ground[:,1,2]-ground[:,0,2])+w*(ground[:,2,2]-ground[:,0,2]);return float(max(zz[mask])) if mask.any() else None
gateheight=original_height(*gate)
if gateheight is None:
 candidates=[]
 for dx in np.linspace(-1.5,1.5,13):
  for dy in np.linspace(-1.5,1.5,13):
   h=original_height(gate[0]+dx,gate[1]+dy)
   if h is not None:candidates.append((dx*dx+dy*dy,h))
 assert candidates,'No measured ground near gate'
 gateheight=min(candidates)[1]
# Smooth height ramp along the existing street entrance, then level loop.
g=np.array(gate);end=np.array(join.coords[0]);length=approach.length
near=approach.intersection(ring.buffer(2.6))
if not near.is_empty:
 points=[]
 for part in near.geoms if hasattr(near,'geoms') else [near]:
  if hasattr(part,'coords'):points.extend(part.coords)
 length=min(approach.project(Point(q)) for q in points)
 end=np.array(approach.interpolate(length).coords[0])
def height(x,y):
 t=float(np.clip(approach.project(Point(x,y))/length,0,1));return gateheight+.03+(66.5-gateheight-.03)*t
samples=[]
for t in np.linspace(0,1,11):
 pt=np.array(approach.interpolate(t*length).coords[0]);samples.append([*pt,height(*pt)])
report={'anchor':anchor,'rotation':angle,'front_rotation_change':-90,'road_width_m':5,'gate_height':gateheight,'ramp_length_m':length,'ramp_slope_percent':100*(66.5-gateheight-.03)/length,'road':mapping(road),'apron':mapping(apron),'affected':mapping(affected),'footprint':mapping(world(foot)),'court':mapping(court),'centerline':mapping(center),'approach':mapping(approach),'garage_original_world_preserved':True,'ramp_samples':samples,'grade_gate':gate,'grade_end':end.tolist()}
(P/'implantacao.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
im=Image.open(P/'implantacao_diagnostico.png');dr=ImageDraw.Draw(im)
def xy(p):return ((p[0]+1000)*14,1050-(p[1]-172)*14)
def fill(sh,color):
 for q in sh.geoms if hasattr(sh,'geoms') else [sh]:
  dr.polygon([xy(p) for p in q.exterior.coords],fill=color)
  for hole in q.interiors:dr.polygon([xy(p) for p in hole.coords],fill='#ece4d3')
fill(road,'#59656b');fill(world(foot),'#d4c5a4');dr.line([xy(p) for p in center.coords],fill='#edda8d',width=2)
dr.line([xy(p) for p in approach.coords],fill='#edda8d',width=3)
for name,poly in [('FRENTE / X',world(Point(0,-12))),('GARAGEM',oldgarage.centroid)]:dr.text(xy(poly.coords[0]),name,fill='#921010')
im.save(P/'trajeto_planejado.png')
print('PLANNED rotation',angle,'anchor',anchor,'road width 5m; ramp slope',round(report['ramp_slope_percent'],2),'court preserved')
