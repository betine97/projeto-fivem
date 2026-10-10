local origin=vector3(1558.848090595123,847.9298344546474,77.64698791503906)
local heading=-29.15626109700797
local function world(x,y,z)
 return origin+vector3(.873294249*x+.487193139*y,-.487193139*x+.873294249*y,z)
end
local doorPos=world(-3.312,-7.961615,0)
local door,opening=false,false
local tabletOpen=false
local labTone=false
local rainMuted=false
local nextRainRefresh=0
local function insideLab(pos)
 local dx,dy=pos.x-origin.x,pos.y-origin.y
 local x=.873294249*dx-.487193139*dy
 local y=.487193139*dx+.873294249*dy
 local z=pos.z-origin.z
 return (z>-.2 and z<3.7 and
  ((x>-4.1 and x<4.1 and y>-6.1 and y<6.1) or
   (x>-3.9 and x<1.8 and y>-8.1 and y<=-6.1) or
   (x>-1.2 and x<1.2 and y>=6.1 and y<7.4))) or
  (z>-8.3 and z<-4.2 and x>-4.1 and x<4.1 and y>-6.1 and y<7.5)
end
local function updateIndoorRain(pos)
 local indoors=insideLab(pos)
 if indoors then
  if not rainMuted or GetGameTimer()>=nextRainRefresh then
   SetRainLevel(0.0)
   rainMuted=true
   nextRainRefresh=GetGameTimer()+1000
  end
 elseif rainMuted then
  SetRainLevel(-1.0)
  rainMuted=false
 end
end
local function closeTablet()
 if not tabletOpen then return end
 tabletOpen=false
 SetNuiFocus(false,false)
 SendNUIMessage({action='close'})
end
local function openTablet()
 if tabletOpen then return end
 local ped=PlayerPedId()
 if IsPedDeadOrDying(ped,true) or IsPedInAnyVehicle(ped,false) then return end
 tabletOpen=true
 SetNuiFocus(true,true)
 SendNUIMessage({action='open'})
