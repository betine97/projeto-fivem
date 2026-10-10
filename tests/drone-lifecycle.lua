-- Run with .downloads/lua-tests/node_modules/.bin/fengari tests/drone-lifecycle.lua
-- Simulates API calls, not GTA physics. Regressions: partial creation and stuck pilot.
local commands, threads, entities, api = {}, {}, {[1]=true}, {}
local frozen, cameraActive, cameraPlaced, thrust = false, false, false, 0
local failCreate, failTick, nextEntity = false, false, 10
local vector = {}
local function v(x,y,z) return setmetatable({x=x,y=y,z=z}, vector) end
vector3=v
local bodyPosition=v(0,0,1)
local blocked=false
local keys={[22]=true}
local mouseX,mouseY=0,0
local nextCamera=false
local camFov=0
local clock=1000
local angles={}
vector.__add=function(a,b) return v(a.x+b.x,a.y+b.y,a.z+b.z) end
vector.__sub=function(a,b) return v(a.x-b.x,a.y-b.y,a.z-b.z) end
vector.__mul=function(a,b) return v(a.x*b,a.y*b,a.z*b) end
vector.__len=function(a) return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z) end
function RegisterCommand(name, fn) commands[name]=fn end
function CreateThread(fn) threads[#threads+1]=coroutine.create(fn) end
function Wait() coroutine.yield() end
function exports(name,fn) api[name]=fn end
function PlayerPedId() return 1 end
function DoesEntityExist(id) return entities[id] == true end
function CreateObjectNoOffset() nextEntity=nextEntity+1; entities[nextEntity]=true; return nextEntity end
function DeleteEntity(id) entities[id]=nil end
function SetCgoffset() error('SET_CGOFFSET is unsafe for this drone object') end
function ActivatePhysics() if failCreate then error('injected creation failure') end end
function FreezeEntityPosition(entity,value) if entity==1 then frozen=value end end
function CreateCam() return 99 end
function SetCamCoord() cameraPlaced=true end
function RenderScriptCams(active) if active then assert(cameraPlaced) end; cameraActive=active end
function GetEntityCoords(entity) return entity==1 and v(0,0,1) or bodyPosition end
function SetEntityCoordsNoOffset(_,x,y,z) bodyPosition=v(x,y,z) end
function SetEntityRotation(_,pitch,roll,heading) angles={pitch=pitch,roll=roll,heading=heading} end
function SetEntityVelocity() end
function RequestCollisionAtCoord() end
function IsNuiFocused() return false end
function IsUsingKeyboard() return true end
function GetDisabledControlNormal(_,key) return key==1 and mouseX or mouseY end
function IsDisabledControlJustPressed(_,key)
    if key==0 and nextCamera then nextCamera=false; return true end
    return false
end
function SetCamFov(_,fov) camFov=fov end
function SetCamRot() end
function StopCamPointing() end
function SetEntityLocallyInvisible() end
function PointCamAtCoord() end
function GetOffsetFromEntityInWorldCoords() return v(0,1,1) end
function GetEntityVelocity() if failTick then error('injected frame failure') end; return v(0,0,0) end
function GetEntityRotation() return v(0,0,0) end
function GetEntityRotationVelocity() return v(0,0,0) end
function GetEntityHeading() return 0 end
function GetGameTimer() return clock end
function GetFrameTime() return 1/60 end
function IsDisabledControlPressed(_,key) return keys[key] or false end
function ApplyForceToEntity(_,kind,_,_,z) if kind==0 then thrust=thrust+z end end
function StartShapeTestCapsule() return 1 end
function GetShapeTestResult() return 2,blocked,v(0,0,0),v(0,0,1),0 end
function joaat(name) return name end
for _,name in ipairs({'IsModelInCdimage','IsModelValid','HasModelLoaded'}) do _G[name]=function() return true end end
for _,name in ipairs({'IsPedInAnyVehicle','IsEntityDead','IsPauseMenuActive','HasEntityCollidedWithAnything'}) do _G[name]=function() return false end end
for _,name in ipairs({'BeginTextCommandThefeedPost','AddTextComponentSubstringPlayerName','EndTextCommandThefeedPostTicker','ClearFocus','DestroyCam','SendNUIMessage','RequestModel','SetModelAsNoLongerNeeded','AttachEntityToEntity','SetEntityHeading','SetEntityDynamic','SetEntityCollision','SetEntityHasGravity','SetEntityLoadCollisionFlag','SetEntityRecordsCollisions','SetObjectPhysicsParams','SetEntityVisible','TriggerEvent','PointCamAtEntity','DisableAllControlActions','EnableControlAction','SetFocusPosAndVel','SetEntityAlpha','AddEventHandler'}) do _G[name]=function() end end
dofile('server-data/resources/fpv_drone_runtime/config.lua')
dofile('server-data/resources/fpv_drone_runtime/motor.lua')
dofile('server-data/resources/fpv_drone_runtime/flight.lua')
dofile('server-data/resources/fpv_drone_runtime/client.lua')
commands.dronevoar(); assert(not frozen and not api.isPiloting())
failCreate=true; commands.drone(); commands.dronevoar()
assert(not frozen and not api.isPiloting(), 'Incomplete creation must not lock player')
assert(next(entities)==1 and next(entities,1)==nil, 'Partial object must be deleted')
failCreate=false; commands.drone(); commands.dronevoar()
assert(api.isPiloting() and frozen and cameraActive and cameraPlaced)
assert(coroutine.resume(threads[1])); assert(coroutine.resume(threads[1]))
assert(coroutine.resume(threads[1]))
assert(bodyPosition.z>1 and api.isPiloting(), 'Space input must actually move the object upward')
blocked=true
local stoppedZ=bodyPosition.z
assert(coroutine.resume(threads[1])); assert(coroutine.resume(threads[1]))
assert(bodyPosition.z==stoppedZ, 'Detected obstacle must block movement')
blocked=false
for _,expected in ipairs({78,82,90,75}) do
    nextCamera=true
    assert(coroutine.resume(threads[1]))
    assert(camFov==expected, 'V must cycle all four cameras')
end
mouseX=0.2; mouseY=-0.2; keys={[32]=true}
for i=1,20 do clock=clock+17; assert(coroutine.resume(threads[1])) end
assert(angles.heading<0, 'Mouse right must turn the drone right')
assert(angles.pitch<0, 'Forward input must lean forward')
bodyPosition=v(5000,5000,100)
assert(coroutine.resume(threads[1]))
assert(api.isPiloting(), 'Distance from pilot must not disconnect')
commands.dronedesligar(); commands.dronevoar()
assert(api.isPiloting(), 'Can resume pilot control from far away')
failTick=true; assert(coroutine.resume(threads[1]))
assert(not frozen and not cameraActive and not api.isPiloting(), 'Frame failure must release pilot')
failTick=false; commands.drone(); commands.dronevoar()
assert(api.isPiloting(), 'Must be able to create and pilot again after failure')
commands.droneremover(); assert(not frozen and not cameraActive and not api.isPiloting())
print('OK: incomplete creation, camera placement, input, frame failure cleanup and retry')
