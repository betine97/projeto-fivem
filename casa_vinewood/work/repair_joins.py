"""Continuous facade lining with native window openings and closed floor joins.

This revision works on the accepted scene, preserving the patched walking routes.
Each lining section is a closed prism; matching mitered corners overlap and do not
depend on the original exterior's one-sided, independently offset triangles.
"""
import bpy,sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps')]
import numpy as np
from shapely.geometry import Polygon,Point,box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
bpy.ops.wm.open_mainfile(filepath=str(W/'backup_antes_frestas_render/mansao_encaixada.blend'))
spec=json.loads((W/'encaixe_fachada.json').read_text())
cols={k:next(c for c in bpy.data.collections if c.name.startswith(p)) for k,p in [('outer','01_'),('ground','02_'),('upper','03_'),('slabs','04_'),('stairs','05_'),('ceil','06_')]}
for c in cols.values():c.hide_viewport=False;c.hide_render=False
old=next(o for o in cols['outer'].objects if o.name=='Revestimento da fachada nativa')
mat=old.data.materials[0];bpy.data.objects.remove(old,do_unlink=True)
glass=next(o for o in cols['outer'].objects if o.name.startswith('Vidros'))
glass.data.calc_loop_triangles();windows=[]
for t in glass.data.loop_triangles:
 p=np.array([glass.matrix_world@glass.data.vertices[v].co for v in t.vertices]);n=np.cross(p[1]-p[0],p[2]-p[0]);length=np.linalg.norm(n)
 if length<.2 or abs(n[2]/length)>.2:continue
 axis=int(np.argmax(np.abs(n)));axes=[i for i in range(3) if i!=axis]
 if np.ptp(p[:,axes],axis=0).min()<.15:continue
 windows.append((axis,float(p[:,axis].mean()),Polygon(p[:,axes])))
def mesh(name,vs,fs,col,material):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();me.materials.append(material)
 ob=bpy.data.objects.new(name,me);col.objects.link(ob);return ob
def pieces(p):
 return [p] if p.geom_type=='Polygon' else [q for q in getattr(p,'geoms',[]) if q.geom_type=='Polygon']
def panel(name,p,axis,front,back):
 """Extrude a polygon in (horizontal coordinate, Z) along its fixed axis."""
 axes=[i for i in range(3) if i!=axis];vs=[];fs=[]
 def co(q,depth):
  v=[0.,0.,0.];v[axis]=depth;v[axes[0]]=q[0];v[2]=q[1];return v
 for t in constrained_delaunay_triangles(p).geoms:
  pts=list(t.exterior.coords)[:-1]
  for depth,reverse in [(front,False),(back,True)]:
   q=pts[::-1] if reverse else pts;i=len(vs);vs.extend(co(v,depth) for v in q);fs.append(tuple(range(i,i+3)))
 for ring in [p.exterior,*p.interiors]:
  pts=list(ring.coords)
  for a,b in zip(pts,pts[1:]):
   i=len(vs);vs.extend([co(a,front),co(b,front),co(b,back),co(a,back)]);fs.append((i,i+1,i+2,i+3))
 ob=mesh(name,vs,fs,cols['outer'],mat)
 # Face winding: cap normals follow the fixed axis and the signed thickness.
 # Recalculate on a welded copy of every closed panel before export.
 import bmesh
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
 return ob
G=Polygon(spec['ground_polygon']);U=Polygon(spec['upper_polygon']);panels=[]
for label,poly,z0,z1 in [('terreo',G,-.815,2.568),('superior',U,2.558,6.510)]:
 inner=list(poly.buffer(-.035,join_style=2).exterior.coords)[:-1]
 outer=list(poly.buffer(.025,join_style=2).exterior.coords)[:-1]
 assert len(inner)==len(outer)
 for i,(a,b) in enumerate(zip(inner,inner[1:]+inner[:1])):
  oa,ob=outer[i],outer[(i+1)%len(outer)]
  axis=0 if abs(a[0]-b[0])<.00001 else 1;h=1-axis
  front=a[axis];back=oa[axis]
  h0=min(a[h],b[h],oa[h],ob[h]);h1=max(a[h],b[h],oa[h],ob[h])
  region=box(h0,z0,h1,z1);holes=[]
  for wa,plane,shape in windows:
   if wa==axis and abs(plane-front)<.52:holes.append(shape.buffer(.001,join_style=2))
  for lo,hi in spec['door_cuts']:
   if min(front,back)<=hi[axis] and max(front,back)>=lo[axis]:holes.append(box(lo[h],lo[2],hi[h],hi[2]))
  if holes:region=region.difference(unary_union(holes))
  for j,q in enumerate(pieces(region)):
   if q.area>.00001:
    name=f'Revestimento continuo {label} {i:02d} {j}'
    panel(name,q,axis,front,back);panels.append({'name':name,'axis':axis,'front':front,'back':back,'area_m2':q.area,'bounds':list(q.bounds)})
