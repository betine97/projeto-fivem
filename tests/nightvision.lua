local commands,threads,events={},{},{}
local effect=false
local pedMode,vehicleMode=0,0
local vehicle,drone,droneFirst,dead=false,false,false,false
local message
function RegisterCommand(n,f) commands[n]=f end
function CreateThread(f) threads[#threads+1]=coroutine.create(f) end
function Wait() coroutine.yield() end
function AddEventHandler(n,f) events[n]=f end
function PlayerPedId() return 1 end
function GetResourceState() return 'started' end
exports={fpv_drone_runtime={isPiloting=function() return drone end,isFirstPerson=function() return droneFirst end,
setFirstPerson=function() droneFirst=true; return true end}}
function IsEntityDead() return dead end
function IsPedInAnyVehicle() return vehicle end
function SetNightvision(v) effect=v end
function SendNUIMessage(v) message=v end
function SetFollowPedCamViewMode(v) pedMode=v end
function SetFollowVehicleCamViewMode(v) vehicleMode=v end
function GetFollowPedCamViewMode() return pedMode end
function GetFollowVehicleCamViewMode() return vehicleMode end
function IsGameplayCamRendering() return true end
function GetFinalRenderedCamRot() return {x=30,y=-10,z=-90} end
function IsPauseMenuActive() return false end
function GetCurrentResourceName() return 'cidade_nightvision' end
dofile('server-data/resources/cidade_nightvision/client.lua')
local function tick() assert(coroutine.resume(threads[1])) end
commands.nightvision(); assert(effect and pedMode==4)
tick(); tick(); assert(message.active and message.heading==90 and message.pitch==30)
pedMode=1; tick(); tick(); assert(not effect and not message.active)
vehicle=true; commands.nightvision(); assert(effect and vehicleMode==4)
tick(); tick(); vehicleMode=0; tick(); tick(); assert(not effect)
vehicle=false; drone=true; commands.nightvision(); assert(effect and droneFirst)
tick(); tick(); droneFirst=false; tick(); tick(); assert(not effect)
commands.nightvision(); assert(effect); commands.nightvision(); assert(not effect)
commands.nightvision(); dead=true; tick(); tick(); assert(not effect)
dead=false; commands.nightvision(); events.onResourceStop('cidade_nightvision'); assert(not effect)
print('OK: force first person, camera telemetry, automatic exit for ped/vehicle/drone, toggle, death and cleanup')
