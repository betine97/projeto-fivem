"""Replace the approximate envelope by a lining sampled from the native facade."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps'),str(R/'laboratorio_fivem/work')]
import numpy as np
from shapely.geometry import Polygon,Point,box as rect
from shapely import constrained_delaunay_triangles
from clip_geometry import split,subtract_box
bpy.ops.wm.open_mainfile(filepath=str(W/'backup_antes_encaixe/mansao_interior_inicial.blend'))
s=bpy.context.scene
cols={k:next(c for c in bpy.data.collections if c.name.startswith(p)) for k,p in [('outer','01_'),('ground','02_'),('upper','03_'),('slabs','04_'),('stairs','05_'),('ceil','06_')]}
for c in cols.values():c.hide_viewport=False;c.hide_render=False
G=[(-9.271,-12),(-8.270,-12),(-8.270,-13.199),(1.546,-13.199),(1.546,-11.518),(4.722,-11.518),(4.722,-11.666),(6.254,-11.666),(6.254,-14.456),(14.401,-14.456),(14.401,6.341),(13.4,6.341),(13.4,7.54),(3.584,7.54),(3.584,5.859),(1.065,5.859),(1.065,6.007),(-1.123,6.007),(-1.123,9.817),(-9.271,9.817)]
U=[(-9.271,-12),(-8.270,-12),(-8.270,-13.199),(1.546,-13.199),(1.546,-11.518),(4.722,-11.518),(4.722,-11.666),(6.254,-11.666),(6.254,-15.978),(14.401,-15.978),(14.401,6.341),(13.4,6.341),(13.4,7.54),(3.584,7.54),(3.584,5.859),(1.065,5.859),(1.065,6.007),(-1.123,6.007),(-1.123,9.727),(-9.271,9.727)]
polygons=[Polygon(G),Polygon(U)];assert all(p.is_valid for p in polygons)
DOORS=[([5.50,-13.52,-1.05],[7.18,-12.27,1.95]),([-9.55,-5.72,-1.05],[-8.87,-4.62,1.6]),([13.88,-5.72,-1.05],[14.66,-4.62,1.6]),([-6.19,-13.52,-1.05],[-4.87,-12.80,1.6]),([-2.10,6.37,-1.05],[-.35,7.60,1.95])]
wallmat=bpy.data.materials['Parede | branco quente'];woodmat=bpy.data.materials['Escada | madeira'];ceilmat=bpy.data.materials['Teto claro'];metal=bpy.data.materials['Guarda-corpo | grafite']
glass=bpy.data.materials.new('Vidro fachada original');glass.diffuse_color=(.60,.75,.82,.18)
def mesh(name,vs,fs,col,mat):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);me.materials.append(mat);return o
def cube(name,b,col,mat):
 x0,x1,y0,y1,z0,z1=b
 vs=[(x,y,z) for z in [z0,z1] for y in [y0,y1] for x in [x0,x1]]
 return mesh(name,vs,[(0,2,3,1),(4,5,7,6),(0,1,5,4),(1,3,7,5),(3,2,6,7),(2,0,4,6)],col,mat)
def poly_prism(name,p,top,depth,col,mat):
 vs=[];fs=[]
 for t in constrained_delaunay_triangles(p).geoms:
  coords=list(t.exterior.coords)[:-1];a,b,c=coords
  if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<0:coords.reverse()
  i=len(vs);vs.extend((x,y,top) for x,y in coords);fs.append(tuple(range(i,i+3)))
  i=len(vs);vs.extend((x,y,top-depth) for x,y in reversed(coords));fs.append(tuple(range(i,i+3)))
 for ring in [p.exterior,*p.interiors]:
  pts=list(ring.coords)
  for a,b in zip(pts,pts[1:]):
   i=len(vs);vs.extend([(a[0],a[1],top-depth),(b[0],b[1],top-depth),(b[0],b[1],top),(a[0],a[1],top)]);fs.append((i,i+1,i+2,i+3))
 return mesh(name,vs,fs,col,mat)
for key in ['outer','slabs','ceil']:
 for o in list(cols[key].objects):bpy.data.objects.remove(o,do_unlink=True)
# Extend rear room walls to the measured facade and clip every partition footprint.
for key,poly in [('ground',polygons[0]),('upper',polygons[1])]:
 for o in list(cols[key].objects):
  if o.type!='MESH':continue
  pts=np.array([list(o.matrix_world@v.co) for v in o.data.vertices]);lo=pts.min(0);hi=pts.max(0)
  if o.name.startswith('Cozinha lateral') and lo[1]<-11.90:lo[1]=-11.90
  if hi[1]>7.1 and hi[0]<-.65:hi[1]=9.70 if key=='upper' else 9.79
  p=rect(lo[0],lo[1],hi[0],hi[1]).intersection(poly.buffer(-.06,join_style=2))
  name=o.name;mat=o.data.materials[0];bpy.data.objects.remove(o,do_unlink=True)
  if p.is_empty:continue
  for j,q in enumerate(p.geoms if hasattr(p,'geoms') else [p]):
   if q.area>.0001:poly_prism(name+f' ajustada {j}',q,hi[2],hi[2]-lo[2],cols[key],mat)
void=rect(-9.30,-13.3,6.40,-3.85);shaft=rect(-.30,1.65,2.50,5.70)
poly_prism('Piso terreo contorno nativo',polygons[0].buffer(-.025,join_style=2),-.8,.25,cols['slabs'],woodmat)
upper=polygons[1].buffer(-.025,join_style=2).difference(void).difference(shaft)
poly_prism('Laje superior contorno nativo',upper,2.808,.25,cols['slabs'],woodmat)
poly_prism('Teto contorno nativo',polygons[1].buffer(-.025,join_style=2),6.65,.16,cols['ceil'],ceilmat)
# A closed, flush strip connects each true external door to the original deck.
bridges=[('Entrada',(5.50,7.18,-13.52,-12.27,-1.05,-.8)),('Sacada esquerda',(-9.84,-8.87,-5.72,-4.62,-1.05,-.8)),('Sacada direita',(13.88,15.05,-5.72,-4.62,-1.05,-.8)),('Sala deck',(-6.19,-4.87,-13.65,-12.80,-1.05,-.8)),('Fundos',(-2.10,-.35,6.37,7.65,-1.05,-.8))]
for name,b in bridges:cube('Piso continuo '+name,b,cols['slabs'],woodmat)
raw=json.loads((W/'work/all_shell_faces.json').read_text());counts={'native_wall_faces':0,'glass_faces':0}
def carve(polys):
 for lo,hi in DOORS:
  out=[]
  for p in polys:out.extend(subtract_box(p,np.array(lo),np.array(hi))[0])
  polys=out
 return polys
for kind in ['wall','glass']:
 vs=[];fs=[]
 for q in raw:
  mat=q['material'].lower();p=np.array(q['points']);n=np.array(q['normal'])
  isglass='wins' in mat
  if kind=='glass' and not isglass:continue
  if kind=='wall' and (isglass or not any(x in mat for x in ['wall32','wall_brick_32','idwall','doors'])):continue
  if abs(n[2])>.98 or p[:,2].max()<-.8 or p[:,2].min()>6.489:continue
  mid=p.mean(0);pol=polygons[1 if mid[2]>2.808 else 0]
  if pol.boundary.distance(Point(mid[:2]))>.48:continue
  pp=list(p)
  pp=split(pp,2,-.8,False)[0];pp=split(pp,2,6.488,True)[0]
  if len(pp)<3:continue
  # Shift inward only, choosing the normal side with more depth in the footprint.
  pos=Point(mid[:2]+n[:2]*.40);neg=Point(mid[:2]-n[:2]*.40)
  score=lambda pt:pol.boundary.distance(pt)*(1 if pol.covers(pt) else -1)
  inward=n if score(pos)>score(neg) else -n
  for piece in carve([pp]):
   if len(piece)<3:continue
   off=len(vs);vs.extend((v+inward*.035).tolist() for v in piece)
   ids=list(range(off,len(vs)))
   if np.dot(np.cross(np.array(vs[ids[1]])-vs[ids[0]],np.array(vs[ids[2]])-vs[ids[0]]),inward)<0:ids.reverse()
   fs.append(tuple(ids));fs.append(tuple(reversed(ids)))
   counts['glass_faces' if isglass else 'native_wall_faces']+=1
 mesh('Vidros nos vaos nativos' if kind=='glass' else 'Revestimento da fachada nativa',vs,fs,cols['outer'],glass if kind=='glass' else wallmat)
# Close the previous false openings with the actual lining; the native glass supplies its exact locations.
# Surface ramps are separate collision objects; visual treads remain unchanged.
physics=bpy.data.collections.new('09_COLISAO_DE_CAMINHADA (oculta)');s.collection.children.link(physics)
def ramp(name,x0,x1,y0,y1,z0,z1):
 # z1 at y1; all top faces are wound upward.
 v=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z1),(x0,y1,z1),(x0,y0,z0-.22),(x1,y0,z0-.22),(x1,y1,z1-.22),(x0,y1,z1-.22)]
 faces=[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
 if y1<y0:faces=[tuple(reversed(f)) for f in faces]
 o=mesh(name,v,faces,physics,woodmat);o['physics_only']=True
ramp('Rampa fisica lance 1',-.2,1,2.65,5.65,-.8,1.004)
ramp('Rampa fisica lance 2',1.2,2.4,5.65,2.95,1.004,2.808)
# Rebuild mid-landing and upper arrival flush with the ramps; remove their old .18m ledge.
for o in list(cols['stairs'].objects):
 if 'patamar intermediario' in o.name or 'chegada superior' in o.name:bpy.data.objects.remove(o,do_unlink=True)
cube('Escada patamar intermediario',(-.2,2.4,5.65,6.85,.804,1.004),cols['stairs'],woodmat)
cube('Escada chegada superior',(1.2,2.4,2.65,2.95,2.558,2.808),cols['stairs'],woodmat)
physics.hide_render=True;physics.hide_viewport=True
# The native north facade recedes at the stair: translate the whole U stair,
# including its railings and physics, 1.20m south so the landing stays indoors.
for col in [cols['stairs'],physics]:
 for o in col.objects:o.location.y-=1.20
# Move the master-suite entrance away from the relocated stair railing.
for o in list(cols['upper'].objects):
 if o.name.startswith('Suite master lado hall'):bpy.data.objects.remove(o,do_unlink=True)
for name,b in [('Sul',(-1.64,-1.46,1.15,1.50,2.808,6.488)),('Norte',(-1.64,-1.46,2.60,9.70,2.808,6.488)),('Verga',(-1.64,-1.46,1.50,2.60,5.308,6.488))]:
 cube('Suite master lado hall '+name,b,cols['upper'],wallmat)
s['status']='Revestimento derivado da fachada nativa; colisao de caminhada separada. Validacao no jogo pendente.'
spec={'ground_polygon':G,'upper_polygon':U,'door_cuts':DOORS,'levels_native':[-.8,2.808,6.488],'lining':counts,'ground_gross_m2':polygons[0].area,'upper_gross_m2':upper.area,'collision_clearance_buffer_m':.38}
(W/'encaixe_fachada.json').write_text(json.dumps(spec,indent=2))
cols['ceil'].hide_viewport=True
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_encaixada.blend'))
print('FIT_LAYOUT_OK',spec,flush=True)
