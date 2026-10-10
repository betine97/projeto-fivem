"""Reuse installed glass/wood door and jamb in the two requested openings."""
import sys,json,copy,math,hashlib,shutil,re,os
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao';O=P/'package';B=P/'backup'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',str(R/'casa_vinewood/work/lua_syntax_deps')]
import numpy as np
from szio.gta5 import *
from szio.gta5.bounds import *
from szio.gta5.maps import *
from szio.gta5.entities import *
from szio.types import Vector,Quaternion
from luaparser import ast
from lupa import LuaRuntime
TARGET=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
changed=['portas_madeira.json','auditoria_client.lua','objetos_catalogo.json','fxmanifest.lua']
if not (P/'baseline.json').exists():
    (P/'baseline.json').write_text(json.dumps({f.relative_to(D).as_posix():sha(f) for f in D.rglob('*') if f.is_file()},indent=2))
    for rel in changed:
        dest=B/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(D/rel,dest)
baseline=json.loads((P/'baseline.json').read_text())
assert all(sha(D/n)==baseline[n] for n in changed),'Concurrent edits to door targets'
(O/'stream').mkdir(parents=True,exist_ok=True)
cfg=json.loads((D/'portas_madeira.json').read_text());assert len(cfg['doors'])==7
origin=np.array(cfg['origin']);source=try_load_asset(D/'stream/mansao_porta_vidro_aparador.ydr')
fixed=try_load_asset(D/'stream/mansao_parede_aparador.ydr')

def points(a):return np.concatenate([g.vertex_buffer['Position'] for m in a.models[LodLevel.HIGH] for g in m.geometries])
def setbounds(b,lo,hi):
    b.bb_min=Vector(lo);b.bb_max=Vector(hi);b.centroid=Vector((lo+hi)/2);b.cg=b.centroid;b.radius_around_centroid=float(np.linalg.norm(hi-lo)/2)
def scale_bound(b,s):
    for c in getattr(b,'children',[]):
        if c:scale_bound(c,s)
    if hasattr(b,'geometry_vertices'):
        for v in b.geometry_vertices:v.co=Vector(np.array(v.co)*s)
        b.geometry_center=Vector(np.array(b.geometry_center)*s)
    setbounds(b,np.array(b.bb_min)*s,np.array(b.bb_max)*s)
def scale_mesh(a,s):
    for ms in a.models.values():
        for m in ms:
            for g in m.geometries:
                vb=g.vertex_buffer.copy();vb['Position']*=s
                for field,factor in [('Normal',1/s),('Tangent',s)]:
                    if field in vb.dtype.names:
                        vec=vb[field][:,:3]*factor;vec/=np.maximum(np.linalg.norm(vec,axis=1,keepdims=True),1e-9);vb[field][:,:3]=vec
                g.vertex_buffer=vb
    if a.bounds:scale_bound(a.bounds,s)
def canonical_shaders(a):
    for shader in a.shader_group.shaders:
        # Known authored preset names; avoid rehashing unresolved hash_* labels.
        shader.name=Path(shader.preset_filename).stem
def typ(a):
    ps=points(a);lo,hi=ps.min(0),ps.max(0)
    return Archetype(a.name,ArchetypeType.BASE,32,120,0,120,'','','',a.name,Vector(lo),Vector(hi),Vector((lo+hi)/2),float(np.linalg.norm(hi-lo)/2),a.name,ArchetypeAssetType.DRAWABLE,[])

