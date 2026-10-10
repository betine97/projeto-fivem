from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent/'test_deps'))
from lupa import LuaRuntime
source=Path('server-data/resources/cidade_laboratorio/client_elevator.lua').read_text()
mock=r"""
local mt={}
mt.__add=function(a,b)return vector3(a.x+b.x,a.y+b.y,a.z+b.z)end
function vector3(x,y,z)return setmetatable({x=x,y=y,z=z},mt)end
threads={}; events={}; clock=0; pos=vector3(1560.602,851.074,78.647); view=1; frozen=false; busyState=false; camAlive=false; headingSet=nil; steps=0; controls={}; ratio=nil
LocalPlayer={state={set=function(_,_,v)busyState=v end}}
function CreateThread(f)threads[#threads+1]=f end
function AddEventHandler(n,f)events[n]=f end
function joaat(s)return s end
function PlayerPedId()return 1 end
function GetEntityCoords()return pos end
function GetGameTimer()return clock end
function Wait(n)clock=clock+math.max(n,16)end
function IsPedDeadOrDying()return dead or false end
function IsPedInAnyVehicle()return false end
function GetFollowPedCamViewMode()return view end
function SetFollowPedCamViewMode(v)view=v end
function CreateCam()camAlive=true;return 42 end
function DestroyCam()camAlive=false end
function FreezeEntityPosition(_,v)frozen=v end
function TaskGoStraightToCoord(_,x,y,z)steps=steps+1;if not blocked then pos=vector3(x,y,z)end end
function SetEntityCoordsNoOffset(_,x,y,z)pos=vector3(x,y,z)end
function SetEntityHeading(_,v)headingSet=v end
function HasCollisionLoadedAroundEntity()return not missingCollision end
function GetCurrentResourceName()return 'cidade_laboratorio' end
function DoesEntityExist()return false end
function DisableControlAction(_,n)controls[n]=true end
function DisableAllControlActions(n)controls['all'..n]=true end
function SetPedMaxMoveBlendRatio(_,v)ratio=v end
for _,n in ipairs({'SetCamCoord','PointCamAtCoord','SetCamFov','RenderScriptCams','ClearPedTasks','SetGameplayCamRelativeHeading','SetGameplayCamRelativePitch','TaskAchieveHeading','DoScreenFadeOut','DoScreenFadeIn','RequestCollisionAtCoord','DeleteEntity','EnableControlAction'})do _G[n]=function()end end
"""
for case in ['success','blocked','dead','missing_collision']:
 lua=LuaRuntime(unpack_returned_tuples=True);lua.execute(mock)
 api=lua.execute(source+'\nreturn {travel=travel,busy=function()return busy end,world=world,localPosition=localPosition}\n')
 lua.globals().pos=api.world(0,3.65,1)
 if case=='blocked':lua.globals().blocked=True
 if case=='dead':lua.globals().dead=True
 if case=='missing_collision':lua.globals().missingCollision=True
 api.travel(0)
 g=lua.globals();assert not api.busy() and not g.frozen and not g.camAlive and not g.busyState,case
 if case=='success':
  x,y,z=api.localPosition(g.pos);assert abs(y-3.65)<.001 and abs(z+7)<.001
  assert abs(g.headingSet-150.843738902992)<.001 and g.steps==3
  assert g.view==1
 print('PASS',case,'control restored')
# Run one frame of the input limiter, then leave the basement.
lua=LuaRuntime(unpack_returned_tuples=True);lua.execute(mock);api=lua.execute(source+'\nreturn {world=world}\n');g=lua.globals();g.pos=api.world(0,0,-7)
lua.execute('Wait=function()coroutine.yield()end; limiter=coroutine.create(threads[2]);assert(coroutine.resume(limiter))')
assert g.controls[21] and g.ratio==1.5
g.pos=api.world(0,0,1);lua.execute('assert(coroutine.resume(limiter))');assert g.ratio==3.0
print('PASS basement speed limit and restoration')
