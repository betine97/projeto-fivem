"""Only carve the new door and below-grade garage/ramp; preserve all other data."""
import sys,json,copy,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent;N=W/'work/native';B=P/'baseline/stream';O=P/'stream'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(R/'laboratorio_fivem/work'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from clip_geometry import subtract_box
from szio.gta5 import *
from szio.gta5.bounds import *
from szio.types import Vector
import pymateria.gta5.gen8 as g8
spec=json.loads((P/'spec.json').read_text());origin=np.array(spec['origin']);target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
cuts=[(np.array(a),np.array(b)) for a,b in spec['earth_cuts']]+[(np.array(a),np.array(b)) for a,b in [spec['door_opening']]]
report={'render':[],'collision':[],'occlusion':[],'maps':[],'cuts':[[a.tolist(),b.tolist()] for a,b in cuts]}
def source(name):
    q=B/name;return q if q.exists() else N/name
def clip(poly,boxes=cuts):
    pieces=[poly];hit=False
    for a,b in boxes:
        result=[]
        for q in pieces:
            out,h=subtract_box(q,a,b);result.extend(out);hit|=h
        pieces=result
    return pieces,hit
def triangulate(poly):
    for i in range(1,len(poly)-1):
        t=np.array([poly[0],poly[i],poly[i+1]])
        if np.linalg.norm(np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]))>1e-8:yield t
def drawable(name,offset,boxes):
    f=source(name+'.ydr');a=try_load_asset(f);changes=0
    for models in a.models.values():
        for m in models:
            keep=[]
            for g in m.geometries:
                vb=g.vertex_buffer;extra=[];indices=[]
                for ids in g.index_buffer.reshape(-1,3):
                    q=[np.r_[row['Position'].astype(float)+offset,np.concatenate([np.asarray(row[n]).reshape(-1).astype(float) for n in vb.dtype.names if n!='Position'])] for row in vb[ids]]
                    polys,hit=clip(q,boxes)
                    if not hit:indices.extend(ids);continue
                    changes+=1
                    for p in polys:
                        for t in triangulate(p):
                            off=len(vb)+len(extra)
                            for v in t:
                                row=np.zeros((),dtype=vb.dtype);row['Position']=v[:3]-offset;k=3
                                for n in vb.dtype.names:
                                    if n=='Position':continue
                                    dest=np.asarray(row[n]);vals=v[k:k+dest.size];k+=dest.size
                                    if np.issubdtype(dest.dtype,np.integer):vals=np.clip(np.rint(vals),0,np.iinfo(dest.dtype).max)
                                    if n=='Normal' and np.linalg.norm(vals)>0:vals/=np.linalg.norm(vals)
                                    row[n]=vals.reshape(dest.shape)
                                extra.append(row)
                            indices.extend([off,off+1,off+2])
                if extra:g.vertex_buffer=np.concatenate([vb,np.array(extra,dtype=vb.dtype)])
                assert len(g.vertex_buffer)<65535
                g.index_buffer=np.array(indices,dtype=np.uint16)
                if len(indices):keep.append(g)
            m.geometries=keep
    if a.bounds is not None:cut_bound(a.bounds,np.array(offset),boxes)
    if changes:
        original_raw=g8.Drawable.import_rsc(f).result
        save_asset(a,target,O,name)
        exported=g8.Drawable.import_rsc(O/(name+'.ydr')).result
        assert len(exported.shader_group.shaders)==len(original_raw.shader_group.shaders)
        for s,old in zip(exported.shader_group.shaders,original_raw.shader_group.shaders):
            s.basis_shader=old.basis_shader;s.basis_material=old.basis_material
        g8.Drawable.export_rsc(exported,O/(name+'.ydr'))
        assert try_load_asset(O/(name+'.ydr'))
        report['render'].append({'file':name+'.ydr','triangles_cut':changes,'offset':offset.tolist(),'original_shader_keys_preserved':True})
        print('CARVED_RENDER',name,changes,flush=True)
faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
signs=np.array([(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
def corners(q):
    v1,v2,v3,v4=q;c=q.mean(0);a=((v3+v4)-(v1+v2))*.5;edges=np.array([a,v3-a-v1,v4-a-v1])
    if np.linalg.det(edges)<0:edges=edges[[0,2,1]]
    return c+signs@edges*.5
def cut_bound(asset,offset,boxes):
    changed=[0]
    def visit(b,parent=np.eye(4)):
        tx=np.asarray(b.composite_transform)@parent
        for c in getattr(b,'children',[]):visit(c,tx)
        if not hasattr(b,'geometry_primitives'):return
        vs=b.geometry_vertices;result=[];inv=np.linalg.inv(tx)
        for t in b.geometry_primitives:
            q=np.array([vs[i].co for i in t.vertices]);v=(np.c_[q,np.ones(len(q))]@tx)[:,:3]+offset
            lo=v.min(0)-(t.radius or 0);hi=v.max(0)+(t.radius or 0)
            if not any(np.all(hi>=a)&np.all(lo<=z) for a,z in boxes):result.append(t);continue
            if t.primitive_type not in [BoundPrimitiveType.TRIANGLE,BoundPrimitiveType.BOX]:
                if any(np.all(lo>a)&np.all(hi<z) for a,z in boxes):changed[0]+=1
                else:result.append(t)
                continue
            surfaces=[v] if t.primitive_type==BoundPrimitiveType.TRIANGLE else [corners(v)[list(ids)] for ids in faces]
            hit=False;triangles=[]
            for surface in surfaces:
                ps,h=clip(list(surface),boxes);hit|=h
                for p in ps:triangles.extend(triangulate(p))
            if not hit:result.append(t);continue
            changed[0]+=1
            for tri in triangles:
                co=(np.c_[tri-offset,np.ones(3)]@inv)[:,:3];n=len(vs);vs.extend(BoundVertex(Vector(v),None) for v in co)
                result.append(BoundPrimitive.new_triangle(n,n+1,n+2,t.material,t.material_color))
        b.geometry_primitives=result
        assert len(vs)<65535
    visit(asset);return changed[0]
entities=json.loads((W/'work/near_house_entities.json').read_text())
for name in ['ch2_09b_hs05','ch2_09b_hs05_details','ch2_09b_l2']:
    e=next(e for e in entities if e['name']==name);drawable(name,np.array(e['pos'])-origin,cuts)
drawable('mansao_paredes',np.zeros(3),[cuts[-1]])
for original in sorted(N.glob('*ch2_09b_[0-3].ybn')):
    f=source(original.name);a=try_load_asset(f);count=cut_bound(a,-origin,cuts)
    if count:
        save_asset(a,target,O,f.stem);assert try_load_asset(O/f.name)
        report['collision'].append({'file':f.name,'primitives_cut':count});print('CARVED_COLLISION',f.name,count,flush=True)
f=source('cidade_mansao.ybn');a=try_load_asset(f);count=cut_bound(a,-origin,[cuts[-1]])
if count:save_asset(a,target,O,f.stem);report['collision'].append({'file':f.name,'primitives_cut':count})
# Native occlusion planes must also be opened where the street looks into the garage.
from szio.gta5.maps import MapModelOccluder,MapModelOccluderFlags
for f in [source('ch2_occl_02.ymap'),source('apa_ch2_occl_02.ymap')]:
    if not f.exists():continue
    a=try_load_asset(f);keep=[];changed=0
    for oc in a.model_occluders:
        triangles=[];hit=False
        for ids in oc.indices:
            ps,h=clip(list(oc.vertices[ids].astype(float)-origin));hit|=h
            for p in ps:triangles.extend(t+origin for t in triangulate(p))
        if not hit:keep.append(oc);continue
        changed+=1
        for i in range(0,len(triangles),60):
            v=np.array(triangles[i:i+60]).reshape(-1,3);uv,ids=np.unique(np.round(v,5),axis=0,return_inverse=True)
            keep.append(MapModelOccluder(oc.flags,uv.astype(np.float32),ids.reshape(-1,3).astype(np.uint8)))
    boxes=[]
    for oc in a.box_occluders:
        co=np.array(oc.center)-origin;size=np.array(oc.size)*.5
        if any(np.all(co+size>=lo)&np.all(co-size<=hi) for lo,hi in cuts):changed+=1
        else:boxes.append(oc)
    if changed:
        a.model_occluders=keep;a.box_occluders=boxes;save_asset(a,target,O,f.stem);report['occlusion'].append({'file':f.name,'opened':changed})
(P/'site_patch_report.json').write_text(json.dumps(report,indent=2))
assert any(e['file']=='mansao_paredes.ydr' for e in report['render'])
print('FACADE_SITE_CARVED',flush=True)
