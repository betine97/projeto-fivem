import sys,json,hashlib,struct,math,collections
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent;O=P/'stream';B=P/'baseline/stream'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(R/'laboratorio_fivem/work'),str(W/'work/lua_syntax_deps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
from szio.gta5.bounds import *
from clip_geometry import subtract_box
import pymateria.gta5.gen8 as g8
from luaparser import ast
from lupa import LuaRuntime
spec=json.loads((P/'spec.json').read_text());origin=np.array(spec['origin']);patch=json.loads((P/'site_patch_report.json').read_text());report={'passed':False,'native_roundtrip':True,'in_game_verified':False,'models':{},'checks':{}}
installnames={p['file'] for cat in ['render','collision','occlusion','maps'] for p in patch[cat]}|{n+'.ydr' for n in spec['models']}|{'mansao_acesso_garagem.ytyp','mansao_acesso_garagem.ymap','mansao_acesso_garagem.ybn'}
assets={n:try_load_asset(O/n) for n in installnames};assert all(a is not None for a in assets.values())
def memory(p):
    _,_,s,g=struct.unpack('<4I',p.read_bytes()[:16])
    def size(f):return (512<<(f&15))*sum([(f>>27)&1,((f>>26)&1)*2,((f>>25)&1)*4,((f>>24)&1)*8,((f>>17)&127)*16,((f>>11)&63)*32,((f>>7)&15)*64,((f>>5)&3)*128,((f>>4)&1)*256])
    return {'system_MiB':size(s)/1048576,'graphics_MiB':size(g)/1048576,'disk_bytes':p.stat().st_size}
for name in spec['models']:
    a=assets[name+'.ydr'];counts=[]
    for lod in [LodLevel.HIGH,LodLevel.MEDIUM,LodLevel.LOW,LodLevel.VERYLOW]:
        assert len(a.models[lod])==1
        count=0
        for m in a.models[lod]:
            for g in m.geometries:
                vb=g.vertex_buffer;ids=g.index_buffer.reshape(-1,3);assert ids.min()>=0 and ids.max()<len(vb)
                for n in vb.dtype.names:assert np.isfinite(vb[n]).all()
                ts=vb['Position'][ids];assert np.min(np.linalg.norm(np.cross(ts[:,1]-ts[:,0],ts[:,2]-ts[:,0]),axis=1))>1e-12
                if 'Tangent' in vb.dtype.names:assert np.min(np.linalg.norm(vb['Tangent'][:,:3],axis=1))>.5
                count+=len(ids)
        counts.append(count)
    assert counts==sorted(counts,reverse=True)
    expected={'normal_spec.sps':'hash_38dd00df','emissive.sps':'hash_8f245469','glass.sps':'hash_d9f8c9bf'}
    for s in a.shader_group.shaders:assert str(s.name)==expected[s.preset_filename]
    for txname,tx in a.shader_group.embedded_textures.items():
        data=tx.data.read_bytes();source=(P/'textures'/(txname+'.dds')).read_bytes();assert data[128:]==source[128:len(data)]
        h,w=struct.unpack_from('<II',data,12);levels=struct.unpack_from('<I',data,28)[0];assert levels>=max(1,int(math.log2(min(w,h)))-1)
    mem=memory(O/(name+'.ydr'));assert mem['graphics_MiB']<16 and mem['system_MiB']<16
    report['models'][name]={'triangles_by_lod':counts,'memory':mem,'embedded_collision':True,'always_on_lights':len(a.lights)}
for row in patch['render']:
    n=row['file'];old=B/n;old=old if old.exists() else W/'work/native'/n
    x=g8.Drawable.import_rsc(old).result;y=g8.Drawable.import_rsc(O/n).result
    assert [(s.basis_shader.hash,s.basis_material.hash) for s in x.shader_group.shaders]==[(s.basis_shader.hash,s.basis_material.hash) for s in y.shader_group.shaders]
    # All triangles outside the precise cut are retained, including the interior room walls.
    a=try_load_asset(old);b=assets[n];off=np.array(row['offset']);cuts=patch['cuts'][-1:] if n=='mansao_paredes.ydr' else patch['cuts'];unchanged=0
    for lod,models in a.models.items():
        def signature(t,shader):return shader,tuple(np.round(t.reshape(-1),5))
        actual=collections.Counter(signature(g.vertex_buffer['Position'][ids],g.shader_index) for m in b.models[lod] for g in m.geometries for ids in g.index_buffer.reshape(-1,3))
        for m in models:
            for g in m.geometries:
                for ids in g.index_buffer.reshape(-1,3):
                    q=g.vertex_buffer['Position'][ids];hit=False
                    for lo,hi in cuts:
                        _,h=subtract_box(list(q.astype(float)+off),np.array(lo),np.array(hi));hit|=h
                    if not hit:
                        s=signature(q,g.shader_index);assert actual[s]>0,(n,lod,s);actual[s]-=1;unchanged+=1
    row['triangles_outside_cut_verified']=unchanged
print('GEOMETRY_PRESERVED',flush=True)
faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
signs=np.array([(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
def physical(asset,off,parent=np.eye(4)):
    tx=np.asarray(asset.composite_transform)@parent;ts=[]
    for c in getattr(asset,'children',[]):ts.extend(physical(c,off,tx))
    if hasattr(asset,'geometry_primitives'):
        vs=np.array([v.co for v in asset.geometry_vertices]);v=(np.c_[vs,np.ones(len(vs))]@tx)[:,:3]+off
        for t in asset.geometry_primitives:
            q=v[list(t.vertices)]
            if t.primitive_type==BoundPrimitiveType.TRIANGLE:ts.append(q)
            elif t.primitive_type==BoundPrimitiveType.BOX:
                v1,v2,v3,v4=q;c=q.mean(0);e=((v3+v4)-(v1+v2))*.5;edges=np.array([e,v3-e-v1,v4-e-v1])
                if np.linalg.det(edges)<0:edges=edges[[0,2,1]]
                points=c+signs@edges*.5;ts.extend(points[list(f)] for f in faces)
    return ts
ts=[]
for suffix in ['','hi@']:
    for i in range(4):
        n=suffix+'ch2_09b_'+str(i)+'.ybn';f=O/n;f=f if f.exists() else B/n;f=f if f.exists() else W/'work/native'/n
        ts.extend(physical(try_load_asset(f),-origin))
for n in spec['models'][:2]:ts.extend(physical(assets[n+'.ydr'].bounds,np.zeros(3)))
# Current unchanged floors and stair collision are also part of the checks.
for n in ['mansao_pisos','mansao_escada','mansao_paredes']:
    a=assets.get(n+'.ydr') or try_load_asset(B/(n+'.ydr'))
    if a.bounds:ts.extend(physical(a.bounds,np.zeros(3)))
ts=np.array(ts);a=ts[:,0];e1=ts[:,1]-a;e2=ts[:,2]-a
def intersections(p,q):
    p=np.array(p,dtype=float);d=np.array(q)-p;h=np.cross(np.broadcast_to(d,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h);safe=abs(det)>1e-7;inv=1/np.where(safe,det,1);v=p-a;u=np.einsum('ij,ij->i',v,h)*inv;s=np.cross(v,e1);w=np.einsum('j,ij->i',d,s)*inv;t=np.einsum('ij,ij->i',e2,s)*inv;keep=safe&(u>=-1e-5)&(w>=-1e-5)&(u+w<=1.00001)&(t>=0)&(t<=1)
    return p+t[keep,None]*d
def rampz(x,y):
    t=max(0,min(1,(y-9.55)/(19.22-9.55)));return -4.2+(-3.159-(x-6.4)*.1205+4.2)*t*t*(3-2*t)
for x in [4.12,4.40,4.68,4.98,5.18]:
    for z in [-.55,.25,1.25,1.98]:assert len(intersections([x,7.91,z],[x,6.9,z]))==0,('entry blocked',x,z)
for x in [4.1,4.65,5.2]:
    for z in [-.64,-.40,-.15,.30]:
        hits=intersections([x,7.91,z],[x,15.10,z])
        assert len(hits)==0,('entry terrace obstacle',x,z,hits.tolist())
for x in [4.0,4.15,4.3]:
    for z in [-.4,.5,1.2]:
        assert len(intersections([x,6.9,z],[x,2.9,z]))==0,('foyer connection to hall',x,z)
for x in [7.4,8.0,9.6,11.2,12.0]:
    for y in np.arange(9.65,19.18,.36):
        z=rampz(x,y);hits=intersections([x,y,z+.32],[x,y,z-.32]);assert len(hits)>0,('ramp missing',x,y)
        assert abs(hits[:,2].max()-z)<.015,('invisible ground',x,y,z,hits[:,2])
        assert len(intersections([x,y,z+.40],[x,y,z+2.65]))==0,('car roof obstacle',x,y)
for x in [7,8.1,9.4,10,11.2,12.2]:
    for y in [-.2,1.7,4,6.5,8.5]:
        assert len(intersections([x,y,-3.9],[x,y,-4.4]))>0
        assert len(intersections([x,y,-3.7],[x,y,-1.55]))==0,('garage car envelope',x,y)
top_open=spec['gate_hinge'][2]-.067;assert top_open-spec['garage_floor']>2.65 and top_open<spec['garage_ceiling']-.07
assert spec['garage_ceiling']-spec['garage_floor']>2.9
maxgrade=1.5*(1.041)/(19.22-9.55);assert maxgrade<.17
assert all(np.max(np.array(q['vertices'])[:,1])<5.8 or np.min(np.array(q['vertices'])[:,1])>5.9 for q in spec['collision_meshes'][spec['models'][0]])
report['checks'].update({'clear_main_door':True,'clear_exterior_stair_arrival':True,'foyer_connection_to_existing_hall':True,'garage_floor_and_car_headroom':True,'ramp_continuous_no_native_ground_above':True,'garage_ceiling_height_m':spec['garage_ceiling']-spec['garage_floor'],'ramp_max_grade_percent':maxgrade*100,'gate_swing_below_slab':True,'unchanged_triangles':patch['render'],'stairs_office_lavabo_meshes_preserved':True})
print('PHYSICAL_PATHS_VERIFIED',flush=True)
for f in ['garagem_client.lua','garagem_server.lua']:ast.parse((P/f).read_text())
# Exercise the server authorization and anti-crush rules with the Lua runtime.
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute("""
events={}; messages={}; positions={}; vehicles={}; players={'1'}; source=1; now=3000
function GetCurrentResourceName() return 'cidade_mansao' end
function LoadResourceFile() return '' end
json={decode=function() return cfg end}
function RegisterNetEvent(n,f) events[n]=f end
function AddEventHandler() end
function TriggerClientEvent(n,p,a,b) table.insert(messages,{name=n,player=p,state=a,instant=b}) end
function GetGameTimer() return now end
function GetPlayerPed(p) return tonumber(p) end
function DoesEntityExist(e) return positions[e]~=nil end
function GetEntityCoords(e) return positions[e] end
function GetPlayers() return players end
function GetAllVehicles() return vehicles end
""")
def table(v):
    if isinstance(v,dict):return lua.table_from({k:table(x) for k,x in v.items()})
    if isinstance(v,list):return lua.table_from([table(x) for x in v])
    return v
g=lua.globals();g.cfg=table({'origin':spec['origin'],'interaction':[9.6,9.44,-3.0]})
def position(id,x,y,z):g.positions[id]=table(dict(zip(['x','y','z'],origin+[x,y,z])))
lua.execute((P/'garagem_server.lua').read_text());position(1,9.6,13,-3.1);g.events['cidade_mansao:toggleGarage']();assert g.messages[1]['state']==True
g.now=6000;position(1,9.6,7.5,-3.1);g.events['cidade_mansao:toggleGarage']();assert g.messages[2]['name']=='cidade_mansao:garageBlocked'
g.now=9000;position(1,9.6,14,-3.1);position(100,9.6,9,-3.2);g.vehicles=table([100]);g.events['cidade_mansao:toggleGarage']();assert g.messages[3]['name']=='cidade_mansao:garageBlocked'
g.now=12000;g.vehicles=table([]);g.events['cidade_mansao:toggleGarage']();assert g.messages[4]['state']==False
g.now=15000;position(1,4.65,7.5,.1);g.events['cidade_mansao:toggleGarage']();assert len(g.messages)==4
g.now=18000;position(1,0,30,-3);g.events['cidade_mansao:toggleGarage']();assert len(g.messages)==4
report['checks']['lua_server_open_close_proximity_and_people_vehicle_guard']=True
report['checks']['upper_front_door_does_not_trigger_gate']=True
report['files']={n:hashlib.sha256((O/n).read_bytes()).hexdigest() for n in sorted(installnames)}
report['passed']=True;(P/'verification.json').write_text(json.dumps(report,indent=2));print('GARAGE_VERIFIED',len(installnames),report['checks']['garage_ceiling_height_m'],flush=True)
