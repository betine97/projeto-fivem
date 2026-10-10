"""Carve only the occupied house volumes; retain neighbouring collision and occlusion."""
import sys,json,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];W=ROOT/'casa_vinewood';OUT=W/'fivem';N=W/'work/native'
sys.path[:0]=[str(W/'work/pydeps'),str(ROOT/'laboratorio_fivem/work/pydeps'),str(ROOT/'laboratorio_fivem/work'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from clip_geometry import subtract_box
from szio.gta5 import *
from szio.gta5.bounds import *
from szio.types import Vector
from shapely.geometry import Polygon,Point,MultiPoint,box as rect
ORIGIN=np.array(json.loads((W/'medidas_estudo.json').read_text())['native_origin'])
SPEC=json.loads((W/'encaixe_fachada.json').read_text())
RENDER_CUTS=[(np.array(a),np.array(b)) for a,b in SPEC['door_cuts']]
# The street gate opens into the recessed courtyard, then the side rear door.
# It is separate from the rear door plane at x=-1.35.
GATE_CUT=(np.array([1.10,7.08,-1.07]),np.array([3.61,7.56,2.14]))
RENDER_CUTS.append(GATE_CUT)
FOOTPRINT=Polygon(SPEC['ground_polygon']).union(Polygon(SPEC['upper_polygon'])).buffer(.38,join_style=2)
xy=list(FOOTPRINT.exterior.coords);xs=sorted(set(v[0] for v in xy));ys=sorted(set(v[1] for v in xy))
CUTS=[(np.array([x0,y0,-1.07]),np.array([x1,y1,6.52])) for x0,x1 in zip(xs,xs[1:]) for y0,y1 in zip(ys,ys[1:]) if FOOTPRINT.covers(Point((x0+x1)/2,(y0+y1)/2))]
CUTS+=RENDER_CUTS

def volume_cuts(poly,z0,z1):
 xy=list(poly.exterior.coords);xs=sorted(set(v[0] for v in xy));ys=sorted(set(v[1] for v in xy))
 return [(np.array([x0,y0,z0]),np.array([x1,y1,z1])) for x0,x1 in zip(xs,xs[1:]) for y0,y1 in zip(ys,ys[1:]) if poly.covers(Point((x0+x1)/2,(y0+y1)/2))]
# The house's deck meshes also contain railings and plinths inside the new rooms.
# Clip decoration by floor level; keep the exterior facade and external deck intact.
CLEANUP_CUTS=volume_cuts(Polygon(SPEC['ground_polygon']).buffer(-.055,join_style=2),-.825,2.558)
CLEANUP_CUTS+=volume_cuts(Polygon(SPEC['upper_polygon']).buffer(-.055,join_style=2),2.79,6.489)

TARGET=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
report={'cuts_native':[{'lo':a.tolist(),'hi':b.tolist()} for a,b in CUTS],'cleanup_volumes':[{'lo':a.tolist(),'hi':b.tolist()} for a,b in CLEANUP_CUTS],'render':[],'collision':[],'occlusion':[],'in_game_verified':False}

def clip(poly,cuts=None):
 pieces=[poly];changed=False
 for lo,hi in (CUTS if cuts is None else cuts):
  new=[]
  for p in pieces:
   out,hit=subtract_box(p,lo,hi);new.extend(out);changed|=hit
  pieces=new
 return pieces,changed

def triangles(poly):
 for i in range(1,len(poly)-1):
  t=np.array([poly[0],poly[i],poly[i+1]])
  if np.linalg.norm(np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]))>1e-7:yield t