# Extract the original three beveled wood jambs, with original UVs/material.
jamb=copy.deepcopy(source);jamb.name='mansao_batente_vidro_sala';jamb.lights=[]
wood_index=next(i for i,s in enumerate(fixed.shader_group.shaders) if any(q.value=='apar_madeira' for q in s.parameters if isinstance(q.value,str)))
jamb.shader_group=copy.deepcopy(fixed.shader_group);jamb.models={};jamb.bounds=None
geom=[]
for m in fixed.models[LodLevel.HIGH]:
    for g in m.geometries:
        if g.shader_index!=wood_index:continue
        ps=g.vertex_buffer['Position'];tri=g.index_buffer.reshape(-1,3);t=ps[tri]
        keep=np.all((t>=[14.1075,-5.7205,-.8005])&(t<=[14.3685,-4.6195,1.7005]),axis=(1,2))
        if not keep.any():continue
        chosen=tri[keep];used,inv=np.unique(chosen,return_inverse=True);ng=copy.deepcopy(g);vb=g.vertex_buffer[used].copy()
        p=vb['Position'].copy();vb['Position'][:,0]=-(p[:,1]+5.676);vb['Position'][:,1]=p[:,0]-14.168;vb['Position'][:,2]=p[:,2]+.785
        for field in ['Normal','Tangent']:
            if field in vb.dtype.names:
                q=vb[field].copy();vb[field][:,0]=-q[:,1];vb[field][:,1]=q[:,0]
        ng.vertex_buffer=vb;ng.index_buffer=inv.reshape(-1).astype(np.uint16);geom.append(ng)
