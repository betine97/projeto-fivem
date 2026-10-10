-- Independent hanging PVC strips: slide on the new upper tracks and sway near players.
local origin=vector3(1558.848090595123,847.9298344546474,77.64698791503906)
local heading=-29.15626109700797
local function world(x,y,z)
 return origin+vector3(.873294249*x+.487193139*y,-.487193139*x+.873294249*y,z)
end
local function localXY(pos)
 local dx,dy=pos.x-origin.x,pos.y-origin.y
 return .873294249*dx-.487193139*dy,.487193139*dx+.873294249*dy
end
local groups={}
for _,rack in ipairs({-2.48,2.48}) do
 for _,side in ipairs({-1,1}) do
  local group={rack=rack,side=side,face='side',open=false,slide=0,strips={}}
  for index=1,20 do
   group.strips[index]={index=index,base=-3.70+(index-.5)*.370,
    swayX=0,swayY=0,velocityX=0,velocityY=0}
  end
  groups[#groups+1]=group
 end
 local group={rack=rack,face='front',open=false,slide=0,strips={}}
 for index=1,6 do
  group.strips[index]={index=index,base=-1.08+(index-.5)*.36,
   swayX=0,swayY=0,velocityX=0,velocityY=0}
 end
 groups[#groups+1]=group
end

local model=joaat('lab_vinyl_strip')
local loaded=false
local function removeStrips()
 for _,group in ipairs(groups) do
  for _,strip in ipairs(group.strips) do
   if strip.entity and DoesEntityExist(strip.entity) then DeleteEntity(strip.entity) end
   strip.entity=nil
  end
 end
 loaded=false
end
local function loadStrips()
 if loaded then return true end
 RequestModel(model)
 local deadline=GetGameTimer()+10000
 while not HasModelLoaded(model) and GetGameTimer()<deadline do Wait(0) end
 if not HasModelLoaded(model) then
  print('[Laboratorio] Cortina transparente indisponivel: lab_vinyl_strip')
  return false
 end
 for _,group in ipairs(groups) do
  for _,strip in ipairs(group.strips) do
   local x,y
   if group.face=='side' then
    x=group.rack+group.side*1.07;y=-.8+strip.base
   else x=group.rack+strip.base;y=-4.50 end
   local p=world(x,y,2.95)
   local entity=CreateObjectNoOffset(model,p.x,p.y,p.z,false,false,false)
   if DoesEntityExist(entity) then
    strip.entity=entity
    SetEntityHeading(entity,heading+(group.face=='side' and 90 or 0))
    SetEntityCollision(entity,false,false)
    FreezeEntityPosition(entity,true)
    SetEntityInvincible(entity,true)
    SetEntityLodDist(entity,110)
   end
  end
 end
 SetModelAsNoLongerNeeded(model)
 loaded=true
 print('[Laboratorio] Cortinas moveis carregadas: 92 tiras em 6 trilhos')
 return true
end

local function openPosition(group,index)
 if group.face=='front' then
  if index<=3 then return -1.035+(index-1)*.12 end
  return .795+(index-4)*.12
 end
 if index<=10 then return -3.53+(index-1)*.255 end
 return 1.235+(index-11)*.255
end
local function proximity(group,x,y)
 if group.face=='side' then
  return math.sqrt((x-group.rack-group.side*1.07)^2+
   math.max(math.abs(y+.8)-3.45,0)^2)
 end
 return math.sqrt(math.max(math.abs(x-group.rack)-.95,0)^2+(y+4.5)^2)
end
local function updateStrips(px,py,speed,dt)
 local t=GetGameTimer()*.001
 for groupIndex,group in ipairs(groups) do
  local goal=group.open and 1 or 0
  group.slide=group.slide+(goal-group.slide)*math.min(1,dt*3.0)
  for _,strip in ipairs(group.strips) do
   if strip.entity and DoesEntityExist(strip.entity) then
    local along=strip.base+(openPosition(group,strip.index)-strip.base)*group.slide
    local x,y,yaw
    if group.face=='side' then
     x=group.rack+group.side*1.07;y=-.8+along;yaw=heading+90
    else x=group.rack+along;y=-4.50;yaw=heading end
    local p=world(x,y,2.95)
    local distance=math.sqrt((px-x)^2+(py-y)^2)
    local influence=math.max(0,1-distance/1.85)
    local impulse=math.min(speed,2.2)*.52
    local forceX=influence*(2.3*math.sin(t*3.1+strip.index*.73+groupIndex)+impulse)
    local forceY=influence*(1.8*math.sin(t*2.7+strip.index*.94)+impulse*.6)
    strip.velocityX=strip.velocityX+(forceX-strip.swayX*8-strip.velocityX*5)*dt
    strip.velocityY=strip.velocityY+(forceY-strip.swayY*8-strip.velocityY*5)*dt
    strip.swayX=math.max(-4,math.min(4,strip.swayX+strip.velocityX*dt))
    strip.swayY=math.max(-4,math.min(4,strip.swayY+strip.velocityY*dt))
    SetEntityCoordsNoOffset(strip.entity,p.x,p.y,p.z,false,false,false)
    SetEntityRotation(strip.entity,strip.swayX,strip.swayY,yaw,2,true)
   end
  end
 end
end

CreateThread(function()
 while true do
  local ped=PlayerPedId()
  local pos=GetEntityCoords(ped)
  local distance=#(pos-origin)
  if distance<35 then
   if loadStrips() then
    local px,py=localXY(pos)
    local nearest=nil
    local nearDistance=1.55
    for _,group in ipairs(groups) do
     local d=proximity(group,px,py)
     if d<nearDistance then nearest=group;nearDistance=d end
    end
    if nearest then
     BeginTextCommandDisplayHelp('STRING')
     AddTextComponentSubstringPlayerName('~INPUT_CONTEXT~ Abrir / fechar cortina das plantas')
     EndTextCommandDisplayHelp(0,false,true,-1)
     if IsControlJustPressed(0,38) then nearest.open=not nearest.open end
    end
    updateStrips(px,py,GetEntitySpeed(ped),math.min(GetFrameTime(),.05))
    Wait(0)
   else Wait(2000) end
  else
   if loaded then removeStrips() end
   Wait(1000)
  end
 end
end)
AddEventHandler('onResourceStop',function(name)
 if name==GetCurrentResourceName() then removeStrips() end
end)
