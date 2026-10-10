-- Two-stop laboratory lift. Floor 0 is the grow room; floor -1 is empty.
local origin=vector3(1558.848090595123,847.9298344546474,77.64698791503906)
local heading=-29.15626109700797
local function world(x,y,z)
 return origin+vector3(.873294249*x+.487193139*y,-.487193139*x+.873294249*y,z)
end
local function localPosition(pos)
 local dx,dy=pos.x-origin.x,pos.y-origin.y
 return .873294249*dx-.487193139*dy,
        .487193139*dx+.873294249*dy,pos.z-origin.z
end
local floors={
 [0]={z=0,open=false,progress=0,doors={}},
 [-1]={z=-8,open=false,progress=0,doors={}},
}
local models={joaat('lab_elev_porta_l'),joaat('lab_elev_porta_r')}
local busy=false
local cooldown=0
local cinematicCam=nil
local savedView=nil
local function sceneCamera(floor)
 local p=world(0,2.35,floors[floor].z+1.75)
 local target=world(0,5.45,floors[floor].z+1.18)
 if not cinematicCam then cinematicCam=CreateCam('DEFAULT_SCRIPTED_CAMERA',true) end
 SetCamCoord(cinematicCam,p.x,p.y,p.z)
 PointCamAtCoord(cinematicCam,target.x,target.y,target.z)
 SetCamFov(cinematicCam,58.0)
 RenderScriptCams(true,false,0,true,true)
end
local function finishScene()
 local ped=PlayerPedId()
 ClearPedTasks(ped)
 FreezeEntityPosition(ped,false)
 if cinematicCam then
  RenderScriptCams(false,false,0,true,true)
  DestroyCam(cinematicCam,false)
  cinematicCam=nil
 end
 if savedView then SetFollowPedCamViewMode(savedView);savedView=nil end
 SetGameplayCamRelativeHeading(0)
 SetGameplayCamRelativePitch(0,1.0)
 LocalPlayer.state:set('labElevatorBusy',false,false)
 busy=false
 cooldown=GetGameTimer()+1500
end
local function sceneWait(duration)
 local deadline=GetGameTimer()+duration
 while GetGameTimer()<deadline do
  if IsPedDeadOrDying(PlayerPedId(),true) then error('viagem interrompida') end
  Wait(0)
 end
end
local function walkTo(x,y,z,finalHeading)
 local ped=PlayerPedId()
 local target=world(x,y,z)
 TaskGoStraightToCoord(ped,target.x,target.y,target.z,1.0,8000,finalHeading,.10)
 local deadline=GetGameTimer()+8000
 while GetGameTimer()<deadline do
  local p=GetEntityCoords(ped)
  if ((p.x-target.x)^2+(p.y-target.y)^2)<.035 then
   ClearPedTasks(ped)
   return
  end
  if IsPedDeadOrDying(ped,true) then error('viagem interrompida') end
  Wait(0)
 end
 error('caminho do elevador bloqueado; controle devolvido')
end

local function floorAt(z)
 if math.abs(z)<2.8 then return 0 end
 if math.abs(z+8)<2.8 then return -1 end
 return nil
end
local function loadDoors()
 if floors[0].doors[1] and DoesEntityExist(floors[0].doors[1]) then return true end
 for _,model in ipairs(models) do RequestModel(model) end
 local deadline=GetGameTimer()+8000
 while (not HasModelLoaded(models[1]) or not HasModelLoaded(models[2])) and
       GetGameTimer()<deadline do Wait(0) end
 if not HasModelLoaded(models[1]) or not HasModelLoaded(models[2]) then
  print('[Laboratorio] ERRO: folhas do elevador indisponiveis')
  return false
 end
 for _,floor in pairs(floors) do
  for index,side in ipairs({-1,1}) do
   local p=world(side*.52,4.65,floor.z+1.14)
   local door=CreateObjectNoOffset(models[index],p.x,p.y,p.z,false,false,false)
   if DoesEntityExist(door) then
    SetEntityHeading(door,heading)
    FreezeEntityPosition(door,true)
    SetEntityInvincible(door,true)
    SetEntityCollision(door,true,true)
    floor.doors[index]=door
   end
  end
 end
 for _,model in ipairs(models) do SetModelAsNoLongerNeeded(model) end
 print('[Laboratorio] Elevador pronto: andares 0 e -1')
 return true
end

local function removeDoors()
 for _,floor in pairs(floors) do
  for _,door in pairs(floor.doors) do
   if DoesEntityExist(door) then DeleteEntity(door) end
  end
  floor.doors={}
  floor.open=false
  floor.progress=0
 end
end

local function animateDoors(dt)
 for _,floor in pairs(floors) do
  local target=floor.open and 1 or 0
  floor.progress=floor.progress+(target-floor.progress)*math.min(1,dt*3.2)
  for index,side in ipairs({-1,1}) do
   local door=floor.doors[index]
   if door and DoesEntityExist(door) then
    local x=side*(.52+.63*floor.progress)
    local p=world(x,4.65,floor.z+1.14)
    SetEntityCoordsNoOffset(door,p.x,p.y,p.z,false,false,false)
    SetEntityCollision(door,floor.progress<.12,floor.progress<.12)
   end
  end
 end
