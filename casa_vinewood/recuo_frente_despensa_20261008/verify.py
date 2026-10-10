import sys,json,math,collections,hashlib,struct
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent;O=P/'stream';B=P/'baseline/stream'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/lua_syntax_deps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
from szio.gta5.bounds import *
import pymateria.gta5.gen8 as g8
from luaparser import ast
from lupa import LuaRuntime
spec=json.loads((P/'spec.json').read_text());patch=json.loads((P/'patch_report.json').read_text());origin=np.array(spec['origin'])
names={q['file'] for cat in ['native_render','native_collision','wall','landscape','occlusion'] for q in patch[cat]}|{'mansao_fachada_entrada.ydr','mansao_garagem_subsolo.ydr','mansao_acesso_garagem.ybn','mansao_acesso_garagem.ytyp','mansao_acesso_garagem.ymap'}
assets={n:try_load_asset(O/n) for n in names};assert all(a is not None for a in assets.values())
report={'passed':False,'in_game_verified':False,'assets_loaded':len(names),'models':{},'checks':{}}
for name in ['mansao_fachada_entrada','mansao_garagem_subsolo']:
    a=assets[name+'.ydr'];counts=[]
    for lod in [LodLevel.HIGH,LodLevel.MEDIUM,LodLevel.LOW,LodLevel.VERYLOW]:
        count=0
        for m in a.models[lod]:
            for g in m.geometries:
                vb=g.vertex_buffer;ids=g.index_buffer.reshape(-1,3);assert ids.max()<len(vb)
                for n in vb.dtype.names:assert np.isfinite(vb[n]).all()
                q=vb['Position'][ids];assert (np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)>1e-12).all()
                count+=len(ids)
        counts.append(count)
    assert counts==sorted(counts,reverse=True)
    old=try_load_asset(B/(name+'.ydr'));assert len(a.lights)==len(old.lights)
    for lamp,prior in zip(a.lights,old.lights):
        for key in ['color','intensity','flags','time_flags','falloff','falloff_exponent','volume_intensity','corona_intensity','light_type']:
            assert getattr(lamp,key)==getattr(prior,key),('Lighting profile changed',name,key)
    assert a.bounds is not None
    report['models'][name]={'triangles_by_lod':counts,'disk_bytes':(O/(name+'.ydr')).stat().st_size}
def signatures(a):
    return collections.Counter((int(lod),g.shader_index,tuple(np.round(g.vertex_buffer['Position'][ids].reshape(-1),5))) for lod,models in a.models.items() for m in models for g in m.geometries for ids in g.index_buffer.reshape(-1,3))
old=try_load_asset(B/'mansao_paredes.ydr');new=assets['mansao_paredes.ydr'];before=signatures(old);after=signatures(new)
assert not (after-before), 'Unexpected new wall faces'
assert sum((before-after).values())==1264
for name in ['mansao_paredes.ydr']+[q['file'] for q in patch['native_render']]:
    x=g8.Drawable.import_rsc(B/name).result;y=g8.Drawable.import_rsc(O/name).result
    assert [(s.basis_shader.hash,s.basis_material.hash) for s in x.shader_group.shaders]==[(s.basis_shader.hash,s.basis_material.hash) for s in y.shader_group.shaders]