FACES=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
SIGNS=np.array([(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
def box_corners(q):
 v1,v2,v3,v4=q;center=np.mean(q,axis=0);a1=((v3+v4)-(v1+v2))*.5
 edges=np.array([a1,v3-a1-v1,v4-a1-v1])
 if np.linalg.det(edges)<0:edges=edges[[0,2,1]]
 return center+SIGNS@edges*.5

parts=json.loads((W/'work/near_house_entities.json').read_text())
for e in parts:
 name=e['name']
 if not (name.startswith('ch2_09b_hs05') or name in ('ch2_09b_l2','ch2_09b_emissive_05')) or 'lod' in name:continue
 a=try_load_asset(N/(name+'.ydr'));offset=np.array(e['pos'])-ORIGIN;count=0
 for models in a.models.values():
  for model in models:
   keep=[]
   for g in model.geometries:
    sh=a.shader_group.shaders[g.shader_index]
    tex=next((p.value for p in sh.parameters if p.name.lower()=='diffusesampler'),'')
    # This house-only drawable contains fake opaque night-light window planes,
    # including three upper rear windows outside the interior clipping volume.
    # The replacement glass supplies the windows; discard the obsolete overlays.
    if name=='ch2_09b_emissive_05':count+=len(g.index_buffer)//3;continue
    if name in ('ch2_09b_hs05','ch2_09b_hs05_details') and 'wins' in str(tex).lower():count+=len(g.index_buffer)//3;continue
    structural=any(k in str(tex).lower() for k in ('wall32','wall_brick_32','idwall','wins'))
    cleanup=name!='ch2_09b_hs05' or not structural
    cuts=RENDER_CUTS+CLEANUP_CUTS if cleanup else RENDER_CUTS
    vb=g.vertex_buffer;names=vb.dtype.names;extra=[];inds=[];hits=0
    for t in g.index_buffer.reshape(-1,3):
     poly=[np.r_[row['Position'].astype(float)+offset,np.concatenate([np.asarray(row[n]).reshape(-1).astype(float) for n in names if n!='Position'])] for row in vb[t]]
     polys,hit=clip(poly,cuts)
     if not hit:inds.extend(map(int,t));continue
     hits+=1
     for p in polys:
      for tri in triangles(p):
       off=len(vb)+len(extra)
       for v in tri:
        row=np.zeros((),dtype=vb.dtype);row['Position']=v[:3]-offset;k=3
        for n in names:
         if n=='Position':continue
         dest=np.asarray(row[n]);vals=v[k:k+dest.size];k+=dest.size
         if np.issubdtype(dest.dtype,np.integer):vals=np.clip(np.rint(vals),0,np.iinfo(dest.dtype).max)
         if n=='Normal' and np.linalg.norm(vals)>0:vals=vals/np.linalg.norm(vals)
         row[n]=vals.reshape(dest.shape)
        extra.append(row)
       inds.extend((off,off+1,off+2))
    if hits:
     assert len(vb)+len(extra)<65535
     g.vertex_buffer=np.concatenate((vb,np.asarray(extra,dtype=vb.dtype))) if extra else vb
     g.index_buffer=np.array(inds,dtype=np.uint16);count+=hits
    if len(g.index_buffer):keep.append(g)
   model.geometries=keep
 if name=='ch2_09b_emissive_05':a.models={}
 if count:
  save_asset(a,TARGET,OUT,name);assert try_load_asset(OUT/(name+'.ydr'))
  report['render'].append({'file':name+'.ydr','cut_original_triangles':count});print('OPENED_RENDER',name,count,flush=True)

for f in sorted(N.glob('*ch2_09b_[0-3].ybn')):
 asset=try_load_asset(f);changes=[]
 def visit(b,parent=np.eye(4),path=()):
  tx=np.asarray(b.composite_transform)@parent
  for j,c in enumerate(getattr(b,'children',[])):visit(c,tx,path+(j,))
  if not hasattr(b,'geometry_primitives'):return
  verts=b.geometry_vertices;result=[];inverse=np.linalg.inv(tx)
  for j,t in enumerate(b.geometry_primitives):
   q=np.array([verts[i].co for i in t.vertices]);points=(np.c_[q,np.ones(len(q))]@tx)[:,:3]-ORIGIN
   pad=t.radius or 0
   lo=points.min(0)-pad;hi=points.max(0)+pad
   if not any(np.all(hi>=a)&np.all(lo<=z) for a,z in CUTS):result.append(t);continue
   if t.primitive_type not in (BoundPrimitiveType.TRIANGLE,BoundPrimitiveType.BOX):
    # A buried pole may extend below the floor, or span several clipping cells.
    # Test the complete footprint, rather than containment in one grid cell.
    shape=MultiPoint(points[:,:2]).convex_hull.buffer(pad+.002)
    internal=FOOTPRINT.covers(shape) and hi[2]>-1.07 and lo[2]<6.52
    if internal or any(np.all(lo>a)&np.all(hi<z) for a,z in RENDER_CUTS):changes.append({'path':path,'primitive':j,'type':t.primitive_type.name})
    else:result.append(t)
    continue
   surface=[points] if t.primitive_type==BoundPrimitiveType.TRIANGLE else [box_corners(points)[list(ids)] for ids in FACES]
   clipped=[];hit=False
   for face in surface:
    pieces,h=clip(list(face));hit|=h
    for p in pieces:clipped.extend(triangles(p))
   if not hit:result.append(t);continue
   changes.append({'path':path,'primitive':j,'type':t.primitive_type.name})
   for tri in clipped:
    co=(np.c_[tri+ORIGIN,np.ones(3)]@inverse)[:,:3];off=len(verts)
    verts.extend(BoundVertex(Vector(p),None) for p in co)
    result.append(BoundPrimitive.new_triangle(off,off+1,off+2,t.material,t.material_color))
  b.geometry_primitives=result
  assert len(verts)<65535
 visit(asset)
 if changes:
  save_asset(asset,TARGET,OUT,f.stem);assert try_load_asset(OUT/f.name)
  report['collision'].append({'file':f.name,'changes':changes});print('OPENED_COLLISION',f.name,len(changes),flush=True)

def occluder_chunks(tris,flags):
 chunk=[];points=set()
 def emit(ts):
  v=np.array(ts).reshape(-1,3);unique,inv=np.unique(np.round(v,5),axis=0,return_inverse=True)
  return MapModelOccluder(flags,unique.astype(np.float32),inv.reshape(-1,3).astype(np.uint8))
 for tri in tris:
  keys={tuple(np.round(v,5)) for v in tri}
  if chunk and len(points|keys)>250:yield emit(chunk);chunk=[];points=set()
  chunk.append(tri);points|=keys
 if chunk:yield emit(chunk)

for f in sorted(N.glob('ch2_occl*.ymap')):
 a=try_load_asset(f);new=[];changed=0;box_changed=0
 for o in a.model_occluders:
  tris=[];hit=False
  for ids in o.indices:
   pieces,h=clip(list(o.vertices[ids].astype(float)-ORIGIN));hit|=h
   for p in pieces:tris.extend(t+ORIGIN for t in triangles(p))
  if hit:new.extend(occluder_chunks(tris,o.flags));changed+=1
  else:new.append(o)
 boxes=[]
 for o in a.box_occluders:
  co=np.array(o.center)-ORIGIN;size=np.array(o.size)*.5;c,s=o.cos_sin_z
  # GTA's packed occluder axes differ by 90 degrees from ordinary yaw.
  pts=SIGNS*size;pts[:,:2]=pts[:,:2]@np.array([[s,c],[-c,s]]);pts+=co
  footprint=Polygon(pts[[0,1,2,3],:2])
  overlaps=not footprint.intersection(FOOTPRINT.buffer(.5)).is_empty and pts[:,2].max()>-1 and pts[:,2].min()<7
  if overlaps:box_changed+=1;continue
  tris=[];hit=False
  for ids in FACES:
   ps,h=clip(list(pts[list(ids)]));hit|=h
   for p in ps:tris.extend(t+ORIGIN for t in triangles(p))
  if hit:new.extend(occluder_chunks(tris,MapModelOccluderFlags(0)));box_changed+=1
  else:boxes.append(o)
 if changed or box_changed:
  a.model_occluders=new;a.box_occluders=boxes;save_asset(a,TARGET,OUT,f.stem)
  assert try_load_asset(OUT/f.name)
  report['occlusion'].append({'file':f.name,'models_cut':changed,'boxes_cut':box_changed});print('OPENED_OCCLUSION',f.name,changed,box_changed,flush=True)
(W/'alteracoes_nativas.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
assert report['render'] and report['collision']
print('NATIVE_HOUSE_OPEN_OK',flush=True)