end

local function travel(current)
 if busy or GetGameTimer()<cooldown then return end
 local ped=PlayerPedId()
 if IsPedInAnyVehicle(ped,false) or IsPedDeadOrDying(ped,true) then return end
 busy=true
 savedView=GetFollowPedCamViewMode()
 LocalPlayer.state:set('labElevatorBusy',true,false)
 local ok,err=xpcall(function()
  local destination=(current==0) and -1 or 0
  local _,_,pedZ=localPosition(GetEntityCoords(ped))
  local height=pedZ-floors[current].z
  sceneCamera(current)
  floors[current].open=true
  sceneWait(1350)
  walkTo(0,4.40,floors[current].z+height,heading)
  walkTo(0,6.05,floors[current].z+height,heading)
  TaskAchieveHeading(ped,(heading+180)%360,1000)
  sceneWait(1100)
  floors[current].open=false
  sceneWait(1400)
  FreezeEntityPosition(ped,true)
  DoScreenFadeOut(400)
  sceneWait(500)
  local p=world(0,6.05,floors[destination].z+height)
  RequestCollisionAtCoord(p.x,p.y,p.z)
  SetEntityCoordsNoOffset(ped,p.x,p.y,p.z,false,false,false)
  SetEntityHeading(ped,(heading+180)%360)
  local deadline=GetGameTimer()+5000
  while not HasCollisionLoadedAroundEntity(ped) and GetGameTimer()<deadline do
   RequestCollisionAtCoord(p.x,p.y,p.z)
   sceneWait(50)
  end
  if not HasCollisionLoadedAroundEntity(ped) then error('colisao do destino indisponivel') end
  sceneCamera(destination)
  floors[destination].open=true
  DoScreenFadeIn(400)
  sceneWait(1350)
  FreezeEntityPosition(ped,false)
  walkTo(0,3.65,floors[destination].z+height,(heading+180)%360)
  floors[destination].open=false
  sceneWait(350)
  print(('[Laboratorio] Elevador: saida automatica concluida no andar %d'):format(destination))
 end,debug.traceback)
 finishScene()
 if not ok then
  for _,floor in pairs(floors) do floor.open=true end
  DoScreenFadeIn(200)
  print('[Laboratorio] Elevador: '..tostring(err))
 end
end

CreateThread(function()
 while true do
  local ped=PlayerPedId()
  local pos=GetEntityCoords(ped)
  local x,y,z=localPosition(pos)
  local floorNumber=floorAt(z)
  if floorNumber and math.abs(x)<25 and math.abs(y)<25 then
   if loadDoors() then
    local floor=floors[floorNumber]
    animateDoors(math.min(GetFrameTime(),.05))
    local inFront=math.abs(x)<1.08 and y>3.25 and y<4.95
    if inFront and not busy then
     BeginTextCommandDisplayHelp('STRING')
     AddTextComponentSubstringPlayerName('~INPUT_CONTEXT~ Entrar no elevador')
     EndTextCommandDisplayHelp(0,false,true,-1)
     if IsControlJustPressed(0,38) then CreateThread(function() travel(floorNumber) end) end
    end
    local lamp=world(0,6.30,floor.z+2.12)
    DrawLightWithRange(lamp.x,lamp.y,lamp.z,235,244,255,3.0,5.0)
    if floorNumber==-1 then
     local center=world(0,0,-4.6)
     DrawLightWithRange(center.x,center.y,center.z,210,215,220,9.5,1.35)
    end
    Wait(0)
   else Wait(2000) end
  else
   if floors[0].doors[1] then removeDoors() end
   Wait(1000)
  end
 end
end)
AddEventHandler('onResourceStop',function(resource)
 if resource==GetCurrentResourceName() then
  removeDoors()
  SetPedMaxMoveBlendRatio(PlayerPedId(),3.0)
  if busy then finishScene();DoScreenFadeIn(0) end
 end
end)

local movementLimited=false
-- Keep AI walking tasks active while ignoring player input during the scene.
CreateThread(function()
 while true do
  local ped=PlayerPedId()
  local x,y,z=localPosition(GetEntityCoords(ped))
  local basement=math.abs(z+8)<3.0 and math.abs(x)<4.3 and y>-6.3 and y<7.7
  if busy then
   DisableAllControlActions(0)
   DisableAllControlActions(1)
   DisableAllControlActions(2)
   EnableControlAction(0,199,true)
   EnableControlAction(0,200,true)
  elseif basement then
   DisableControlAction(0,21,true)
   SetPedMaxMoveBlendRatio(ped,1.5)
   movementLimited=true
  elseif movementLimited then
   SetPedMaxMoveBlendRatio(ped,3.0)
   movementLimited=false
  end
  if basement or busy then Wait(0) else Wait(150) end
 end
end)
