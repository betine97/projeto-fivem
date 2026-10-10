"""Re-cut native terrain to the inset footprint; remove only the marked divider."""
import sys, json, copy, hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent;F=W/'fachada_garagem_20261008';N=W/'work/native';O=P/'stream';B=P/'baseline/stream'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(R/'laboratorio_fivem/work'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
from szio.gta5.bounds import *
from szio.types import Vector
from clip_geometry import subtract_box
import pymateria.gta5.gen8 as g8
spec=json.loads((P/'spec.json').read_text());origin=np.array(spec['origin']);target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
report={'native_render':[],'native_collision':[],'wall':[],'landscape':[]}
# Reuse the proven vertex/UV interpolation and collision serializer, in this stage only.
source_code=(F/'patch_site.py').read_text().split('entities=json.loads')[0]
env={'__file__':str(F/'patch_site.py')}
exec(compile(source_code,str(F/'patch_site.py'),'exec'),env)
env['O']=O
env['report']={'render':[]}
def original(name):
    live=B/name;old=F/'stream'/name
    if live.exists() and old.exists():
        assert live.read_bytes()==old.read_bytes(), f'Native asset changed since facade install: {name}'
    f=F/'baseline/stream'/name
    return f if f.exists() else N/name
env['source']=original
axis=[(np.array(a),np.array(b)) for a,b in spec['earth_cuts']+[spec['door_opening']]]
env['cuts']=axis
def inset_clip(poly,boxes=None):
    pieces=[np.asarray(poly,dtype=float)];hit=False
    for low,high in (axis if boxes is None else boxes):
        skew = .173 if (abs(low[0]-6.145)<.001 or abs(low[0]-3.54)<.001) else 0
        result=[]
        for part in pieces:
            if not skew:
                out,h=subtract_box(list(part),low,high)
            else:
                # A constant inland edge and diagonal street edge form a six-plane volume.
                planes=[([-1,0,0],-low[0]),([1,0,0],high[0]),([0,-1,0],-low[1]),([-skew,1,0],16.255),([0,0,-1],-low[2]),([0,0,1],high[2])]
                remaining=list(part);out=[];h=True
                for normal,bound in planes:
                    inside=[];outside=[];normal=np.array(normal)
                    for v,w in zip(remaining,remaining[1:]+remaining[:1]):
                        dv=np.dot(normal,v[:3])-bound;dw=np.dot(normal,w[:3])-bound;iv=dv<=1e-7;iw=dw<=1e-7
                        (inside if iv else outside).append(v)
                        if iv!=iw:
                            q=v+(w-v)*(dv/(dv-dw));inside.append(q);outside.append(q)
                    if len(outside)>=3:out.append(outside)
                    remaining=inside
                    if len(remaining)<3:out=[list(part)];h=False;break
            hit |= h
            result.extend(np.asarray(x,dtype=float) for x in out)
        pieces=result
    return pieces,hit
env['clip']=inset_clip
rows=json.loads((W/'work/near_house_entities.json').read_text())
for name in ['ch2_09b_hs05','ch2_09b_hs05_details','ch2_09b_l2']:
    row=next(e for e in rows if e['name']==name)
    env['drawable'](name,np.array(row['pos'])-origin,axis)
report['native_render']=env['report']['render']
for f in sorted(N.glob('*ch2_09b_[0-3].ybn')):
    a=try_load_asset(original(f.name));count=env['cut_bound'](a,-origin,axis)
    if count:
        save_asset(a,target,O,f.stem);report['native_collision'].append({'file':f.name,'primitives_cut':count})
        print('NATIVE_COLLISION',f.name,count,flush=True)
# Only entire wall/frame faces in the marked frontage; leave floor/ceiling and perpendicular walls.
wall_lo=np.array(spec['removed_wall'][0]);wall_hi=np.array(spec['removed_wall'][1])
def marked(v):
    if not (np.all(v.min(0)>=wall_lo-.0004) and np.all(v.max(0)<=wall_hi+.0004)):return False
    if np.ptp(v[:,2])<.002 and (abs(v[0,2]+.80)<.004 or abs(v[0,2]-2.358)<.004):return False
    return True
def remove_bound(b,offset,parent=np.eye(4)):
    tx=np.asarray(b.composite_transform)@parent;count=0
    for child in getattr(b,'children',[]):count+=remove_bound(child,offset,tx)
    if not hasattr(b,'geometry_primitives'):return count
    v=np.array([x.co for x in b.geometry_vertices]);v=(np.c_[v,np.ones(len(v))]@tx)[:,:3]+offset
    keep=[]
    for t in b.geometry_primitives:
        if marked(v[list(t.vertices)]):count+=1
        else:keep.append(t)
    b.geometry_primitives=keep
    return count
def prune_bounds(b):
    if hasattr(b,'children'):
        b.children=[c for c in b.children if prune_bounds(c)]
        return bool(b.children)
    return not hasattr(b,'geometry_primitives') or bool(b.geometry_primitives)
for name in ['mansao_paredes.ydr','cidade_mansao.ybn']:
    a=try_load_asset(B/name);render=0
    if name.endswith('.ydr'):
        for lod,models in a.models.items():
            for m in models:
                for g in m.geometries:
                    tris=g.index_buffer.reshape(-1,3);keep=np.array([not marked(g.vertex_buffer['Position'][ids]) for ids in tris]);render+=int((~keep).sum());g.index_buffer=tris[keep].reshape(-1).copy()
                m.geometries=[g for g in m.geometries if len(g.index_buffer)]
            a.models[lod]=[m for m in models if m.geometries]
        count=remove_bound(a.bounds,np.zeros(3));prune_bounds(a.bounds);raw=g8.Drawable.import_rsc(B/name).result
        save_asset(a,target,O,Path(name).stem)
        new=g8.Drawable.import_rsc(O/name).result
        assert len(new.shader_group.shaders)==len(raw.shader_group.shaders)
        for shader,old in zip(new.shader_group.shaders,raw.shader_group.shaders):
            shader.basis_shader=old.basis_shader;shader.basis_material=old.basis_material
        new.lights=raw.lights
        g8.Drawable.export_rsc(new,O/name)
    else:
        count=remove_bound(a,-origin);prune_bounds(a);save_asset(a,target,O,Path(name).stem)
    report['wall'].append({'file':name,'faces_removed':render,'collision_faces_removed':count})
    print('WALL_REMOVED',name,render,count,flush=True)
# Remove plants left above the excavated areas, consistently across GTA map variants.
remove_names={'prop_bush_med_07','prop_bush_med_03','prop_agave_01','prop_weeds_nxg04','prop_plant_cane_02a','prop_wall_light_03a'}
for prefix in ['', 'apa_', 'hei_']:
    for tail in ['critical_0','long_0','strm_0','strm_1']:
        name=prefix+'ch2_09b_'+tail+'.ymap';f=B/name
        if not f.exists():f=N/name
        a=try_load_asset(f);keep=[];indices={};changes=[]
        for i,e in enumerate(a.entities):
            p=np.array(e.position)-origin;n=str(e.archetype_name)
            affected=(6.10<p[0]<13.08 and 9.53<p[1]<19.25) or (3.53<p[0]<5.91 and 12.38<p[1]<18.0)
            if affected and n in remove_names:
                assert e.num_children==0
                changes.append({'model':n,'old':p.tolist(),'action':'remove'});continue
            indices[i]=len(keep);keep.append(e)
        if changes:
            # Parents are indices in the parent map, not indices in this child list.
            a.entities=keep;save_asset(a,target,O,Path(name).stem)
            report['landscape'].append({'file':name,'changes':changes})
for name in ['ch2_roads_long_0.ymap','ch2_roads.ymap']:
    f=B/name if (B/name).exists() else N/name;a=try_load_asset(f);changes=[]
    for i,e in enumerate(a.entities):
        p=np.array(e.position)-origin
        if np.linalg.norm(p[:2]-[12.4188,16.1446])<.01 and str(e.archetype_name) in ['prop_palm_sm_01d','ch2_props_combo0126_11_lod']:
            old=p.copy();p[:2]=[14.03,15.90];e.position=Vector(origin+p)
            changes.append({'model':str(e.archetype_name),'old':old.tolist(),'new':p.tolist(),'action':'move_to_retained_soil'})
    assert len(changes)==1
    save_asset(a,target,O,Path(name).stem);report['landscape'].append({'file':name,'changes':changes})
# Procedural grass is stored in packed instance batches, separately from object entities.
for prefix in ['', 'apa_', 'hei_']:
    name=prefix+'ch2_09b_grass_0.ymap';f=N/name
    if not f.exists():continue
    a=try_load_asset(f);removed=0
    for batch in a.grass_instance_lists:
        lo,hi=map(np.array,batch.extents)
        p=lo+batch.instances['Position'].astype(float)/65535*(hi-lo)-origin
        hit=((p[:,0]>3.45)&(p[:,0]<5.95)&(p[:,1]>12.35)&(p[:,1]<19.3))|((p[:,0]>6.05)&(p[:,0]<13.12)&(p[:,1]>9.50)&(p[:,1]<19.3))
        removed+=int(hit.sum());batch.instances=batch.instances[~hit].copy()
    if removed:
        a.grass_instance_lists=[g for g in a.grass_instance_lists if len(g.instances)]
        save_asset(a,target,O,Path(name).stem);report['landscape'].append({'file':name,'grass_instances_removed':removed})
env['report']['occlusion']=[]
occl=(F/'patch_site.py').read_text().split('# Native occlusion planes')[1].split("(P/'site_patch_report.json')")[0]
exec(compile('# Native occlusion planes'+occl,str(F/'patch_site.py'),'exec'),env)
report['occlusion']=env['report']['occlusion']
# Stable IDs: delete the Despensa entry and look up remaining doors by their actual IDs.
config=json.loads((P/'baseline/portas_madeira.json').read_text());assert next(d for d in config['doors'] if d['id']==3)['name']=='Despensa'
config['doors']=[d for d in config['doors'] if d['id']!=3];config['revision']='recuo-frente-despensa-20261008'
(P/'portas_madeira.json').write_text(json.dumps(config,indent=2,ensure_ascii=False),encoding='utf-8')
for name in ['portas_client.lua','portas_server.lua']:
    code=(P/'baseline'/name).read_text(encoding='utf-8')
    at="local config = json.decode(LoadResourceFile(resource, 'portas_madeira.json'))"
    code=code.replace(at,at+'\nlocal doorsById = {}\nfor _, door in ipairs(config.doors) do doorsById[door.id] = door end')
    code=code.replace('config.doors[id]','doorsById[id]')
    (P/name).write_text(code,encoding='utf-8')
(P/'patch_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('PATCH_READY',report['wall'],flush=True)