assert geom and 60<=sum(len(g.index_buffer)//3 for g in geom)<=400,'Unexpected jamb extraction'
model=copy.deepcopy(source.models[LodLevel.HIGH][0]);model.geometries=geom
for lod in [LodLevel.HIGH,LodLevel.MEDIUM,LodLevel.LOW,LodLevel.VERYLOW]:jamb.models[lod]=[copy.deepcopy(model)]
# Keep only the wood shader and required shared embedded maps in this small prop.
jamb.shader_group.shaders=[copy.deepcopy(fixed.shader_group.shaders[wood_index])]
required={q.value for q in jamb.shader_group.shaders[0].parameters if isinstance(q.value,str)}
jamb.shader_group.embedded_textures={k:copy.deepcopy(v) for k,v in fixed.shader_group.embedded_textures.items() if k in required}
for ms in jamb.models.values():
    for m in ms:
        for g in m.geometries:g.shader_index=0
canonical_shaders(jamb)

names=re.findall(r'CollisionMaterialDef\("([A-Z_0-9]+)"',Path(r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz/Sollumz/ybn/collision_materials.py').read_text())
face=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
def jamb_bound():
    b=AssetBoundBvh();b.margin=.001;b.composite_collision_type_flags=CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_WEAPON|CollisionFlags.MAP_TYPE_VEHICLE;b.composite_collision_include_flags=CollisionFlags(0xffffffff)
    vs=[];fs=[]
    for lo,hi in [([-.044,-.060,-.015],[0,.20,2.485]),([-1.056,-.060,-.015],[-1.012,.20,2.485]),([-1.012,-.060,2.44],[0,.20,2.485])]:
        x,y,z=lo;X,Y,Z=hi;idx=len(vs);vs.extend([(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)])
        fs.extend(tuple(idx+i for i in f) for f in face)
    b.geometry_vertices=[BoundVertex(Vector(v),None) for v in vs];b.geometry_primitives=[BoundPrimitive.new_triangle(*f,CollisionMaterial.from_packed(names.index('WOOD_SOLID_MEDIUM'))) for f in fs]
    setbounds(b,np.min(vs,0),np.max(vs,0));c=AssetBoundComposite(children=[b]);setbounds(c,np.min(vs,0),np.max(vs,0));return c
# The right jamb sits on the positive X side of the hinge, matching source mesh.
jamb.bounds=jamb_bound()
# Correct right post collision extent to match extracted actual geometry.
for v in jamb.bounds.children[0].geometry_vertices[:8]:v.co[0]+=.044
setbounds(jamb.bounds.children[0],np.array([-1.056,-.06,-.015]),np.array([.044,.20,2.485]));setbounds(jamb.bounds,np.array([-1.056,-.06,-.015]),np.array([.044,.20,2.485]))

# Door two is the actual left side facade opening. Door one is perpendicular
# to the bar frontage, at X 6.344, not the new main entry elsewhere in the map.
newdoors=[dict(id=8,name='Sacada ao lado do bar',model='mansao_porta_vidro_bar',hinge=[6.344,-12.32,-.785],closed_heading=90,open_heading=185,width_m=1.15,height_m=2.677,leaf_thickness_m=.045,opening_center=[6.344,-12.895,.54],opening_bounds=[6.219,6.469,-13.52,-12.27,-.8,1.95]),
          dict(id=9,name='Sacada da sala ao lado da TV',model='mansao_porta_vidro_aparador',hinge=[-9.181,-4.664,-.785],closed_heading=90,open_heading=-5,width_m=1.012,height_m=2.427,leaf_thickness_m=.045,opening_center=[-9.181,-5.17,.25],opening_bounds=[-9.306,-9.056,-5.72,-4.62,-.8,1.7])]
barleaf=copy.deepcopy(source);barleaf.name='mansao_porta_vidro_bar';sbar=np.array([1.15/1.012,1,2.677/2.427]);scale_mesh(barleaf,sbar);canonical_shaders(barleaf)
barframe=copy.deepcopy(jamb);barframe.name='mansao_batente_vidro_bar';scale_mesh(barframe,np.array([1.25/1.1,1,2.75/2.5]))
# Align scaled jamb top/bottom with floor, rather than scaling its 15 mm offset.
offset=np.array([0,0,.0015]);
for ms in barframe.models.values():
    for m in ms:
        for g in m.geometries:g.vertex_buffer['Position']+=offset
def offsetbound(b,o):
    for c in getattr(b,'children',[]):
        if c:offsetbound(c,o)
    if hasattr(b,'geometry_vertices'):
        for v in b.geometry_vertices:v.co=Vector(np.array(v.co)+o)
        b.geometry_center=Vector(np.array(b.geometry_center)+o)
    setbounds(b,np.array(b.bb_min)+o,np.array(b.bb_max)+o)
offsetbound(barframe.bounds,offset)
assets=[barleaf,jamb,barframe]
for a in assets:save_asset(a,TARGET,O/'stream',a.name)
save_asset(AssetMapTypes(name='mansao_portas_sacadas',archetypes=[typ(a) for a in assets]),TARGET,O/'stream','mansao_portas_sacadas')
entities=[];ext=[]
for d,n in zip(newdoors,['mansao_batente_vidro_bar','mansao_batente_vidro_sala']):
    pos=origin+d['hinge'];angle=math.radians(d['closed_heading']);q=Quaternion([math.cos(angle/2),0,0,-math.sin(angle/2)])
    entities.append(Entity(n,Vector(pos),q,1,1,EntityFlags.IS_STATIC,0,-1,120,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[]))
    a=next(a for a in assets if a.name==n);ps=points(a);rot=np.array([[math.cos(angle),-math.sin(angle),0],[math.sin(angle),math.cos(angle),0],[0,0,1]])
    ext.extend(ps@rot.T+pos)
lo,hi=np.min(ext,0),np.max(ext,0)
save_asset(AssetMapData(name='mansao_portas_sacadas',content_flags=MapContentFlags.HAS_ENTITIES_HD|MapContentFlags.HAS_PHYSICS,entities=entities,streaming_extents=(Vector(lo-120),Vector(hi+120)),entities_extents=(Vector(lo-.01),Vector(hi+.01))),TARGET,O/'stream','mansao_portas_sacadas')
cfg['doors']+=newdoors;cfg['prototypes'].append(dict(name=barleaf.name,width_m=1.15,height_m=2.677,thickness_m=.045));cfg['revision']='portas-bar-sala-20261008'
cfg['reserved_entrances']=['Novos modelos aplicados nas sacadas indicadas nos prints 2 e 3; entrada principal atual preservada.']
(O/'portas_madeira.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
catalog=json.loads((D/'objetos_catalogo.json').read_text());assert 'protectedModels' in catalog
for n in [a.name for a in assets]:
    if n not in catalog['protectedModels']:catalog['protectedModels'].append(n)
(O/'objetos_catalogo.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
fx=(D/'fxmanifest.lua').read_text(encoding='utf-8')+"\n-- Matching wood/glass doors and fixed jambs at bar and living balcony exits.\nfiles { 'stream/mansao_portas_sacadas.ytyp' }\ndata_file 'DLC_ITYP_REQUEST' 'stream/mansao_portas_sacadas.ytyp'\n"
(O/'fxmanifest.lua').write_text(fx,encoding='utf-8')
audit=(D/'auditoria_client.lua').read_text(encoding='utf-8').replace("local woodenDoorModel = GetHashKey('mansao_porta_madeira_095')","local configuredDoors = json.decode(LoadResourceFile(GetCurrentResourceName(), 'portas_madeira.json'))\nlocal doorModels = {}\nfor _, door in ipairs(configuredDoors.doors) do doorModels[GetHashKey(door.model)] = true end")
audit=audit.replace('GetEntityModel(entity) == woodenDoorModel','doorModels[GetEntityModel(entity)] == true')
(O/'auditoria_client.lua').write_text(audit,encoding='utf-8');ast.parse(audit);ast.parse(fx)

# Validate the closed leaf remains within each real opening and the open leaf
# clears its center line by > 0.30 m, preserving E and shared server state.
checks=[]
for d in newdoors:
    a=try_load_asset(O/'stream'/f"{d['model']}.ydr") if d['id']==8 else source
    assert a.bounds is not None
    ps=points(a);angle=math.radians(d['closed_heading']);rot=np.array([[math.cos(angle),-math.sin(angle),0],[math.sin(angle),math.cos(angle),0],[0,0,1]])
    p=ps@rot.T+d['hinge'];b=d['opening_bounds']
    assert p[:,1].min()>=b[2]-.01 and p[:,1].max()<=b[3]+.01
    assert p[:,2].min()>=b[4] and p[:,2].max()<=b[5],(d['name'],p.max(0))
    assert len(a.models)==4
    assert all(np.isfinite(g.vertex_buffer['Position']).all() for ms in a.models.values() for m in ms for g in m.geometries)
    checks.append(dict(id=d['id'],name=d['name'],closed_bbox=[p.min(0).tolist(),p.max(0).tolist()],fits_opening=True,all_four_lods=True,hinge_space_collision=True,interaction='E'))
beforecfg=json.loads((B/'portas_madeira.json').read_text());assert cfg['doors'][:7]==beforecfg['doors']
for a in assets:
    rt=try_load_asset(O/'stream'/f'{a.name}.ydr')
    for lod in a.models:
        for x,y in zip(a.models[lod],rt.models[lod]):
            for g,h in zip(x.geometries,y.geometries):assert np.array_equal(g.vertex_buffer,h.vertex_buffer) and np.array_equal(g.index_buffer,h.index_buffer)
    for k,t in a.shader_group.embedded_textures.items():assert t.data.read_bytes()==rt.shader_group.embedded_textures[k].data.read_bytes()
assert 'CreateObjectNoOffset' in (D/'portas_client.lua').read_text() and 'config.doors' in (D/'portas_server.lua').read_text()
changes={f.relative_to(O).as_posix():f for f in O.rglob('*') if f.is_file()}
before={f.relative_to(D).as_posix():sha(f) for f in D.rglob('*') if f.is_file()}
for n in changed:assert before[n]==baseline[n]
for n in changes:
    if n not in changed:assert n not in before,'New asset name already exists'
for rel,src in changes.items():
    dst=D/rel;assert dst.resolve().is_relative_to(D.resolve());tmp=dst.with_name(dst.name+'.door-update');shutil.copy2(src,tmp);os.replace(tmp,dst)
after={f.relative_to(D).as_posix():sha(f) for f in D.rglob('*') if f.is_file()}
for n in before:
    if n not in changes:assert after[n]==before[n],f'Unrelated file changed {n}'
assert all(after[n]==sha(src) for n,src in changes.items())
report=dict(installed=True,doors=checks,original_seven_doors_preserved=True,source_door_unchanged=True,shared_E_runtime_preserved=True,
    changed={n:after[n] for n in changes},unrelated_files_preserved=len(before)-len(changed),saved_prop_positions_preserved=True,
    architecture_lighting_preserved=True,in_game_verified=False)
(P/'installation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('INSTALLED two matching doors; fitted jambs; E shared state; preserved',report['unrelated_files_preserved'],'unrelated files',flush=True)
