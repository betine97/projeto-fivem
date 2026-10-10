"""Test serialized leaf physics and server/client door behavior."""
import sys,json,math,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=R/'server-data/resources/cidade_mansao'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/lua_syntax_deps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import try_load_asset
from lupa import LuaRuntime
from luaparser import ast
config=json.loads((W/'portas_madeira.json').read_text());a=try_load_asset(W/'fivem/mansao_porta_madeira_095.ydr')
child=a.bounds.children[0];v=np.array([q.co for q in child.geometry_vertices]);T=v[np.array([q.vertices for q in child.geometry_primitives])]
assert len(T)==12 and abs(np.ptp(v[:,1])-.045)<.001
assert 'mansao_porta_madeira_095' not in [e.archetype_name for e in try_load_asset(W/'fivem/cidade_mansao.ymap').entities]
def hits(a,b,t):
 d=b-a;e1=t[:,1]-t[:,0];e2=t[:,2]-t[:,0];h=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,h);ok=abs(det)>1e-12;inv=np.divide(1,det,out=np.zeros_like(det),where=ok);s=a-t[:,0];u=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1);vv=inv*(q@d);tt=inv*np.einsum('ij,ij->i',e2,q)
 return bool(np.any(ok&(u>=0)&(vv>=0)&(u+vv<=1)&(tt>0)&(tt<1)))
physical=[]
for d in config['doors']:
 hinge=np.array(d['hinge']);c=np.array(d['opening_center']);c[2]=hinge[2]+.85
 closed=T+hinge;ang=math.radians(d['open_heading']);rot=np.array([[math.cos(ang),-math.sin(ang),0],[math.sin(ang),math.cos(ang),0],[0,0,1]])
 opened=T@rot.T+hinge
 assert hits(c-[0,.4,0],c+[0,.4,0],closed),d['name']
 assert not hits(c-[0,.4,0],c+[0,.4,0],opened),d['name']
 # A 60cm-wide pedestrian corridor stays clear of the opened leaf.
 for dx in (-.3,0,.3):assert not hits(c+[dx,-.4,0],c+[dx,.4,0],opened),(d['name'],dx)
 physical.append(dict(name=d['name'],closed_blocks=True,open_center_and_body_width_clear=True))
for p in D.glob('*.lua'):ast.parse(p.read_text(encoding='utf-8'))
lua=LuaRuntime(unpack_returned_tuples=True);g=lua.globals()
def table(value):
 if isinstance(value,dict):return lua.table_from({k:table(v) for k,v in value.items()})
 if isinstance(value,list):return lua.table_from([table(v) for v in value])
 return value
g.test_config=table(config)
lua.execute('''
handlers={};events={};clock=1000;source=1;positions={};players={1};pedexists=true
json={decode=function(_) return test_config end}
function GetCurrentResourceName() return 'cidade_mansao' end
function LoadResourceFile(_,_) return '' end
function RegisterNetEvent(n,f) handlers[n]=f end
function AddEventHandler(n,f) handlers[n]=f end
function TriggerClientEvent(n,target,...) table.insert(events,{name=n,target=target,args={...}}) end
function GetGameTimer() return clock end
function GetPlayerPed(id) return pedexists and tonumber(id) or 0 end
function GetEntityCoords(p) return positions[p] end
function GetPlayers() return players end
''')
lua.execute((D/'portas_server.lua').read_text(encoding='utf-8'));cases=[]
def position(x,y,z):g.positions[1]=lua.table_from(dict(x=x+config['origin'][0],y=y+config['origin'][1],z=z+config['origin'][2]))
def call(name,arg=None):
 g.events=lua.table()
 if arg is None:g.handlers[name]()
 else:g.handlers[name](arg)
 return [dict(g.events[i].items()) for i in range(1,len(g.events)+1)]
def expect(name,fn,n):
 ev=fn();assert len(ev)==n,(name,ev);cases.append(dict(name=name,passed=True));return ev
position(0,0,0)
expect('Initial five closed states',lambda:call('cidade_mansao:requestDoorStates'),1)
expect('Invalid door rejected',lambda:call('cidade_mansao:toggleDoor',99),0)
expect('Fractional index rejected',lambda:call('cidade_mansao:toggleDoor',1.5),0)
expect('Remote toggle rejected',lambda:call('cidade_mansao:toggleDoor',1),0)
d=config['doors'][0];c=d['opening_center'];position(c[0],c[1]-.9,c[2])
e=expect('Nearby door opens for all clients',lambda:call('cidade_mansao:toggleDoor',1),1);assert e[0]['target']==-1 and e[0]['args'][2] is True
expect('Rapid repeat suppressed',lambda:call('cidade_mansao:toggleDoor',1),0)
g.clock=2000;position(*c)
e=expect('Occupied doorway cannot close',lambda:call('cidade_mansao:toggleDoor',1),1);assert e[0]['name']=='cidade_mansao:doorOccupied'
position(c[0],c[1]-.9,c[2]);g.clock=3000
e=expect('Clear doorway closes',lambda:call('cidade_mansao:toggleDoor',1),1);assert e[0]['args'][2] is False
g.pedexists=False;g.clock=4000
expect('Missing player entity rejected',lambda:call('cidade_mansao:toggleDoor',1),0)
g.pedexists=True
expect('Rejoining client receives snapshot',lambda:call('cidade_mansao:requestDoorStates'),1)
# Exercise the client prop lifecycle and smooth hinge movement with coroutines.
client=LuaRuntime(unpack_returned_tuples=True);cg=client.globals()
# Convert to the client runtime, since Lua objects cannot cross runtimes.
cg.test_config=client.eval('function() return {} end')()
def ct(value):
 if isinstance(value,dict):return client.table_from({k:ct(v) for k,v in value.items()})
 if isinstance(value,list):return client.table_from([ct(v) for v in value])
 return value
