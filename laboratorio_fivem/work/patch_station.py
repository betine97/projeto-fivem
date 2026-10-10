import sys,json,copy,numpy as np
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps']
from szio.gta5 import try_load_asset,save_asset,AssetTarget,AssetFormat,AssetVersion
from szio.gta5.bounds import BoundPrimitive,BoundPrimitiveType,BoundVertex
from szio.types import Vector
from clip_geometry import subtract_box
work=Path(__file__).resolve().parent;src=work/'base_assets';out=work.parent/'exports';out.mkdir(exist_ok=True)
targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
station=np.array([1554.5638427734375,814.5931396484375,88.08595275878906]);u=np.array([.873294,-.487193,0]);u/=np.linalg.norm(u);v=np.array([-u[1],u[0],0]);basis=np.stack([u,v,[0,0,1]],axis=1)
door=station+np.array([-1.947998046875,27.69677734375,-10.43896484375]);origin=station+basis@np.array([-12.5,31.2,-10.43896484375])
# Lab local coordinate frame, entrance starts at ground level.
d=(door-origin)@basis
boxes=[(d+[-.602,-.55,-.01],d+[.602,.55,2.28])]
report={'station_model':'ch3_08_ppbldg003','station':station.tolist(),'origin':origin.tolist(),'basis':basis.tolist(),'door':door.tolist(),'door_local':d.tolist(),'heading':float(np.degrees(np.arctan2(u[1],u[0]))),'patched':[]}
asset=try_load_asset(src/'ch3_08_ppbldg003.ydr');removed=0
for models in asset.models.values():
 for model in models:
  for g in model.geometries:
   vb=g.vertex_buffer;names=vb.dtype.names;poskey=next(k for k in names if k.lower()=='position');inds=[]
   for tri in g.index_buffer.reshape(-1,3):
    xyz=(vb[poskey][tri]+station-origin)@basis
    # Existing green leaf occupies this precise opening; preserve all other surfaces.
    if g.shader_index==13 and np.all(np.abs(xyz[:,:2]-d[:2])<[.62,.05]) and xyz[:,2].max()<2.30:
     removed+=1;continue
    inds.extend(tri)
   g.index_buffer=np.array(inds,dtype=g.index_buffer.dtype)
assert removed==4,removed
save_asset(asset,targets,out,'ch3_08_ppbldg003');report['door_render_triangles_removed']=removed
# Remove only the doorway obstruction and internal collision occupying the room.
boxes += [(np.array([-4.0,-5.90,.015]),np.array([4.0,5.90,3.60])),(np.array([-3.8,-7.80,.015]),np.array([1.7,-5.80,3.25]))]
for p in src.glob('*ch3_08*.ybn'):
 a=try_load_asset(p);changed=0
 def process(b):
  global changed
  if b is None:return
  if hasattr(b,'children'):
   for child in b.children:process(child)
  if not hasattr(b,'geometry_primitives'):return
  trans=np.array(b.composite_transform);inv=np.linalg.inv(trans)
  verts=b.geometry_vertices;prims=[]
  for t in b.geometry_primitives:
   if t.primitive_type!=BoundPrimitiveType.TRIANGLE:prims.append(t);continue
   xyz=np.array([list(verts[i].co)+[1] for i in t.vertices])@trans
   local=(xyz[:,:3]-origin)@basis
   pieces=[list(local)];touched=False
   for lo,hi in boxes:
    result=[]
    for piece in pieces:
     new,hit=subtract_box(piece,lo,hi);result.extend(new);touched|=hit
    pieces=result
   if not touched:prims.append(t);continue
   changed+=1
   for poly in pieces:
    if len(poly)<3:continue
    world=np.array(poly)@basis.T+origin
    co=(np.c_[world,np.ones(len(world))]@inv)[:,:3];idx=len(verts)
    verts.extend(BoundVertex(Vector(v),None) for v in co)
    for j in range(1,len(poly)-1):
     if np.linalg.norm(np.cross(co[j]-co[0],co[j+1]-co[0]))>1e-6:prims.append(BoundPrimitive.new_triangle(idx,idx+j,idx+j+1,t.material,t.material_color))
  b.geometry_primitives=prims
 process(a)
 if changed:
  save_asset(a,targets,out,p.stem);report['patched'].append({'file':p.name,'triangles_cut':changed});print('PATCHED',p.name,changed,flush=True)
(work.parent/'placement.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
