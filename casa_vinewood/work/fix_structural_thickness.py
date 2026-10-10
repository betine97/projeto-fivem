"""Closed architectural solids with consistent outward faces and usable openings."""
import bpy,bmesh,json,sys
from pathlib import Path
from mathutils import Matrix,Vector
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps')]
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
bpy.ops.wm.open_mainfile(filepath=str(W/'backup_antes_espessuras/mansao_encaixada.blend'))
cols={k:next(c for c in bpy.data.collections if c.name.startswith(p)) for k,p in [('outer','01_'),('ground','02_'),('upper','03_'),('slabs','04_'),('stairs','05_'),('ceil','06_')]}
spec=json.loads((W/'encaixe_fachada.json').read_text());rows=[]
for c in cols.values():c.hide_viewport=False
old_panels=[o for o in cols['outer'].objects if o.name.startswith('Revestimento continuo')];assert len(old_panels)==41
mat=old_panels[0].data.materials[0]
for o in old_panels:bpy.data.objects.remove(o,do_unlink=True)
glass=next(o for o in cols['outer'].objects if o.name.startswith('Vidros'));glass.data.calc_loop_triangles();windows=[]
for t in glass.data.loop_triangles:
 p=np.array([glass.matrix_world@glass.data.vertices[v].co for v in t.vertices]);n=np.cross(p[1]-p[0],p[2]-p[0]);length=np.linalg.norm(n)
 if length<.2 or abs(n[2]/length)>.2:continue
 axis=int(np.argmax(abs(n)));axes=[i for i in range(3) if i!=axis]
 if np.ptp(p[:,axes],axis=0).min()<.15:continue
 windows.append((axis,float(p[:,axis].mean()),Polygon(p[:,axes])))
def mesh(name,vs,fs):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();me.materials.append(mat)
 ob=bpy.data.objects.new(name,me);cols['outer'].objects.link(ob);return ob
def panel(name,p,axis,front,back):
 axes=[i for i in range(3) if i!=axis];vs=[];fs=[]
 def co(q,depth):
  v=[0.,0.,0.];v[axis]=depth;v[axes[0]]=q[0];v[2]=q[1];return v
 for t in constrained_delaunay_triangles(p).geoms:
  ps=list(t.exterior.coords)[:-1]
  for depth,reverse in [(front,False),(back,True)]:
   i=len(vs);vs.extend(co(q,depth) for q in (ps[::-1] if reverse else ps));fs.append(tuple(range(i,i+3)))
 for ring in [p.exterior,*p.interiors]:
  ps=list(ring.coords)
  for a,b in zip(ps,ps[1:]):
   i=len(vs);vs.extend([co(a,front),co(b,front),co(b,back),co(a,back)]);fs.append((i,i+1,i+2,i+3))
 return mesh(name,vs,fs)
panels=[]
for label,key,z0,z1 in [('terreo','ground_polygon',-.815,2.568),('superior','upper_polygon',2.358,6.510)]:
 poly=Polygon(spec[key]);inner=list(poly.buffer(-.215,join_style=2).exterior.coords)[:-1];outer=list(poly.buffer(.035,join_style=2).exterior.coords)[:-1];old_inner=list(poly.buffer(-.035,join_style=2).exterior.coords)[:-1]
 assert len(inner)==len(outer)==len(old_inner)
 for i,(a,b) in enumerate(zip(inner,inner[1:]+inner[:1])):
  oa,ob=outer[i],outer[(i+1)%len(outer)];axis=0 if abs(a[0]-b[0])<1e-5 else 1;h=1-axis
  front,back=a[axis],oa[axis];h0=min(a[h],b[h],oa[h],ob[h]);h1=max(a[h],b[h],oa[h],ob[h]);region=box(h0,z0,h1,z1);holes=[]
  # Preserve the accepted native aperture assignment, even though the interior
  # wall face is moving inward. Frame and pane locations remain native.
  for wa,plane,shape in windows:
   if wa==axis and abs(plane-old_inner[i][axis])<.52:holes.append(shape.buffer(.001,join_style=2))
  for lo,hi in spec['door_cuts']:
   if min(front,back)<=hi[axis] and max(front,back)>=lo[axis]:holes.append(box(lo[h],lo[2],hi[h],hi[2]))
  if holes:region=region.difference(unary_union(holes))
  # Native panes contain sub-millimetre bevel segments. Remove this noise
  # before triangulation: almost-collinear slivers have unstable float32
  # normals in Blender and GTA, even when the wall itself is planar.
  region=region.simplify(.0005,preserve_topology=True)
  pieces=[region] if region.geom_type=='Polygon' else [q for q in getattr(region,'geoms',[]) if q.geom_type=='Polygon']
  for j,q in enumerate(pieces):
   if q.area<1e-5:continue
   name=f'Revestimento continuo {label} {i:02d} {j}';o=panel(name,q,axis,front,back);o['structural_thickness_m']=.25
   panels.append(dict(name=name,axis=axis,front=front,back=back,area_m2=q.area,bounds=list(q.bounds)))
