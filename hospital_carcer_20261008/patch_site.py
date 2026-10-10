from locate import *
import copy,hashlib
sys.path[:0]=[str(R/'casa_vinewood/work/pydeps'),str(R/'laboratorio_fivem/work')]
from shapely.geometry import Polygon,Point,MultiPoint
from shapely import constrained_delaunay_triangles
from szio import jenkhash
from szio.gta5.bounds import *
from szio.gta5.maps import *
from szio.types import Vector
import pymateria.gta5.gen8 as g8
O=P/'package/stream';TARGET=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
# Use patched game metadata where present, then preserve already-installed map edits.
sources=json.loads((P/'all_extra_sources.json').read_text())
for s in sources:
 if 'patchday2ng' in s and Path(s.split('|')[-1]).name.startswith('bh1_22'):
  parts=s.split('|');(N/Path(parts[-1]).name).write_bytes(archive(parts).read_bytes(parts[-1]))
for f in N.glob('*.ymap'):
 for directory in ['cidade_castelo_livre','cidade_mansao']:
  installed=R/'server-data/resources'/directory/'stream'/f.name
  if installed.exists():f.write_bytes(installed.read_bytes())
es=[]
for f in N.glob('*.ymap'):
 try:a=try_load_asset(f)
 except Exception:continue
 es.extend(dict(name=str(e.archetype_name),pos=list(e.position),map=f.name,index=i) for i,e in enumerate(a.entities))
pos={e['name']:np.array(e['pos']) for e in es}
foot=Polygon(json.loads((P/'plaza.json').read_text())['polygon']).buffer(-.035,join_style=2)
lo=np.r_[foot.bounds[:2],31.40];hi=np.r_[foot.bounds[2:],110.0];planes=[]
for cell in constrained_delaunay_triangles(foot).geoms:
 pts=np.array(cell.exterior.coords)[:3];pp=[]
 if np.linalg.det(np.stack([pts[1]-pts[0],pts[2]-pts[0]]))<0:pts=pts[::-1]
 for a,b in zip(pts,np.roll(pts,-1,axis=0)):
  n=np.array([b[1]-a[1],a[0]-b[0],0.]);pp.append((n,float(n[:2]@a)))
 pp.extend([(np.array([0.,0.,-1.]),-lo[2]),(np.array([0.,0.,1.]),hi[2])]);planes.append((np.r_[pts.min(0),lo[2]],np.r_[pts.max(0),hi[2]],pp))
exec((P/'patch_functions.py').read_text())
report={'render':[],'maps':[],'collision':[],'occlusion':[],'preserved_existing':[],'in_game_verified':False}
def raw_preserve(f):
 cls=g8.DrawableDictionary if f.suffix=='.ydd' else g8.Drawable
 old=cls.import_rsc(f).result;new=cls.import_rsc(O/f.name).result
 pairs=[(new,old)] if f.suffix=='.ydr' else [(v,old.drawables[k]) for k,v in new.drawables.items()]
 for a,b in pairs:
  assert len(a.shader_group.shaders)==len(b.shader_group.shaders)
  for s,t in zip(a.shader_group.shaders,b.shader_group.shaders):s.basis_shader=t.basis_shader;s.basis_material=t.basis_material
  # Shared models keep their original lights, outside the demolished block.
  if f.stem not in exclusive:a.lights=b.lights
 cls.export_rsc(new,O/f.name)

exclusive={'bh1_22_towerw','bh1_22_towerw_dtl','bh1_22_emissive_22','bh1_22_emissivesign','bh1_22_base','bh1_22_overlays','bh1_22_overlays_01','bh1_22_overlays_02','bh1_22_overlays_03','bh1_22_overlays_04','bh1_22_doorfizz_1','bh1_22_doorfizz_2'}
for name in sorted(exclusive|{'bh1_22_fakeint'}):
 f=N/(name+'.ydr');a=try_load_asset(f);n,total=patch_drawable(a,pos[name],force=name in exclusive)
 if name in exclusive:a.bounds=None;a.lights=[]
 if n:
  save_asset(a,TARGET,O,name);raw_preserve(f);report['render'].append(dict(file=f.name,removed_triangles=n,before=total));print('PATCH_HD',f.name,n,flush=True)

# LOD dictionaries are shared with the hotel and distant Beverly blocks.
for filename in ['bh1_22_slod1_children.ydd','bh1_22_emissive_slod_children.ydd','bh1_lod_17_18_22_children.ydd','bh1_lod_slod3_children.ydd','bh1_lod_emissive_6_21_slod3_children.ydd','bh1_lod_emissive_6_20_slod3_children.ydd']:
 f=N/filename
 existing=R/'server-data/resources/cidade_castelo_livre/stream'/filename
 if existing.exists():f.write_bytes(existing.read_bytes());report['preserved_existing'].append(filename)
 a=try_load_asset(f);changes=[]
 for k,d in a.drawables.items():
  name=next((n for n in pos if jenkhash.name_to_hash(n)==jenkhash.name_to_hash(k)),None)
  if not name:continue
  if filename=='bh1_lod_slod3_children.ydd' and name!='bh1_lod_17_18_22':continue
  n,total=patch_drawable(d,pos[name],force=name in {'bh1_22_b01_lod','bh1_22_emissive_22_lod','bh1_22_base_lod'})
  if n:changes.append(dict(name=name,removed_triangles=n,before=total));d.bounds=None
 if changes:
  save_asset(a,TARGET,O,f.stem);raw_preserve(f);report['render'].append(dict(file=f.name,drawables=changes));print('PATCH_LOD',f.name,changes,flush=True)