def endpoints_wall(ob,poly,key):
 """Extend only the old nominal room perimeter endpoints to the real shell."""
 pts=np.array([ob.matrix_world@v.co for v in ob.data.vertices]);lo=pts.min(0);hi=pts.max(0);axis=0 if hi[0]-lo[0]>.22 else 1
 fixed=(lo[1-axis]+hi[1-axis])/2
 from shapely.geometry import LineString
 ln=LineString([(-30,fixed),(30,fixed)]) if axis==0 else LineString([(fixed,-30),(fixed,30)])
 cut=poly.buffer(-.025,join_style=2).intersection(ln)
 ranges=[q.bounds for q in ([cut] if cut.geom_type=='LineString' else getattr(cut,'geoms',[]))]
 for bounds in ranges:
  start,end=bounds[axis],bounds[axis+2]
  if not (start-.02 <= (lo[axis]+hi[axis])/2 <= end+.02):continue
  # These are the endpoints of the original approximate floor plan. Internal
  # door jambs and deliberate openings are never stretched by proximity alone.
  old_start=float(lo[axis]);old_end=float(hi[axis])
  extend_start=axis==0 and abs(old_start+8.8)<.005
  extend_end=(axis==0 and abs(old_end-13.7)<.005) or (axis==1 and abs(old_end-7.15)<.005)
  if key=='upper' and ob.name.startswith('Quarto 2 lateral vazio'):extend_start=True
  for v in ob.data.vertices:
   world=ob.matrix_world@v.co
   if extend_start and abs(world[axis]-old_start)<.0001:world[axis]=start-.01
   if extend_end and abs(world[axis]-old_end)<.0001:world[axis]=end+.01
   # Slight overlap avoids shader/quantization hairline cracks at floor/ceiling.
   if key=='ground':
    if abs(world.z+ .8)<.001:world.z=-.810
    if abs(world.z-2.558)<.001:world.z=2.575
   else:
    if abs(world.z-2.808)<.001:world.z=2.798
    if abs(world.z-6.488)<.001:world.z=6.510
   v.co=ob.matrix_world.inverted()@world
  break
for key,poly in [('ground',G),('upper',U)]:
 for ob in cols[key].objects:
  if ob.type=='MESH':endpoints_wall(ob,poly,key)
# The room fronts were centered on the void boundary: hide the exposed underside
# with a continuous fascia that overlaps both the slab and the room-wall bottoms.
def cube(name,b):
 x0,x1,y0,y1,z0,z1=b;vs=[(x,y,z) for z in [z0,z1] for y in [y0,y1] for x in [x0,x1]]
 return mesh(name,vs,[(0,2,3,1),(4,5,7,6),(0,1,5,4),(1,3,7,5),(3,2,6,7),(2,0,4,6)],cols['outer'],mat)
cube('Fechamento borda mezanino',(-9.255,6.49,-3.95,-3.75,2.538,2.823))
cube('Fechamento borda quarto sobre sala',(6.30,6.50,-13.285,-3.75,2.538,2.823))
# The old rail retained the study's edge, 1.12m beyond the fitted slab.
for ob in cols['stairs'].objects:
 if ob.name.startswith('Mezanino sala '):ob.location.y+=1.12
bpy.context.scene['status']='Juntas continuas da fachada, divisorias e lajes corrigidas; exportacao e validacao FiveM em andamento.'
cols['ceil'].hide_viewport=True
(W/'revisao_juntas.json').write_text(json.dumps({'panels':panels,'window_masks':len(windows),'wall_thickness_m':.06,'wall_floor_overlap_m':.01,'mezzanine_rail_shift_y_m':1.12,'native_doors_preserved':spec['door_cuts'],'in_game_verified':False},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_encaixada.blend'))
print('CLOSED_JOINS_SAVED',len(panels),'panels',flush=True)
