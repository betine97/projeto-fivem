import sys,json,math,copy,ast,shutil,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];N=R/'server-data/resources/cidade_castelo_livre';O=P/'terrain/stream';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(R/'casa_vinewood/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from shapely.geometry import shape,Polygon,Point,MultiPoint
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
from szio.gta5 import *
from szio.gta5.bounds import *
from szio.gta5.maps import *
from szio.types import Vector
from szio import jenkhash
import pymateria.gta5 as pm
TARGET=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
plan=json.loads((P/'implantacao.json').read_text());foot=shape(plan['affected']);lo=np.array([*foot.bounds[:2],62.9]);hi=np.array([*foot.bounds[2:],92.])
planes=[]
for cell in constrained_delaunay_triangles(foot).geoms:
 pts=np.array(cell.exterior.coords)[:3];pp=[]
 if np.linalg.det(np.stack([pts[1]-pts[0],pts[2]-pts[0]]))<0:pts=pts[::-1]
 for a,b in zip(pts,np.roll(pts,-1,axis=0)):
  n=np.array([b[1]-a[1],a[0]-b[0],0.]);pp.append((n,float(n[:2]@a)))
 pp.extend([(np.array([0,0,-1.]),-lo[2]),(np.array([0,0,1.]),hi[2])]);planes.append((np.r_[pts.min(0),lo[2]],np.r_[pts.max(0),hi[2]],pp))
# Reuse the vetted triangle clipping routines, without running the old build.
code=(R/'castelo_rockford/work/build.py').read_text();tree=ast.parse(code)
needed={'area','tris','split_plane','cut','canonical','patch_drawable','box_corners'}
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name in needed:exec(compile(ast.Module(body=[node],type_ignores=[]),str(P/'clipping'), 'exec'))
faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
signs=np.array([(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
entities=json.loads((R/'castelo_rockford/entities.json').read_text());pos={e['name']:np.array(e['pos']) for e in entities}
report={'render':[],'collision':[],'maps':[],'occlusion':[],'outside_property_unchanged':True,'input_hashes':{str(f.relative_to(N)):hashlib.sha256(f.read_bytes()).hexdigest() for f in N.rglob('*') if f.is_file()}}
shutil.copytree(N,P/'terrain',dirs_exist_ok=True)
def patch_bounds(root):
 changes=[]
 def visit(b,parent=np.eye(4),path=()):
  tx=np.asarray(b.composite_transform)@parent
  for j,c in enumerate(getattr(b,'children',[])):
   if c:visit(c,tx,path+(j,))
  if not hasattr(b,'geometry_primitives'):return
  vv=b.geometry_vertices;inv=np.linalg.inv(tx);new=[]
  for j,p in enumerate(b.geometry_primitives):
   q=np.array([vv[i].co for i in p.vertices]);v=(np.c_[q,np.ones(len(q))]@tx)[:,:3];pad=p.radius or 0
   if np.any(v.max(0)+pad<lo) or np.any(v.min(0)-pad>hi):new.append(p);continue
   if p.primitive_type not in (BoundPrimitiveType.TRIANGLE,BoundPrimitiveType.BOX):
    if foot.intersects(MultiPoint(v[:,:2]).convex_hull.buffer(pad+.001)):changes.append((path,j));continue
    new.append(p);continue
   surfaces=[v] if p.primitive_type==BoundPrimitiveType.TRIANGLE else [box_corners(v)[list(ids)] for ids in faces];out=[];hit=False
   for face in surfaces:
    pieces,h=cut(list(face));hit|=h
    for pp in pieces:out.extend(tris(pp))
   if not hit:new.append(p);continue
   changes.append((path,j))
   for t in out:
    local=(np.c_[t,np.ones(3)]@inv)[:,:3];start=len(vv);vv.extend(BoundVertex(Vector(c),None) for c in local);new.append(BoundPrimitive.new_triangle(start,start+1,start+2,p.material,p.material_color))
  b.geometry_primitives=new
  # Compact vertices: cuts can create duplicates along adjacent triangles.
  used=sorted({int(i) for p in new for i in p.vertices});mapping={old:new for new,old in enumerate(used)}
  b.geometry_vertices=[vv[i] for i in used]
  for p in new:p.vertices=tuple(mapping[int(i)] for i in p.vertices)
  assert len(b.geometry_vertices)<65535
 visit(root);return changes
for f in sorted((N/'stream').glob('*.ydr')):
 a=try_load_asset(f);off=pos.get(f.stem)
 if off is None:continue
 n,total=patch_drawable(a,off)
 # Embedded floor collision uses model-local coordinates.
 if a.bounds:
  original_lo=lo.copy();original_hi=hi.copy();original_planes=planes;lo-=off;hi-=off
  planes=[(c0-off,c1-off,[(normal,k-float(normal@off)) for normal,k in pp]) for c0,c1,pp in original_planes]
  changes=patch_bounds(a.bounds);lo=original_lo;hi=original_hi;planes=original_planes
 else:changes=[]
 if n or changes:
  canonical(a);save_asset(a,TARGET,O,f.stem);report['render'].append({'file':f.name,'triangles_changed':n,'embedded_collision_changed':len(changes)})
  print('TERRAIN_DRAWABLE',f.name,n,flush=True)
for f in sorted((N/'stream').glob('*.ydd')):
 a=try_load_asset(f);changed=[]
 for key,d in a.drawables.items():
  name=next((n for n in pos if jenkhash.name_to_hash(n)==jenkhash.name_to_hash(key)),None)
  if name is None:continue
  n,total=patch_drawable(d,pos[name])
  if n:changed.append((name,n))
 if changed:
  for d in a.drawables.values():canonical(d)
  save_asset(a,TARGET,O,f.stem);report['render'].append({'file':f.name,'drawables':changed});print('TERRAIN_LOD',f.name,flush=True)
for f in sorted((N/'stream').glob('*.ybn')):
 a=try_load_asset(f);changes=patch_bounds(a)
 if changes:save_asset(a,TARGET,O,f.stem);report['collision'].append({'file':f.name,'changed':len(changes)});print('TERRAIN_COLLISION',f.name,len(changes),flush=True)
for f in sorted((N/'stream').glob('*.ymap')):
 a=pm.MapData.import_rsc(f).result
 if 'occl' in f.name:
  # Existing occluders were already pruned for the castle. Keep their opaque data.
  continue
 resolved=try_load_asset(f).entities;retained=[];removed=[]
 for i,e in enumerate(a.entities):
  pt=np.array([e.position.x,e.position.y,e.position.z]);name=str(resolved[i].archetype_name)
  gate_leaf=name in ['prop_lrggate_01_l','prop_lrggate_01_r'] and Point(pt[:2]).distance(Point(*plan['grade_gate']))<4
  in_path=not name.startswith('bh1') and shape(plan['affected']).buffer(-.02).covers(Point(pt[:2])) and 62.9<pt[2]<92
  if gate_leaf or in_path:
   assert e.parent_index==-1 and e.num_children==0
   removed.append({'name':name,'position':pt.tolist()});continue
  retained.append(e)
 if removed:a.entities=retained;pm.MapData.export_rsc(a,O/f.name);report['maps'].append({'file':f.name,'removed':removed});print('TERRAIN_PROPS',f.name,len(removed),flush=True)
(P/'terreno_alteracoes.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('TERRAIN_READY',flush=True)