for filename in ['bh1_lod_slod3.ydr','bh1_lod_emissive_6_21_slod3.ydr','bh1_lod_emissive_6_20_slod3.ydr']:
 f=N/filename
 existing=R/'server-data/resources/cidade_castelo_livre/stream'/filename
 if existing.exists():f.write_bytes(existing.read_bytes());report['preserved_existing'].append(filename)
 a=try_load_asset(f);n,total=patch_drawable(a,pos[f.stem])
 if n:
  save_asset(a,TARGET,O,f.stem);raw_preserve(f);report['render'].append(dict(file=f.name,removed_triangles=n,before=total));print('PATCH_AGGREGATE',f.name,n,flush=True)

# Remove only disposable objects belonging to the old hospital grounds. Main
# structural entities remain with empty geometry so parent indices stay stable.
for f in N.glob('*bh1_22*.ymap'):
 a=try_load_asset(f);keep=[];removed=[]
 for i,e in enumerate(a.entities):
  name=str(e.archetype_name);v=np.array(e.position)
  if not name.startswith('bh1_') and e.parent_index==-1 and foot.contains(Point(v[:2])) and v[2]>31.3:
   removed.append(dict(index=i,name=name,pos=v.tolist()));continue
  keep.append(e)
 if removed:a.entities=keep;save_asset(a,TARGET,O,f.stem);report['maps'].append(dict(file=f.name,removed=removed))

faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
signs=np.array([(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
def box_corners(q):
 v1,v2,v3,v4=q;center=np.mean(q,axis=0);a1=((v3+v4)-(v1+v2))*.5;edges=np.array([a1,v3-a1-v1,v4-a1-v1])
 if np.linalg.det(edges)<0:edges=edges[[0,2,1]]
 return center+signs@edges*.5
for f in sorted(N.glob('*bh1_22_0.ybn')):
 a=try_load_asset(f);changes=[]
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
    if foot.intersects(MultiPoint(v[:,:2]).convex_hull.buffer(pad+.001)):changes.append(dict(path=path,index=j,type=p.primitive_type.name));continue
    new.append(p);continue
   surface=[v] if p.primitive_type==BoundPrimitiveType.TRIANGLE else [box_corners(v)[list(ids)] for ids in faces];out=[];hit=False
   for face in surface:
    pieces,h=cut(list(face));hit|=h
    for pp in pieces:out.extend(tris(pp))
   if not hit:new.append(p);continue
   changes.append(dict(path=path,index=j,type=p.primitive_type.name))
   for t in out:
    local=(np.c_[t,np.ones(3)]@inv)[:,:3];start=len(vv);vv.extend(BoundVertex(Vector(c),vv[0].color if vv else None) for c in local);new.append(BoundPrimitive.new_triangle(start,start+1,start+2,p.material,p.material_color))
  b.geometry_primitives=new;assert len(vv)<65535
 visit(a)
 def prune(b):
  if hasattr(b,'children'):
   b.children=[prune(c) if c else None for c in b.children]
   if not any(c for c in b.children):return None
  if hasattr(b,'geometry_primitives') and not b.geometry_primitives:return None
  return b
 a=prune(a)
 assert a is not None,'Root collision must keep neighboring ground'
 if changes:save_asset(a,TARGET,O,f.stem);report['collision'].append(dict(file=f.name,changes=len(changes)));print('PATCH_COLLISION',f.name,len(changes),flush=True)

for f in N.glob('*bh1_occl*.ymap'):
 a=try_load_asset(f);count=0;boxes=[];models=[]
 for b in a.box_occluders:
  c=np.array(b.center);sz=np.array(b.size)*.5
  if foot.intersects(Point(c[:2]).buffer(float(np.linalg.norm(sz[:2])))) and c[2]+sz[2]>lo[2] and c[2]-sz[2]<hi[2]:count+=1
  else:boxes.append(b)
 for m in a.model_occluders:
  ts=[];changed=False
  for ids in m.indices:
   pp,h=cut(list(m.vertices[ids].astype(float)));changed|=h
   for p in pp:ts.extend(tris(p))
  if not changed:models.append(m);continue
  count+=1
  for start in range(0,len(ts),70):
   xyz=np.array(ts[start:start+70]).reshape(-1,3);v,inv=np.unique(np.round(xyz,5),axis=0,return_inverse=True);models.append(MapModelOccluder(m.flags,v.astype(np.float32),inv.reshape(-1,3).astype(np.uint8)))
 if count:a.box_occluders=boxes;a.model_occluders=models;save_asset(a,TARGET,O,f.stem);report['occlusion'].append(dict(file=f.name,volumes=count));print('PATCH_OCCLUSION',f.name,count,flush=True)
(P/'site_patch_report.json').write_text(json.dumps(report,indent=2));print('SITE_PATCHED',flush=True)
