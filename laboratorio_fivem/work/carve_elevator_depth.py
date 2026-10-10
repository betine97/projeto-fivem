"""Open only the tested lift footprint through the former rear wall."""
from pathlib import Path
import sys
import numpy as np

root=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(root/'laboratorio_fivem/work'),
 r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps']
from clip_geometry import subtract_box
from szio.gta5 import AssetTarget,AssetFormat,AssetVersion,try_load_asset,save_asset
from szio.gta5.bounds import BoundPrimitive,BoundPrimitiveType,BoundVertex
from szio.types import Vector
import json

p=json.loads((root/'laboratorio_fivem/placement.json').read_text())
origin=np.array(p['origin']);station=np.array(p['station']);basis=np.array(p['basis'])
out=root/'laboratorio_fivem/elevator_update'
stream=root/'server-data/resources/cidade_laboratorio/stream'
target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
lo=np.array([-1.16,5.84,.025]);hi=np.array([1.16,7.30,2.27])

def cut_bound_asset(filename,is_world):
    asset=try_load_asset(stream/filename)
    total=0
    def visit(bound):
        nonlocal total
        for child in getattr(bound,'children',[]):visit(child)
        if not hasattr(bound,'geometry_primitives'):return
        transform=np.array(bound.composite_transform)
        inverse=np.linalg.inv(transform)
        verts=bound.geometry_vertices
        result=[]
        for tri in bound.geometry_primitives:
            if tri.primitive_type!=BoundPrimitiveType.TRIANGLE:
                result.append(tri);continue
            points=np.array([list(verts[i].co)+[1] for i in tri.vertices])@transform
            points=points[:,:3]
            local=(points-origin)@basis if is_world else points
            polys,hit=subtract_box(list(local),lo,hi)
            if not hit:
                result.append(tri);continue
            total+=1
            for poly in polys:
                if len(poly)<3:continue
                base=np.array(poly)@basis.T+origin if is_world else np.array(poly)
                co=(np.c_[base,np.ones(len(base))]@inverse)[:,:3]
                offset=len(verts)
                verts.extend(BoundVertex(Vector(point),None) for point in co)
                for j in range(1,len(co)-1):
                    if np.linalg.norm(np.cross(co[j]-co[0],co[j+1]-co[0]))>1e-6:
                        result.append(BoundPrimitive.new_triangle(offset,offset+j,offset+j+1,
                                                                  tri.material,tri.material_color))
        bound.geometry_primitives=result
    visit(asset if is_world else asset.bounds)
    assert total>0,(filename,total)
    save_asset(asset,target,out,Path(filename).stem)
    print('CUT_COLLISION',filename,total,flush=True)

cut_bound_asset('hi@ch3_08_20.ybn',True)
cut_bound_asset('lab_estrutura.ydr',False)

# Preserve every vertex channel while clipping the native back-wall render.
asset=try_load_asset(stream/'ch3_08_ppbldg003.ydr')
removed=0
for models in asset.models.values():
    for model in models:
        for geom in model.geometries:
            vb=geom.vertex_buffer
            names=vb.dtype.names
            if not names or 'Position' not in names:continue
            output_indices=[]
            extra=[]
            for indices in geom.index_buffer.reshape(-1,3):
                rows=vb[indices]
                points=(np.asarray(rows['Position'],dtype=np.float64)+station-origin)@basis
                vectors=[]
                for point,row in zip(points,rows):
                    attrs=np.concatenate([np.asarray(row[name]).reshape(-1).astype(np.float64)
                                          for name in names if name!='Position'])
                    vectors.append(np.r_[point,attrs])
                polys,hit=subtract_box(vectors,lo,hi)
                if not hit:
                    output_indices.extend(map(int,indices));continue
                removed+=1
                for poly in polys:
                    if len(poly)<3:continue
                    offset=len(vb)+len(extra)
                    for vertex in poly:
                        row=np.zeros((),dtype=vb.dtype)
                        row['Position']=(vertex[:3]@basis.T+origin-station).astype(np.float32)
                        k=3
                        for name in names:
                            if name=='Position':continue
                            value=np.asarray(row[name]);count=value.size
                            interpolated=vertex[k:k+count]
                            if np.issubdtype(value.dtype,np.integer):
                                interpolated=np.clip(np.rint(interpolated),0,np.iinfo(value.dtype).max)
                            row[name]=interpolated.reshape(value.shape)
                            k+=count
                        extra.append(row)
                    for j in range(1,len(poly)-1):
                        a,b,c=poly[0][:3],poly[j][:3],poly[j+1][:3]
                        if np.linalg.norm(np.cross(b-a,c-a))>1e-7:
                            output_indices.extend((offset,offset+j,offset+j+1))
            if extra:
                assert len(vb)+len(extra)<65535
                geom.vertex_buffer=np.concatenate((vb,np.asarray(extra,dtype=vb.dtype)))
                geom.index_buffer=np.asarray(output_indices,dtype=np.uint16)
assert removed>0
save_asset(asset,target,out,'ch3_08_ppbldg003')
print('CUT_RENDER',removed,flush=True)

for filename in ('hi@ch3_08_20.ybn','lab_estrutura.ydr','ch3_08_ppbldg003.ydr'):
    assert try_load_asset(out/filename) is not None,filename
print('ELEVATOR_DEPTH_CARVE_OK',flush=True)
