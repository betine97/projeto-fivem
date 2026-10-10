from diagnose import *
import math,hashlib
sys.path.insert(0,str(R/'casa_vinewood/work/lua_syntax_deps'))
from lupa import LuaRuntime
from luaparser import ast
O=P/'package';cfg=json.loads((O/'portas_madeira.json').read_text());tests=0
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
function TriggerClientEvent(name,target,...) emitted[#emitted+1]={name,target,...} end
''')
lua.execute((O/'portas_server.lua').read_text())
def at(p):return lua.table_from(dict(zip(['x','y','z'],[a+b for a,b in zip(cfg['origin'],p)])))
fn=g.handlers['cidade_mansao:toggleDoor']
for d in cfg['doors']:
 c,h=d['opening_center'],d['hinge'];vx,vy=c[0]-h[0],c[1]-h[1];length=math.hypot(vx,vy);normal=[-vy/length,vx/length]
 for side in [-1,1]:
  p=[c[0]+normal[0]*side*.85,c[1]+normal[1]*side*.85,h[2]+.9]
  g.pedpos[1]=at(p);g.pedpos[2]=at([0,0,15]);g.now+=1000;fn(d['id']);ev=g.emitted[len(g.emitted)]
  assert ev[1]=='cidade_mansao:doorState' and ev[2]==-1 and ev[4] is True,(d,ev[1])
  heading=ev[5];assert (heading-d['closed_heading'])*side<0;tests+=1
  # Snapshot includes the chosen angle, including sparse IDs 4 through 9.
  g.handlers['cidade_mansao:requestDoorStates']();ev=g.emitted[len(g.emitted)];assert ev[4][d['id']]==heading;tests+=1
  # Another player within the swept leaf area prevents closing.
  r=math.radians((heading-d['closed_heading'])/2);v=[vx/length*.65*d['width_m'],vy/length*.65*d['width_m']]
  obstacle=[h[0]+v[0]*math.cos(r)-v[1]*math.sin(r),h[1]+v[0]*math.sin(r)+v[1]*math.cos(r),h[2]+.9]
  g.pedpos[2]=at(obstacle);g.now+=1000;fn(d['id']);assert g.emitted[len(g.emitted)][1]=='cidade_mansao:doorOccupied';tests+=1
  g.pedpos[2]=at([0,0,15]);g.now+=1000;fn(d['id']);assert g.emitted[len(g.emitted)][4] is False;tests+=1
  # Obstacle at the future swing rejects opening.
  g.pedpos[2]=at(obstacle);g.now+=1000;fn(d['id']);assert g.emitted[len(g.emitted)][1]=='cidade_mansao:doorOccupied';tests+=1
  g.pedpos[2]=at([0,0,15]);g.pedpos[1]=at([0,0,15]);n=len(g.emitted);g.now+=1000;fn(d['id']);assert len(g.emitted)==n;tests+=1
cl=LuaRuntime(unpack_returned_tuples=True);cg=cl.globals();cg.decode=lambda _:cl.table_from(cfg,recursive=True)
cl.execute('''json={decode=decode};handlers={};threads={};now=0;entities={};rotations={};collisions={};nextEntity=100
local mt={};mt.__sub=function(a,b) return vector3(a.x-b.x,a.y-b.y,a.z-b.z) end
mt.__add=function(a,b) return vector3(a.x+b.x,a.y+b.y,a.z+b.z) end
mt.__len=function(a) return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z) end
function vector3(x,y,z) return setmetatable({x=x,y=y,z=z},mt) end
function GetCurrentResourceName() return 'cidade_mansao' end
function LoadResourceFile(...) return 'doors' end
function RegisterNetEvent(n,f) handlers[n]=f end
function AddEventHandler(n,f) handlers[n]=f end
function CreateThread(f) threads[#threads+1]=coroutine.create(f) end
function Wait(n) coroutine.yield(n) end
function PlayerPedId() return 1 end
function GetEntityCoords(...) return vector3(-976.101013,676.730896,157.835037) end
function GetHashKey(n) return n end
function RequestModel(...) end
function HasModelLoaded(...) return true end
function GetGameTimer() return now end
function CreateObjectNoOffset(...) nextEntity=nextEntity+1;entities[nextEntity]=true;return nextEntity end
function SetEntityAsMissionEntity(...) end
function FreezeEntityPosition(...) end
function SetEntityCollision(e,v,...) collisions[e]=v end
function SetEntityRotation(e,x,y,z,...) rotations[e]=z end
function SetModelAsNoLongerNeeded(...) end
function TriggerServerEvent(...) end
function IsPedOnFoot(...) return false end
function DoesEntityExist(e) return entities[e]==true end
function DeleteEntity(e) entities[e]=nil end
function tick(i) local ok,msg=coroutine.resume(threads[i]);assert(ok,msg) end
''')
cl.execute((O/'portas_client.lua').read_text());cg.tick(1)
assert len([x for x in cg.entities.values()])==len(cfg['doors']);tests+=1
for i,d in enumerate(cfg['doors']):
 chosen=d['closed_heading']+d['swing_degrees'];cg.handlers['cidade_mansao:doorState'](d['id'],True,chosen)
cg.tick(2);assert all(v is False for v in cg.collisions.values());tests+=1
cg.now=600;cg.tick(2);assert all(v is True for v in cg.collisions.values());tests+=1
for i,d in enumerate(cfg['doors']):assert cg.rotations[101+i]==d['closed_heading']+d['swing_degrees'];tests+=1
cg.handlers['onResourceStop']('cidade_mansao');assert not any(cg.entities.values());tests+=1
geomtests=0
for f in S.glob('*ch2_09b_0.ybn'):
 prior=np.array(physical(try_load_asset(f),-origin));n=O/'stream'/f.name;current=np.array(physical(try_load_asset(n if n.exists() else f),-origin))
 for x in np.linspace(3.82,5.65,7):
  edge=16.235+.173*x
  for z in [-2.6,-2.3,-2.,-1.7,-1.2]:
   assert not len(intersections([x,edge+.35,z],[x,edge-.18,z],current)),('Barrier remains',f,x,z);geomtests+=1
  for y in [edge+.15,edge+.35,edge+.65]:
   old=intersections([x,y,-2.1],[x,y,-3.8],prior);new=intersections([x,y,-2.1],[x,y,-3.8],current)
   assert len(old)==len(new) and np.allclose(np.sort(old[:,2]),np.sort(new[:,2]),atol=.002),('Street floor changed',f,x,y);geomtests+=1
# Exposed caps are visible from the access opening. No gap remains at any height.
a=try_load_asset(O/'stream/mansao_paredes.ydr');ts=np.concatenate([g.vertex_buffer['Position'][g.index_buffer.reshape(-1,3)] for m in a.models[LodLevel.HIGH] for g in m.geometries])
for x,side in [(2.6,1),(5.7,-1)]:
 for z in np.linspace(-.75,2.30,18):
  hit=intersections([x+side*.04,2.30,z],[x-side*.04,2.30,z],ts)
  assert len(hit);geomtests+=1
(P/'verification.json').write_text(json.dumps({'passed':True,'door_runtime_cases':tests,'geometry_cases':geomtests,'doors':len(cfg['doors']),'in_game_verified':False},indent=2));print('VERIFIED',tests,geomtests)
