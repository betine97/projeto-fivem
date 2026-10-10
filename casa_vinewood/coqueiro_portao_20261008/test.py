from diagnose import *
sys.path.insert(0,str(R/'casa_vinewood/work/lua_syntax_deps'))
from luaparser import ast
from lupa import LuaRuntime
O=P/'package';tests=0
a=try_load_asset(O/'stream/mansao_portao_subsolo.ydr');old=try_load_asset(S/'mansao_portao_subsolo.ydr')
ref=None
for lod,models in a.models.items():
 tris=np.concatenate([g.vertex_buffer['Position'][g.index_buffer.reshape(-1,3)] for m in models for g in m.geometries])
 keys=[tuple(sorted(tuple(np.round(p,5)) for p in t)) for t in tris]
 assert len(keys)==len(set(keys));assert np.isfinite(tris).all()
 if ref is None:ref=tris
 else:assert np.array_equal(tris,ref)
 tests+=1
for b,c in zip(a.bounds.children,old.bounds.children):
 assert [str(q) for q in b.geometry_primitives]==[str(q) for q in c.geometry_primitives]
 assert np.allclose([v.co for v in b.geometry_vertices],[v.co for v in c.geometry_vertices],atol=.0001);tests+=1
typ=try_load_asset(O/'stream/mansao_acesso_garagem.ytyp');prior=try_load_asset(S/'mansao_acesso_garagem.ytyp')
assert [str(q) for q in typ.archetypes if str(q.name)!='mansao_portao_subsolo']==[str(q) for q in prior.archetypes if str(q.name)!='mansao_portao_subsolo'];tests+=1
t=next(q for q in typ.archetypes if str(q.name)=='mansao_portao_subsolo');ps=ref.reshape(-1,3)
assert np.all(ps>=np.array(t.bb_min)) and np.all(ps<=np.array(t.bb_max));tests+=1
for f in O.glob('*.lua'):ast.parse(f.read_text());tests+=1
cfg=json.loads((D/'garagem_acesso.json').read_text());lua=LuaRuntime(unpack_returned_tuples=True);g=lua.globals();g.decode=lambda _:lua.table_from(cfg,recursive=True)
lua.execute('''json={decode=decode};handlers={};threads={};now=0;rotation=0;pos=nil;lod=nil;prerender=false
local mt={};mt.__sub=function(a,b) return vector3(a.x-b.x,a.y-b.y,a.z-b.z) end
mt.__add=function(a,b) return vector3(a.x+b.x,a.y+b.y,a.z+b.z) end
mt.__len=function(a) return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z) end
function vector3(x,y,z) return setmetatable({x=x,y=y,z=z},mt) end
function GetCurrentResourceName() return 'cidade_mansao' end
function LoadResourceFile(...) return 'cfg' end
function GetGameTimer() return now end
function RegisterNetEvent(n,f) handlers[n]=f end
function AddEventHandler(n,f) handlers[n]=f end
function RegisterCommand(...) end
function CreateThread(f) threads[#threads+1]=coroutine.create(f) end
function Wait(n) coroutine.yield(n) end
function TriggerServerEvent(...) end
function BeginTextCommandDisplayHelp(...) end
function AddTextComponentSubstringPlayerName(...) end
function EndTextCommandDisplayHelp(...) end
function IsControlJustReleased(...) return false end
function PlayerPedId() return 1 end
function GetEntityCoords(...) return pos or vector3(-966.5,686.2,155.8) end
function GetHashKey(x) return x end
function RequestModel(...) end
function HasModelLoaded(...) return true end
function CreateObjectNoOffset(...) return 22 end
function SetEntityAsMissionEntity(...) end
function SetEntityLodDist(e,n) lod=n end
function SetEntityAlwaysPrerender(e,b) prerender=b end
function FreezeEntityPosition(...) end
function SetEntityCollision(...) end
function SetEntityRotation(e,x,...) rotation=x end
function SetModelAsNoLongerNeeded(...) end
function DoesEntityExist(...) return true end
function DeleteEntity(...) deleted=true end
function tick(i) local ok,msg=coroutine.resume(threads[i]);assert(ok,msg) end
''')
lua.execute((O/'garagem_client.lua').read_text());g.tick(1);assert g.lod==220 and g.prerender is True;tests+=1
handler=g.handlers['cidade_mansao:garageState'];handler(True,False);g.now=450;g.tick(2);partial=g.rotation;assert -90<partial<0;tests+=1
handler(True,True);assert g.rotation==partial;tests+=1
g.now=1800;g.tick(2);assert g.rotation==-90;tests+=1
handler(False,False);g.now=2700;g.tick(2);assert -90<g.rotation<0;tests+=1
g.now=3600;g.tick(2);assert g.rotation==0;tests+=1
g.handlers['onResourceStop']('cidade_mansao');assert g.deleted is True;tests+=1
sv=LuaRuntime(unpack_returned_tuples=True);sg=sv.globals();sg.decode=lambda _:sv.table_from(cfg,recursive=True)
sv.execute('''json={decode=decode};handlers={};emitted={};now=1000;source=1
function GetCurrentResourceName() return 'cidade_mansao' end
function LoadResourceFile(...) return 'cfg' end
function RegisterNetEvent(n,f) handlers[n]=f end
function AddEventHandler(n,f) handlers[n]=f end
function GetGameTimer() return now end
function GetPlayerPed(p) return tonumber(p) end
function GetEntityCoords(p) return {x=-966.5,y=687.8,z=155.4} end
function GetPlayers() return {} end
function GetAllVehicles() return {} end
function DoesEntityExist(...) return true end
function TriggerClientEvent(n,target,...) emitted[#emitted+1]={n,target,...} end
''')
sv.execute((O/'garagem_server.lua').read_text());sg.handlers['cidade_mansao:toggleGarage']();assert len(sg.emitted)==1 and sg.emitted[1][3] is True;tests+=1
sg.source=2;sg.now=1300;sg.handlers['cidade_mansao:toggleGarage']();assert len(sg.emitted)==1;tests+=1
sg.now=3000;sg.handlers['cidade_mansao:toggleGarage']();assert len(sg.emitted)==2 and sg.emitted[2][3] is False;tests+=1
# Targeted palm exclusions apply on load and near streaming, then are cleaned up.
hide=LuaRuntime(unpack_returned_tuples=True);h=hide.globals();hide.execute('''threads={};handlers={};calls={};removed={};far=false
function CreateThread(f) threads[#threads+1]=coroutine.create(f) end
function Wait(n) coroutine.yield(n) end
function GetHashKey(x) return x end
function CreateModelHideExcludingScriptObjects(...) calls[#calls+1]={...} end
function RemoveModelHide(...) removed[#removed+1]={...} end
function PlayerPedId() return 1 end
function GetEntityCoords(...) return far and {x=0,y=0} or {x=-962,y=692} end
function GetCurrentResourceName() return 'cidade_mansao' end
function AddEventHandler(n,f) handlers[n]=f end
function tick() local ok,msg=coroutine.resume(threads[1]);assert(ok,msg) end
''')
hide.execute((O/'exterior_remocoes.lua').read_text());h.tick();assert len(h.calls)==4;tests+=1
h.tick();assert len(h.calls)==8;tests+=1
h.far=True;h.tick();assert len(h.calls)==8;tests+=1
h.handlers['onResourceStop']('cidade_mansao');assert len(h.removed)==4;tests+=1
for i in range(1,5):assert h.calls[i][4]==1.25 and h.calls[i][5] in ['prop_palm_sm_01d','ch2_props_combo0126_11_lod'];tests+=1
(P/'verification.json').write_text(json.dumps({'passed':True,'cases':tests,'gate_triangles_each_lod':len(ref),'duplicate_triangles':0,'snapshot_does_not_interrupt_motion':True,'localized_palm_exclusions':4,'in_game_verified':False},indent=2));print('VERIFIED',tests)