end
RegisterNUICallback('close',function(_,cb) closeTablet();cb({ok=true}) end)
local fanDefs={
 {'lab_rotor_ceiling',0,-3.2667,2.56,'z',1},
 {'lab_rotor_ceiling',0,-.8,2.56,'z',1},
 {'lab_rotor_ceiling',0,1.6667,2.56,'z',1},
 {'lab_rotor_left',-3.80,-2.4,2.6,'x',-1},
 {'lab_rotor_left',-3.80,-.8,2.6,'x',-1},
 {'lab_rotor_left',-3.80,1.6667,2.6,'x',-1},
 {'lab_rotor_right',3.80,-3.2667,2.6,'x',1},
 {'lab_rotor_right',3.80,-.8,2.6,'x',1},
 {'lab_rotor_right',3.80,1.6667,2.6,'x',1},
 {'lab_rotor_rear_left',-3.15,5.79,2.93,'y',1},
 {'lab_rotor_rear_right',3.15,5.79,2.93,'y',1},
}
local rotors={}
local function loadRotors()
 if #rotors==#fanDefs then return end
 for _,r in ipairs(rotors) do if DoesEntityExist(r.entity) then DeleteEntity(r.entity) end end
 rotors={}
 for _,f in ipairs(fanDefs) do
  local hash=joaat(f[1]);RequestModel(hash);local deadline=GetGameTimer()+5000
  while not HasModelLoaded(hash) and GetGameTimer()<deadline do Wait(0) end
  if not HasModelLoaded(hash) then print('[Laboratorio] ERRO: helice indisponivel '..f[1]);return end
  local p=world(f[2],f[3],f[4]);local obj=CreateObjectNoOffset(hash,p.x,p.y,p.z,false,false,false)
  if not DoesEntityExist(obj) then print('[Laboratorio] ERRO: nao foi possivel criar '..f[1]);return end
  SetEntityHeading(obj,heading);SetEntityCollision(obj,false,false);FreezeEntityPosition(obj,true)
  local x,y,z,w=GetEntityQuaternion(obj)
  rotors[#rotors+1]={entity=obj,base={x,y,z,w},axis=f[5],direction=f[6]}
  SetModelAsNoLongerNeeded(hash)
 end
end
local function turnRotors()
 local angle=(GetGameTimer()%3000)*(math.pi*2/3000)
 for _,r in ipairs(rotors) do
  if DoesEntityExist(r.entity) then
   local half=angle*r.direction*.5;local s=math.sin(half);local c=math.cos(half)
   local ax,ay,az=0,0,0
   if r.axis=='x' then ax=s elseif r.axis=='y' then ay=s else az=s end
   local b=r.base;local x,y,z,w=b[1],b[2],b[3],b[4]
   SetEntityQuaternion(r.entity,w*ax+x*c+y*az-z*ay,w*ay-x*az+y*c+z*ax,w*az+x*ay-y*ax+z*c,w*c-x*ax-y*ay-z*az)
  end
 end
end
local function notice(t)
 BeginTextCommandThefeedPost('STRING');AddTextComponentSubstringPlayerName(t);EndTextCommandThefeedPostTicker(false,false)
end
local function loadDoor()
 if door and DoesEntityExist(door) then return true end
 local model=joaat('lab_porta');RequestModel(model);local deadline=GetGameTimer()+10000
 while not HasModelLoaded(model) and GetGameTimer()<deadline do Wait(0) end
 if not HasModelLoaded(model) then print('[Laboratorio] ERRO: modelo da porta indisponivel');return false end
 door=CreateObjectNoOffset(model,doorPos.x,doorPos.y,doorPos.z,false,false,false)
 SetEntityHeading(door,heading);FreezeEntityPosition(door,true);SetEntityInvincible(door,true);SetModelAsNoLongerNeeded(model)
 return true
end
local angle=0;local target=0
local function checkLabClearance()
 CreateThread(function()
  for _,test in ipairs({
   {'entrada externa',-2.695,-8.55,-2.695,-7.40},
   {'vestibulo interno',0,-6.65,0,-5.35},
   {'corredor lateral',-3.30,-2.30,-3.30,-1.20},
   {'aproximacao porta fundo',0,4.65,0,5.65},
  }) do
   local a=world(test[2],test[3],1.0);local b=world(test[4],test[5],1.0)
   local h=StartShapeTestLosProbe(a.x,a.y,a.z,b.x,b.y,b.z,17,PlayerPedId(),7)
   local state,hit,point,normal,entity=GetShapeTestResult(h)
   while state==1 do Wait(0);state,hit,point,normal,entity=GetShapeTestResult(h) end
   print(('[Laboratorio] colisao %s: resultado=%s atingiu=%s entidade=%s pos=%.2f,%.2f,%.2f'):format(test[1],tostring(state),tostring(hit),tostring(entity),point.x,point.y,point.z))
  end
 end)
end
CreateThread(function()
 while true do
  local pos=GetEntityCoords(PlayerPedId());local dist=#(pos-origin)
  if dist<100 then
   updateIndoorRain(pos)
   loadDoor()
   loadRotors()
   turnRotors()
   if door and DoesEntityExist(door) then
    if math.abs(angle-target)>.1 then angle=angle+(target-angle)*math.min(1,GetFrameTime()*5);SetEntityHeading(door,heading+angle) end
    if #(pos-world(-2.695,-7.96,1))<2.2 then
     BeginTextCommandDisplayHelp('STRING');AddTextComponentSubstringPlayerName('~INPUT_CONTEXT~ Abrir / fechar laboratorio');EndTextCommandDisplayHelp(0,false,true,-1)
     if IsControlJustPressed(0,38) then opening=not opening;target=opening and 105 or 0;SetEntityCollision(door,not opening,not opening);if opening then checkLabClearance() end end
    end
   end
   -- The native building was authored as a closed shell. Disable its camera
   -- occlusion only while the player is at this custom interior/doorway.
   if dist<17 then DisableOcclusionThisFrame() end
   if dist<14 and not labTone then
    SetTimecycleModifier('V_FIB_IT3');SetTimecycleModifierStrength(1.0);labTone=true
   elseif dist>=14 and labTone then
    ClearTimecycleModifier();labTone=false
   end
   if tabletOpen and IsPedDeadOrDying(PlayerPedId(),true) then closeTablet() end
   if dist<14 and not LocalPlayer.state.labElevatorBusy and not tabletOpen and #(pos-world(1.67,4.35,.85))<1.45 then
    BeginTextCommandDisplayHelp('STRING');AddTextComponentSubstringPlayerName('~INPUT_CONTEXT~ Usar computador');EndTextCommandDisplayHelp(0,false,true,-1)
    if IsControlJustPressed(0,38) then openTablet() end
   end
   if dist<25 then
    for _,x in ipairs({-2.475,2.475}) do
     for _,y in ipairs({-3.267,-.8,1.667}) do
      local l=world(x,y,2.73);DrawLightWithRange(l.x,l.y,l.z,255,24,42,4.7,5.0)
     end
    end
    for _,y in ipairs({-6.8,-3,1,4.6}) do local l=world(0,y,3.15);DrawLightWithRange(l.x,l.y,l.z,170,160,160,2.4,.12) end
   end
   Wait(0)
  else
   if rainMuted then SetRainLevel(-1.0);rainMuted=false end
   if labTone then ClearTimecycleModifier();labTone=false end
   if tabletOpen then closeTablet() end
   if door and DoesEntityExist(door) then DeleteEntity(door);door=nil end
   for _,r in ipairs(rotors) do if DoesEntityExist(r.entity) then DeleteEntity(r.entity) end end
   rotors={}
   Wait(1000)
  end
 end
end)
local function visit(x,y,z)
 local ped=PlayerPedId();local p=world(x,y,z);RequestCollisionAtCoord(p.x,p.y,p.z);FreezeEntityPosition(ped,true)
 SetEntityCoordsNoOffset(ped,p.x,p.y,p.z,false,false,false);SetEntityHeading(ped,heading)
 SetGameplayCamRelativeHeading(0);SetGameplayCamRelativePitch(0,1)
 local untilTime=GetGameTimer()+5000
 while not HasCollisionLoadedAroundEntity(ped) and GetGameTimer()<untilTime do Wait(50);RequestCollisionAtCoord(p.x,p.y,p.z) end
 FreezeEntityPosition(ped,false)
end
RegisterCommand('laboratorio',function() CreateThread(function() visit(-2.695,-10.2,1);notice('Laboratorio: use E junto a porta.');print('[Laboratorio] Entrada: 1552.62, 842.29, 77.65') end) end,false)
RegisterCommand('labinterior',function() CreateThread(function() visit(0,-4.9,1);print('[Laboratorio] Visita tecnica ao interior') end) end,false)
RegisterCommand('labporta',function() if #(GetEntityCoords(PlayerPedId())-origin)<25 then opening=not opening;target=opening and 105 or 0;if door and DoesEntityExist(door) then SetEntityCollision(door,not opening,not opening) end end end,false)
RegisterCommand('labdiagnostico',function()
 local p=GetEntityCoords(PlayerPedId());print(('[Laboratorio] jogador %.3f %.3f %.3f porta=%s'):format(p.x,p.y,p.z,tostring(door and DoesEntityExist(door))))
end,false)
RegisterCommand('labcolisao',checkLabClearance,false)
RegisterCommand('labtablet',function() if #(GetEntityCoords(PlayerPedId())-world(1.67,4.35,.85))<1.6 then openTablet() end end,false)
AddEventHandler('onResourceStop',function(r)
 if r~=GetCurrentResourceName() then return end
 if tabletOpen then closeTablet() end
 if rainMuted then SetRainLevel(-1.0);rainMuted=false end
 if labTone then ClearTimecycleModifier();labTone=false end
 if door and DoesEntityExist(door) then DeleteEntity(door) end
 for _,fan in ipairs(rotors) do if DoesEntityExist(fan.entity) then DeleteEntity(fan.entity) end end
end)
print('[Laboratorio] Recurso carregado. Comando: laboratorio')