for key in ('ground','upper'):
 for ob in cols[key].objects:
  if ob.type!='MESH':continue
  # Apply transforms before measuring and editing, so a local scale can never
  # turn a nominal wall thickness into a visually thinner exported edge.
  ob.data.transform(ob.matrix_world);ob.matrix_world=Matrix.Identity(4)
  pts=np.array([v.co for v in ob.data.vertices]);lo=pts.min(0);hi=pts.max(0);axis=int(np.argmin(hi[:2]-lo[:2]));center=(lo[axis]+hi[axis])*.5;old=float(hi[axis]-lo[axis]);assert .175<old<.185,(ob.name,old)
  for v in ob.data.vertices:v.co[axis]=center+(v.co[axis]-center)*(.20/old)
  ob['structural_thickness_m']=.20
for ob in cols['slabs'].objects:
 if ob.type!='MESH':continue
 ob.data.transform(ob.matrix_world);ob.matrix_world=Matrix.Identity(4)
 low=min(v.co.z for v in ob.data.vertices);top=max(v.co.z for v in ob.data.vertices);depth=.45 if ob.name.startswith('Laje superior') else .30
 for v in ob.data.vertices:
  if abs(v.co.z-low)<1e-4:v.co.z=top-depth
 ob['structural_thickness_m']=depth;ob['walking_level_z']=top
for ob in cols['ceil'].objects:
 if ob.type!='MESH':continue
 ob.data.transform(ob.matrix_world);ob.matrix_world=Matrix.Identity(4);low=min(v.co.z for v in ob.data.vertices);top=max(v.co.z for v in ob.data.vertices)
 for v in ob.data.vertices:
  if abs(v.co.z-low)<1e-4:v.co.z=top-.20
 ob['structural_thickness_m']=.20
# The arrival originally overlapped the upper slab for 20cm, with coincident
# top and underside faces. End it exactly at the stair opening instead; the
# combined walking surface and slab depth stay unchanged, without z-fighting.
arrival=bpy.data.objects['Escada chegada superior']
arrival.data.transform(arrival.matrix_world);arrival.matrix_world=Matrix.Identity(4)
for v in arrival.data.vertices:
 if v.co.y<1.65:v.co.y=1.65
arrival['structural_thickness_m']=.45
processed=[];skipped=[]
for key,col in cols.items():
 for ob in col.objects:
  if ob.type!='MESH' or ob.name.startswith(('Vidros','Caixilhos')):continue
  ob.data.transform(ob.matrix_world);ob.matrix_world=Matrix.Identity(4)
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5);bm.normal_update()
  if any(not e.is_manifold for e in bm.edges):
   skipped.append(ob.name);bm.free();continue
  before=bm.calc_volume(signed=True);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update();after=bm.calc_volume(signed=True);assert after>1e-8,(ob.name,after)
  # Flat normals preserve a crisp masonry edge instead of smoothing it away.
  for f in bm.faces:f.smooth=False
  bm.to_mesh(ob.data);bm.free();ob.data.update();ob['structural_solid']=True
  ps=np.array([v.co for v in ob.data.vertices]);rows.append(dict(name=ob.name,group=key,lo=ps.min(0).tolist(),hi=ps.max(0).tolist(),thickness_m=ob.get('structural_thickness_m'),volume_before_m3=before,volume_after_m3=after,closed=True,outward_faces=True,walking_level_z=ob.get('walking_level_z')));processed.append(ob.name)
assert not skipped,skipped
joints=json.loads((W/'revisao_juntas.json').read_text());joints.update(panels=panels,wall_thickness_m=.25);(W/'revisao_juntas.json').write_text(json.dumps(joints,indent=2))
report=dict(revision='espessuras-solidas-2026-10-07',interior_wall_thickness_m=.20,exterior_wall_thickness_m=.25,ground_floor_thickness_m=.30,upper_floor_thickness_m=.45,roof_slab_thickness_m=.20,solids=rows,solid_count=len(rows),inconsistent_original_volume_count=sum(r['volume_before_m3']<0 for r in rows),window_positions_preserved=True,door_clear_widths_preserved=True,in_game_verified=False)
(W/'espessuras_estruturais.json').write_text(json.dumps(report,indent=2));bpy.context.scene['status']='Paredes internas 20cm, exteriores 25cm, pisos 30/45cm; volumes fechados e faces externas corrigidos.';cols['ceil'].hide_viewport=True
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_encaixada.blend'))
print('STRUCTURAL_SOLIDS_SAVED',len(rows),'solids;',report['inconsistent_original_volume_count'],'incorrect original windings corrected;',len(panels),'facade panels',flush=True)