cg.test_config=ct(config)
client.execute('''
handlers={};threads={};entities={};rotations={};deleted={};serverevents={};clock=1000;nextentity=100;press=false
local mt={__add=function(a,b) return vector3(a.x+b.x,a.y+b.y,a.z+b.z) end,__sub=function(a,b) return vector3(a.x-b.x,a.y-b.y,a.z-b.z) end,__len=function(a) return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z) end}
function vector3(x,y,z) return setmetatable({x=x,y=y,z=z},mt) end
coords=vector3(test_config.origin[1],test_config.origin[2],test_config.origin[3])
json={decode=function(_) return test_config end}
function GetCurrentResourceName() return 'cidade_mansao' end
function LoadResourceFile(_,_) return '' end
function RegisterNetEvent(n,f) handlers[n]=f end
function AddEventHandler(n,f) handlers[n]=f end
function CreateThread(f) table.insert(threads,coroutine.create(f)) end
function Wait(_) coroutine.yield() end
function PlayerPedId() return 1 end
function GetEntityCoords(_) return coords end
function GetGameTimer() return clock end
function GetHashKey(v) return v end
function RequestModel(_) end
function HasModelLoaded(_) return true end
function CreateObjectNoOffset(_,x,y,z,network,mission,door) assert(not network);nextentity=nextentity+1;entities[nextentity]={x=x,y=y,z=z};return nextentity end
function SetEntityAsMissionEntity(_,_,_) end
function FreezeEntityPosition(e,t) assert(t) end
function SetEntityCollision(e,t,_) assert(t) end
function SetEntityRotation(e,x,y,z,order,_) assert(order==2);rotations[e]=z end
function SetModelAsNoLongerNeeded(_) end
function DoesEntityExist(e) return entities[e]~=nil end
function DeleteEntity(e) deleted[e]=true;entities[e]=nil end
function IsPedOnFoot(_) return true end
function BeginTextCommandDisplayHelp(_) end
function AddTextComponentSubstringPlayerName(_) end
function EndTextCommandDisplayHelp(_,_,_,_) end
function IsControlJustReleased(_,_) return press end
function TriggerServerEvent(n,...) table.insert(serverevents,{name=n,args={...}}) end
function frame(i) local ok,err=coroutine.resume(threads[i]);assert(ok,err) end
''')
client.execute((D/'portas_client.lua').read_text(encoding='utf-8'))
cg.frame(1);assert len(list(cg.entities.items()))==5;cases.append(dict(name='Five local door props spawned',passed=True))
cg.frame(2);assert cg.serverevents[1]['name']=='cidade_mansao:requestDoorStates'
cg.handlers['cidade_mansao:doorState'](1,True);cg.clock=1275;cg.frame(2);assert abs(cg.rotations[101]+47.5)<1e-5
cg.clock=1550;cg.frame(2);assert cg.rotations[101]==-95;cases.append(dict(name='Smooth opening rotates leaf around hinge',passed=True))
cg.handlers['cidade_mansao:doorState'](1,False);cg.clock=2100;cg.frame(2);assert cg.rotations[101]==0;cases.append(dict(name='Closing restores leaf collision position',passed=True))
cg.coords=cg.vector3(config['origin'][0]+100,config['origin'][1],config['origin'][2]);cg.frame(1);assert len(list(cg.entities.items()))==0;cases.append(dict(name='Leaving area cleans props',passed=True))
cg.coords=cg.vector3(*config['origin']);cg.frame(1);assert len(list(cg.entities.items()))==5
cg.handlers['onResourceStop']('unrelated');assert len(list(cg.entities.items()))==5
cg.handlers['onResourceStop']('cidade_mansao');assert len(list(cg.entities.items()))==0;cases.append(dict(name='Resource stop removes all door props',passed=True))
report=dict(passed=True,doors=len(config['doors']),physical_checks=physical,lua_behavior_cases=cases,leaf_sha256=hashlib.sha256((W/'fivem/mansao_porta_madeira_095.ydr').read_bytes()).hexdigest(),in_game_verified=False)
(W/'verificacao_portas_moveis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('DYNAMIC_DOORS_OK',len(physical),'physics checks;',len(cases),'behavior cases',flush=True)
