"""Execute the real Lua client under mocked natives: motion, settling, removal."""
import sys,json
from pathlib import Path
base=Path(__file__).resolve().parent
sys.path.insert(0,str(base/'test_deps'))
from lupa import LuaRuntime
lua=LuaRuntime(unpack_returned_tuples=True)
lua.globals().config_json=(base/'strap-config.json').read_text()
lua.globals().decode_json=lambda _: lua.table_from([lua.table_from(x,recursive=True) for x in json.loads(lua.globals().config_json)])
lua.execute('''
local vector={};local mt={__index=vector}
function V(x,y,z)return setmetatable({x=x,y=y,z=z},mt)end
mt.__add=function(a,b)return V(a.x+b.x,a.y+b.y,a.z+b.z)end
mt.__sub=function(a,b)return V(a.x-b.x,a.y-b.y,a.z-b.z)end
mt.__mul=function(a,b) if type(a)=='number' then a,b=b,a end;return V(a.x*b,a.y*b,a.z*b)end
mt.__div=function(a,b)return V(a.x/b,a.y/b,a.z/b)end
mt.__len=function(a)return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z)end
threads={};events={};objects={};matrices={};speed=0;equipped=true;deleted=0
json={decode=decode_json}
function LoadResourceFile()return config_json end
function GetCurrentResourceName()return 'cidade_roupas'end
function CreateThread(fn)threads[#threads+1]=coroutine.create(fn)end
function Wait(ms)coroutine.yield(ms)end
function joaat(x)return x end
function RequestModel()end
function HasModelLoaded()return true end
function GetGameTimer()return 0 end
function PlayerPedId()return 1 end
function GetPlayerPed()return 1 end
function GetActivePlayers()return {0}end
function DoesEntityExist(x)return x==1 or objects[x]~=nil end
function GetEntityModel()return 'mp_m_freemode_01'end
function GetPedDrawableVariationCollectionName()return equipped and 'Male_Heist' or ''end
function GetPedDrawableVariationCollectionLocalIndex()return 6 end
function GetPedTextureVariation()return 0 end
function GetEntityCoords()return V(0,0,0)end
function GetEntityVelocity()return V(speed,0,0)end
function CreateObjectNoOffset()local id=100+#objects+1; while objects[id] do id=id+1 end;objects[id]=true;return id end
function SetEntityAsMissionEntity()end
function SetEntityCollision()end
function FreezeEntityPosition()end
function SetEntityVisible()end
function DeleteEntity(id) objects[id]=nil;deleted=deleted+1 end
function SetModelAsNoLongerNeeded()end
function GetFrameTime()return 1/60 end
function GetPedBoneCoords(ped,bone,x,y,z)return V(x,y,z)end
function IsPedInAnyVehicle()return false end
function IsEntityDead()return false end
function SetEntityMatrix(id,...)matrices[id]={...}end
function AddEventHandler(event,fn)events[event]=fn end
function step(index)
  local ok,err=coroutine.resume(threads[index]);assert(ok,err)
end
function measure()
 local sum=0;for _,matrix in pairs(matrices)do for _,v in ipairs(matrix)do assert(v==v and math.abs(v)<10);sum=sum+v end end;return sum
end
''')
script=base.parents[1]/'server-data/resources/cidade_roupas/tactical_straps.lua'
lua.execute(script.read_text())
lua.execute('step(1);step(2);rest=measure();speed=2')
lua.execute('for i=1,120 do step(2) end;moving=measure();assert(math.abs(moving-rest)>.001);speed=0')
lua.execute('for i=1,600 do step(2) end;settled=measure();assert(math.abs(settled-rest)<.01)')
lua.execute("equipped=false;step(1);assert(deleted==3);equipped=true;step(1);events.onResourceStop('cidade_roupas');assert(deleted==6)")
print('LUA_RUNTIME_OK: three objects, movement, settling, outfit removal and resource cleanup')