# Build the actual physical surfaces, including both regular and high-detail native collision.
faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
signs=np.array([(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
def physical(b,offset,parent=np.eye(4)):
    tx=np.asarray(b.composite_transform)@parent;tri=[]
    for c in getattr(b,'children',[]):tri.extend(physical(c,offset,tx))
    if hasattr(b,'geometry_primitives'):
        vs=np.array([v.co for v in b.geometry_vertices]);vs=(np.c_[vs,np.ones(len(vs))]@tx)[:,:3]+offset
        for t in b.geometry_primitives:
            v=vs[list(t.vertices)]
            if t.primitive_type==BoundPrimitiveType.TRIANGLE:tri.append(v)
            elif t.primitive_type==BoundPrimitiveType.BOX:
                v1,v2,v3,v4=v;center=v.mean(0);e=((v3+v4)-(v1+v2))*.5;edges=np.array([e,v3-e-v1,v4-e-v1])
                if np.linalg.det(edges)<0:edges=edges[[0,2,1]]
                corners=center+signs@edges*.5;tri.extend(corners[list(f)] for f in faces)
    return tri
tris=[]
for f in O.glob('*ch2_09b_[0-3].ybn'):
    if f.name.startswith(('ch2_','hi@ch2_')):tris.extend(physical(assets[f.name],-origin))
for name in ['mansao_fachada_entrada.ydr','mansao_garagem_subsolo.ydr','mansao_paredes.ydr']:
    tris.extend(physical(assets[name].bounds,np.zeros(3)))
tris.extend(physical(assets['cidade_mansao.ybn'],-origin))
ts=np.array(tris);v=ts[:,0];e1=ts[:,1]-v;e2=ts[:,2]-v
def intersections(p,q):
    p=np.array(p,dtype=float);d=np.array(q)-p;h=np.cross(np.broadcast_to(d,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h);safe=abs(det)>1e-7;inv=1/np.where(safe,det,1);r=p-v;u=np.einsum('ij,ij->i',r,h)*inv;s=np.cross(r,e1);w=np.einsum('j,ij->i',d,s)*inv;t=np.einsum('ij,ij->i',e2,s)*inv;keep=safe&(u>=-1e-5)&(w>=-1e-5)&(u+w<=1.00001)&(t>=0)&(t<=1)
    return p+t[keep,None]*d
def edge(x):return 16.235+.173*x
def rampz(x,t):
    a=.12;s=t*t/(2*a*(1-a)) if t<a else 1-(1-t)**2/(2*a*(1-a)) if t>1-a else (t-a/2)/(1-a)
    return -4.20+(-3.0606-(x-6.4)*.1126+4.20)*s
rays=0
for x in [7.0,7.5,8,9.6,11.2,12.2]:
    for t in np.arange(.012,.997,.035):
        y=9.55+(edge(x)-9.55)*t;z=rampz(x,t)
        h=intersections([x,y,z+.12],[x,y,z-.12]);assert len(h)>0,('ramp hole',x,t)
        assert abs(h[:,2].max()-z)<.025,('native floor above ramp',x,t,h[:,2],z)
        assert len(intersections([x,y,z+.25],[x,y,z+2.65]))==0,('car clearance',x,t)
        rays+=3
for x in [2.90,3.20,3.80,4.25,4.95,5.30]:
    for z in [-.55,.25,1.25,2.1]:
        h=intersections([x,1.9,z],[x,2.8,z]);assert len(h)==0,('hall still blocked',x,z,h)
        rays+=1
    assert len(intersections([x,2.35,-.6],[x,2.35,-1.1]))>0,('floor under removed wall',x)
    assert len(intersections([x,2.35,2.1],[x,2.35,3.05]))>0,('ceiling over removed wall',x)
for i in range(1,14):
    x=4.745;y=edge(x)-.30-(i-.5)*.30;t=i/13
    z=(-2.7435-(x-3.64)*.1145)*(1-t)-.8*t
    h=intersections([x,y,z+.1],[x,y,z-.2]);assert len(h)>0 and abs(h[:,2].max()-z)<.012,('stair traversal',i,h)
    rays+=1
for y in [12.1,12.38,12.5,12.7,12.80]:
    h=intersections([4.745,y,-.70],[4.745,y,-1.05]);assert len(h)>0 and abs(h[:,2].max()+.8)<.025,('stair arrival hole',y,h)
    rays+=1
for q in spec['collision_meshes']['mansao_fachada_entrada']:
    if 'degrau' in q['name'].lower() or 'Patamar inferior' in q['name'] or 'Mureta escada' in q['name']:
        vq=np.array(q['vertices']);assert (vq[:,1]-.173*vq[:,0]<=16.26).all(),('stair in street',q['name'])
for q in spec['collision_meshes']['mansao_garagem_subsolo']:
    vq=np.array(q['vertices']);assert (vq[:,1]-.173*vq[:,0]<=16.26).all(),('garage in street',q['name'])
for i in range(1,14):
    q=next(q for q in spec['collision_meshes']['mansao_fachada_entrada'] if q['name']=='Entrada degrau %02d'%i)
    vv=np.array(q['vertices']);assert abs(np.ptp(vv[:,1]-.173*vv[:,0])-.30)<.001
report['checks'].update(physical_rays=rays,stair_treads_30cm=True,garage_inset_diagonal_edge=True,wall_and_frame_removed=True,floor_and_ceiling_preserved=True)
# Shared door state must continue to work after deleting a middle entry in the list.
cfg=json.loads((P/'portas_madeira.json').read_text());assert [d['id'] for d in cfg['doors']]==[1,2,4,5,6,7,8,9]
for f in ['portas_client.lua','portas_server.lua']:ast.parse((P/f).read_text())
lua=LuaRuntime(unpack_returned_tuples=True);g=lua.globals();g.decode=lambda _:lua.table_from(cfg,recursive=True)
lua.execute('''json={decode=decode};handlers={};emitted={};players={'1','2'};pedpos={};now=1000;source=1
function GetCurrentResourceName() return 'cidade_mansao' end
function LoadResourceFile(...) return 'doors' end
function RegisterNetEvent(name,fn) handlers[name]=fn end
function AddEventHandler(name,fn) handlers[name]=fn end
function GetGameTimer() return now end
function GetPlayerPed(p) return tonumber(p) end
function GetEntityCoords(p) return pedpos[p] end
function GetPlayers() return players end
function TriggerClientEvent(name,target,...) emitted[#emitted+1]={name,target,...} end''')
lua.execute((P/'portas_server.lua').read_text())
def at(p):return lua.table_from(dict(zip(['x','y','z'],[a+b for a,b in zip(cfg['origin'],p)])))
fn=g.handlers['cidade_mansao:toggleDoor'];tests=0
for d in cfg['doors']:
    c=d['opening_center'];p=c[:];p[1]+=1.5;g.pedpos[1]=at(p);g.pedpos[2]=at([0,0,0]);g.now+=1000
    fn(d['id']);event=g.emitted[len(g.emitted)];assert event[1]=='cidade_mansao:doorState' and event[3]==d['id'] and event[4] is True;tests+=1
    g.now+=1000;g.pedpos[2]=at([c[0],c[1],-.8+.85]);fn(d['id']);assert g.emitted[len(g.emitted)][1]=='cidade_mansao:doorOccupied';tests+=1
    g.now+=1000;g.pedpos[2]=at([0,0,0]);fn(d['id']);assert g.emitted[len(g.emitted)][4] is False;tests+=1
    count=len(g.emitted);g.now+=1000;g.pedpos[1]=at([0,0,10]);fn(d['id']);assert len(g.emitted)==count;tests+=1
count=len(g.emitted);g.now+=1000;fn(3);assert len(g.emitted)==count
report['checks']['door_runtime_cases']=tests+1
report['passed']=True;report['install_files']=sorted(['stream/'+n for n in names]+['portas_client.lua','portas_server.lua','portas_madeira.json'])
(P/'verification.json').write_text(json.dumps(report,indent=2));print('VERIFIED',rays,'physical rays',tests+1,'door cases',len(names),'assets',flush=True)
