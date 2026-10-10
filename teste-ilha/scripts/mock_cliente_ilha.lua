commands={};logs={};threads={};clock=0;frozen=false;focus=false;controlled=false;cameraReleased=false
json={decode=function(s)if s=='maps' then return {'bh1_09_strm_0','test_dlc_map'} end return config end}
function LoadResourceFile(r,n)return n=='data/mapas_originais.json' and 'maps' or '{}'end
function GetCurrentResourceName()return 'teste_ilha'end
exports=setmetatable({}, {__call=function(t,n,f)t[n]=f end,__index=function(t,n)return t end})
function RegisterCommand(n,f)commands[n]=f end
function CreateThread(f)threads[#threads+1]=f end
function RegisterNUICallback()end;function AddEventHandler()end
function GetHashKey(n)return n end;function IsModelInCdimage()return city or false end;function IsIplActive()return false end
function LoadWaterFromPath()return waterResult end
function GetWaterQuadCount()if waterDelayed and clock<200 then return 559 end return count end
function SetDeepOceanScaler()end
function SetWaterAreaClipRect()error('Do not expand the engine water grid')end
function print(s)logs[#logs+1]=s end
function BeginTextCommandThefeedPost()end;function AddTextComponentSubstringPlayerName()end;function EndTextCommandThefeedPostTicker()end
function PlayerPedId()return 1 end;function PlayerId()return 0 end;function IsPedInAnyVehicle()return vehicle end
function TriggerEvent()end;function GetResourceState()return 'missing'end
function FreezeEntityPosition(p,v)frozen=v end;function DoScreenFadeOut()end;function DoScreenFadeIn()fadedIn=true end
function Wait(ms)clock=clock+math.max(ms,1) end;function GetGameTimer()return clock end
function RequestCollisionAtCoord()end;function NewLoadSceneStartSphere()scene=true end;function NewLoadSceneStop()scene=false end
function SetEntityCoordsNoOffset(p,x,y,z)moved={x=x,y=y,z=z}end;function SetEntityHeading()end;function SetEntityVelocity()end
function GetEntityCoords()return moved or {x=0,y=0,z=18}end;function GetEntityHeading()return 90 end
function HasCollisionLoadedAroundEntity()return collision end
function GetGroundZFor_3dCoord(x,y)
    if brokenNative then error('simulated native failure') end
    if math.abs(x-config.spawn.x)<.01 then return runwayGround or collision,18 end
    if badGround then return true,70 end
    return collision,config.natural_sample.spawn.z-1.15
end
function ClearFocus()focus=false end;function SetFocusPosAndVel()focus=true end
function RenderScriptCams(v)cameraReleased=not v end
function SetEntityCollision(p,v)entityCollision=v end;function SetEntityVisible(p,v)visible=v end
function SetEntityHasGravity(p,v)gravity=v end;function SetPlayerControl(p,v)controlled=v end
function SetNuiFocus(v)nuiFocus=v end;function SendNUIMessage()end
function RequestModel()end;function SetModelAsNoLongerNeeded()end
function HasModelLoaded()return not missingModels end
function RequestIpl()end;function RemoveIpl(n)removedMaps=removedMaps or {};removedMaps[n]=true end
function GetClosestObjectOfType()return 0 end
