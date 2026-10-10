"""Selective removal of the pictured castle; never alter neighboring resources."""
import sys,json,copy,math,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'castelo_rockford';N=W/'originais';O=W/'package/stream';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(R/'casa_vinewood/work/pydeps'),str(R/'laboratorio_fivem/work/pydeps'),str(R/'laboratorio_fivem/work'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from shapely.geometry import Polygon,Point,MultiPoint,box
from shapely.ops import unary_union,triangulate
from shapely import constrained_delaunay_triangles
from szio.gta5 import *
from szio.gta5.bounds import *
from szio.types import Vector
from szio import jenkhash
from clip_geometry import split
TARGET=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
es=[]
for f in N.glob('*.ymap'):
 a=try_load_asset(f)
 es.extend(dict(name=str(e.archetype_name),pos=list(e.position),map=f.name,index=i) for i,e in enumerate(a.entities))
pos={e['name']:np.array(e['pos']) for e in es}
source=try_load_asset(N/'bh1_45_plot4a_ter_dcs.ydr');origin=pos['bh1_45_plot4a_ter_dcs'];floor=66.47
roof=[]
for m in source.models[LodLevel.HIGH]:
 for g in m.geometries:
  if g.shader_index!=22:continue
  v=g.vertex_buffer['Position']+origin
  roof.extend(Polygon(t[:,:2]) for t in v[g.index_buffer.reshape(-1,3)] if Polygon(t[:,:2]).area>.00001)
roof_union=unary_union(roof)
# The front balcony and connecting porch occupy the recesses between roofs.
# Clear that envelope too, so no supporting arches or garage returns remain.
foot=unary_union([roof_union.convex_hull.buffer(.45,join_style=2),box(-964.0,189.8,-940.0,208.0)]).simplify(.035,preserve_topology=True)
# A roof terrace may have small holes. They belong to the building too.
foot=unary_union([Polygon(p.exterior) for p in (list(foot.geoms) if hasattr(foot,'geoms') else [foot])])
lo=np.array([*foot.bounds[:2],floor+.055]);hi=np.array([*foot.bounds[2:],90.0])
cells=list(constrained_delaunay_triangles(foot).geoms)
assert abs(sum(t.area for t in cells)-foot.area)<.01
planes=[]
for cell in cells:
 pts=np.array(cell.exterior.coords)[:3];pp=[]
 if np.linalg.det(np.stack([pts[1]-pts[0],pts[2]-pts[0]]))<0:pts=pts[::-1]
 for a,b in zip(pts,np.roll(pts,-1,axis=0)):
  n=np.array([b[1]-a[1],a[0]-b[0],0.0]);pp.append((n,float(n[:2]@a)))
 pp.extend([(np.array([0,0,-1.]),-lo[2]),(np.array([0,0,1.]),hi[2])]);planes.append((np.r_[pts.min(0),lo[2]],np.r_[pts.max(0),hi[2]],pp))
report={'render':[],'collision':[],'occlusion':[],'maps':[],'in_game_verified':False}
def area(t):return float(np.linalg.norm(np.cross(t[1][:3]-t[0][:3],t[2][:3]-t[0][:3]))*.5)
def tris(poly):
 for i in range(1,len(poly)-1):
  t=np.array([poly[0],poly[i],poly[i+1]])
  if area(t)>1e-7:yield t
def split_plane(poly,n,k):
 inside=[];out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  da=float(n@a[:3]-k);db=float(n@b[:3]-k);ia=da<=1e-7;ib=db<=1e-7
  (inside if ia else out).append(a)
  if ia!=ib:q=a+(b-a)*da/(da-db);inside.append(q);out.append(q)
 return inside,out
def cut(poly):
 xyz=np.array(poly)[:,:3]
 if np.any(xyz.max(0)<lo) or np.any(xyz.min(0)>hi):return [poly],False
 pieces=[poly];changed=False
 for c0,c1,pp in planes:
  new=[]
  for p in pieces:
   xyz=np.array(p)[:,:3]
   if np.any(xyz.max(0)<c0) or np.any(xyz.min(0)>c1):new.append(p);continue
   rem=p;outside=[]
   for n,k in pp:
    rem,out=split_plane(rem,n,k)
    if len(out)>=3:outside.append(out)
    if len(rem)<3:break
   if len(rem)>=3 and sum(area(t) for t in tris(rem))>1e-7:new.extend(outside);changed=True
   else:new.append(p)
  pieces=new
 return pieces,changed
def canonical(a):
 for s in a.shader_group.shaders:s.name=Path(s.preset_filename).stem
def patch_drawable(a,offset,force=False,main=False):
 changed=0;before=0
 for ms in a.models.values():
  for m in ms:
   geoms=[]
   for g in m.geometries:
    vb=g.vertex_buffer;names=vb.dtype.names;oldtri=g.index_buffer.reshape(-1,3);before+=len(oldtri);extra=[];idx=[]
    # Exclusive castle/garage materials include all trim, windows and roof.
    exclusive=force or (main and g.shader_index in [14,16,18,19,20,22])
    for ids in oldtri:
     if exclusive:changed+=1;continue
     poly=[np.r_[row['Position'].astype(float)+offset,np.concatenate([np.asarray(row[n]).reshape(-1).astype(float) for n in names if n!='Position'])] for row in vb[ids]]
     parts,hit=cut(poly)
     if not hit:idx.extend(map(int,ids));continue
     changed+=1
     for p in parts:
      for t in tris(p):
       start=len(vb)+len(extra)
       for v in t:
        row=np.zeros((),dtype=vb.dtype);row['Position']=v[:3]-offset;k=3
        for n in names:
         if n=='Position':continue
         dst=np.asarray(row[n]);q=v[k:k+dst.size];k+=dst.size
         if np.issubdtype(dst.dtype,np.integer):q=np.clip(np.rint(q),0,np.iinfo(dst.dtype).max)
         if n=='Normal' and np.linalg.norm(q)>0:q/=np.linalg.norm(q)
         row[n]=q.reshape(dst.shape)
        extra.append(row)
       idx.extend([start,start+1,start+2])
    if idx:
     # Compact unused vertices after the cut, keeping indices inside 16 bits.
     allvb=np.concatenate([vb,np.asarray(extra,dtype=vb.dtype)]) if extra else vb
     used,inv=np.unique(idx,return_inverse=True);assert len(used)<65535
     g.vertex_buffer=allvb[used];g.index_buffer=inv.astype(np.uint16);geoms.append(g)
   m.geometries=geoms
 a.models={lod:[m for m in ms if m.geometries] for lod,ms in a.models.items() if any(m.geometries for m in ms)}
 if changed:canonical(a)
 return changed,before
def fill_ground(a):
 flat=[]
 for m in source.models[LodLevel.HIGH]:
  for g in m.geometries:
   vs=g.vertex_buffer['Position']+origin
   for t in vs[g.index_buffer.reshape(-1,3)]:
    n=np.cross(t[1]-t[0],t[2]-t[0]);length=np.linalg.norm(n)
    if length and n[2]/length>.8 and abs(t[:,2].mean()-floor)<.025 and np.ptp(t[:,2])<.02:
     p=Polygon(t[:,:2])
     if p.area>.000001:flat.append(p)
 missing=foot.difference(unary_union(flat).buffer(.008)) if flat else foot
 geom=copy.deepcopy(source.models[LodLevel.HIGH][0].geometries[6]);vb=geom.vertex_buffer
 # Fit the original planar UV mapping, preserving the surrounding tile scale.
 world=vb['Position'].astype(float)+origin;basis=np.c_[world[:,:2],np.ones(len(world))];uv=np.linalg.lstsq(basis,vb['TexCoord0'],rcond=None)[0]
 vertices=[];indices=[]
 for t in constrained_delaunay_triangles(missing).geoms:
  pts=np.array(t.exterior.coords)[:3]
  if np.linalg.det(np.stack([pts[1]-pts[0],pts[2]-pts[0]]))<0:pts=pts[::-1]
  for p in pts:
   row=vb[0].copy();row['Position']=np.r_[p,floor]-origin;row['Normal']=[0,0,1];row['TexCoord0']=np.r_[p,1]@uv;row['Tangent']=[1,0,0,1];vertices.append(row)
  indices.extend(range(len(vertices)-3,len(vertices)))
 geom.vertex_buffer=np.asarray(vertices,dtype=vb.dtype);geom.index_buffer=np.asarray(indices,dtype=np.uint16)
 a.models[LodLevel.HIGH][0].geometries.append(geom)
 # Add the same walkable plane to embedded bounds, within the existing model.
 b=AssetBoundBvh();b.composite_collision_type_flags=CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_VEHICLE|CollisionFlags.MAP_TYPE_WEAPON;b.composite_collision_include_flags=CollisionFlags(0xffffffff)
 b.geometry_vertices=[BoundVertex(Vector(p),None) for p in geom.vertex_buffer['Position']]
 b.geometry_primitives=[BoundPrimitive.new_triangle(*map(int,ids),CollisionMaterial.from_packed(1)) for ids in geom.index_buffer.reshape(-1,3)]
 v=geom.vertex_buffer['Position'];v0,v1=v.min(0),v.max(0);b.bb_min=Vector(v0);b.bb_max=Vector(v1);b.centroid=Vector((v0+v1)/2);b.cg=b.centroid;b.radius_around_centroid=float(np.linalg.norm(v1-v0)/2);b.margin=.001
 comp=AssetBoundComposite(children=[b]);comp.bb_min=b.bb_min;comp.bb_max=b.bb_max;comp.centroid=b.centroid;comp.cg=b.cg;comp.radius_around_centroid=b.radius_around_centroid;a.bounds=comp
 report['ground_fill']={'area_m2':missing.area,'triangles':len(indices)//3,'z':floor}
names=['bh1_45_plot4a_ter_dcs','bh1_45_plot4a_d2_1','bh1_45_plot4a_d2_2','bh1_45_plot4a_d2_3','bh1_45_em_c']
for name in names:
 a=try_load_asset(N/(name+'.ydr'));n,total=patch_drawable(a,pos[name],force=name=='bh1_45_em_c',main=name==names[0])
 if n:
  if name==names[0]:fill_ground(a)
  save_asset(a,TARGET,O,name);assert try_load_asset(O/(name+'.ydr'));report['render'].append(dict(file=name+'.ydr',cut=n,before=total));print('RENDER',name,n,flush=True)
# Patch LOD and SLOD dictionaries in place, retaining all other drawables.
for f in [N/'bh1_45_slod1_children.ydd',N/'bh1_45_em_slod_children.ydd',N/'bh1_lod_45_48_children.ydd',N/'bh1_lod_slod3_children.ydd']:
 a=try_load_asset(f);changes=[]
 for k,d in a.drawables.items():
  name=next((n for n in pos if jenkhash.name_to_hash(n)==jenkhash.name_to_hash(k)),None)
  if not name or (f.name=='bh1_lod_slod3_children.ydd' and name!='bh1_lod_45_48'):continue
  n,total=patch_drawable(d,pos[name],force=name=='bh1_45_em_c_lod')
  if n:changes.append(dict(name=name,cut=n,before=total))
 # Unmodified shaders must keep their native hash through this exporter too.
 if changes:
  for d in a.drawables.values():canonical(d)
  save_asset(a,TARGET,O,f.stem);assert try_load_asset(O/f.name);report['render'].append(dict(file=f.name,drawables=changes));print('LOD',f.name,changes,flush=True)
faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
signs=np.array([(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
def box_corners(q):
 v1,v2,v3,v4=q;center=np.mean(q,axis=0);a1=((v3+v4)-(v1+v2))*.5;edges=np.array([a1,v3-a1-v1,v4-a1-v1])
 if np.linalg.det(edges)<0:edges=edges[[0,2,1]]
 return center+signs@edges*.5
for f in sorted(N.glob('*bh1_45_[0-3].ybn')):
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
    shape=MultiPoint(v[:,:2]).convex_hull.buffer(pad+.001)
    if foot.intersects(shape):changes.append(dict(path=path,index=j,type=p.primitive_type.name));continue
    new.append(p);continue
   surface=[v] if p.primitive_type==BoundPrimitiveType.TRIANGLE else [box_corners(v)[list(ids)] for ids in faces];out=[];hit=False
   for face in surface:
    pieces,h=cut(list(face));hit|=h
    for pp in pieces:out.extend(tris(pp))
   if not hit:new.append(p);continue
   changes.append(dict(path=path,index=j,type=p.primitive_type.name))
   for t in out:
    local=(np.c_[t,np.ones(3)]@inv)[:,:3];start=len(vv);vv.extend(BoundVertex(Vector(c),None) for c in local);new.append(BoundPrimitive.new_triangle(start,start+1,start+2,p.material,p.material_color))
  b.geometry_primitives=new;assert len(vv)<65535
 visit(a)
 if changes:save_asset(a,TARGET,O,f.stem);assert try_load_asset(O/f.name);report['collision'].append(dict(file=f.name,changes=changes));print('COLLISION',f.name,len(changes),flush=True)
# Remove old occlusion volumes covering the demolished structures.
for f in N.glob('*bh1_occl_*.ymap'):
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
 if count:
  a.box_occluders=boxes;a.model_occluders=models;save_asset(a,TARGET,O,f.stem);assert try_load_asset(O/f.name);report['occlusion'].append(dict(file=f.name,volumes=count));print('OCCLUSION',f.name,count,flush=True)
measure={'model':'bh1_45_plot4a_ter_dcs','origin':origin.tolist(),'lot_model_bounds':{'min':(np.array([-39.3505859375,-33.66015625,-3.0751953125])+origin).tolist(),'max':(np.array([39.41796875,27.29296875,16.537109375])+origin).tolist(),'width_m':78.7685546875,'depth_m':60.953125},'roof_projection_area_m2':roof_union.area,'cleared_envelope_area_m2':foot.area,'removed_footprint_bounds_xy':list(foot.bounds),'removed_footprint_polygons':[list(p.exterior.coords) for p in (list(foot.geoms) if hasattr(foot,'geoms') else [foot])],'ground_level_z':floor,'clearance_z':[float(lo[2]),float(hi[2])],'measurement_note':'Lot bounds are the envelope of the native property mesh, not a cadastral area; cleared envelope spans the castle, balcony, porch and garage with 45 cm tolerance.'}
(W/'medidas.json').write_text(json.dumps(measure,indent=2));(W/'alteracoes.json').write_text(json.dumps(report,indent=2));print('BUILT',len(list(O.iterdir())),'assets; footprint',round(foot.area,2),flush=True)
