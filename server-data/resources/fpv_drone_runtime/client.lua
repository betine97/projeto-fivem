local body, camera, pilot, origin
local motors, busy, flying, armed = {}, false, false, false
local lastVelocity, collisionLast, impactTime = nil, false, 0
local casts = {}
local movementProbe, probeStart, probeGoal, probeStarted
local corridorStart, corridorEnd, corridorTime
local flightState, cameraPosition
local cameraMode=1
local soundLevel=0.8
local soundTestUntil=0
local inputState = {forward=0, side=0, up=0, yaw=0}
local function clamp(x,a,b) return math.max(a,math.min(b,x)) end
local function message(s)
    print('[Drone] '..s)
    BeginTextCommandThefeedPost('STRING'); AddTextComponentSubstringPlayerName(s); EndTextCommandThefeedPostTicker(false,false)
end
local function releasePilot()
    local wasFlying=flying
    flying=false
    movementProbe=nil; corridorStart=nil; corridorEnd=nil; flightState=nil; cameraPosition=nil
    if wasFlying and body and DoesEntityExist(body) then
        FreezeEntityPosition(body,false)
        SetEntityHasGravity(body,true)
        ActivatePhysics(body)
    end
    if camera then RenderScriptCams(false,false,0,true,true); DestroyCam(camera,false); camera=nil end
    ClearFocus()
    if pilot and DoesEntityExist(pilot) then
        local p=GetEntityCoords(pilot)
        RequestCollisionAtCoord(p.x,p.y,p.z)
    end
    if pilot and DoesEntityExist(pilot) then FreezeEntityPosition(pilot,false) end
    pilot=nil
end
local function shutdown()
    releasePilot(); armed=false
    SendNUIMessage({type='droneAudio', volume=0})
    for _,m in ipairs(motors) do m.target=0 end
end
local function remove()
    shutdown()
    for _,m in ipairs(motors) do
        if DoesEntityExist(m.entity) then DeleteEntity(m.entity) end
        if DoesEntityExist(m.blur) then DeleteEntity(m.blur) end
    end
    motors={}; casts={}
    if body and DoesEntityExist(body) then DeleteEntity(body) end
    body=nil; origin=nil; busy=false; lastVelocity=nil; collisionLast=false
end
local function load(name)
    local hash=joaat(name)
    if not IsModelInCdimage(hash) or not IsModelValid(hash) then return nil end
    RequestModel(hash); local deadline=GetGameTimer()+10000
    while not HasModelLoaded(hash) and GetGameTimer()<deadline do Wait(10) end
    if not HasModelLoaded(hash) then SetModelAsNoLongerNeeded(hash); return nil end
    return hash
end
local function attach(entity,cfg,angle)
    AttachEntityToEntity(entity,body,-1,cfg.x,cfg.y,cfg.z,0.0,0.0,angle,false,false,false,false,2,true)
end

local function updateCamera(dt,instant)
    local mode=Config.cameras[cameraMode]
    local p=GetEntityCoords(body)
    local h,pitch=math.rad(flightState.heading),math.rad(flightState.look)
    local forward=vector3(-math.sin(h)*math.cos(pitch),math.cos(h)*math.cos(pitch),math.sin(pitch))
    local desired=p-forward*mode.distance+vector3(0,0,mode.height)
    if instant or mode.firstPerson or not cameraPosition then cameraPosition=desired
    else cameraPosition=cameraPosition+(desired-cameraPosition)*(1-math.exp(-Config.cameraResponse*dt)) end
    SetCamCoord(camera,cameraPosition.x,cameraPosition.y,cameraPosition.z)
    if mode.firstPerson then
        SetCamRot(camera,flightState.look,0.0,flightState.heading,2)
        SetEntityLocallyInvisible(body)
        for _,m in ipairs(motors) do SetEntityLocallyInvisible(m.entity); SetEntityLocallyInvisible(m.blur) end
    else
        local aim=p+forward*2.0
        PointCamAtCoord(camera,aim.x,aim.y,aim.z)
    end
    SetCamFov(camera,mode.fov)
    SetFocusPosAndVel(p.x,p.y,p.z,flightState.vx,flightState.vy,flightState.vz)
end

local function moveAssisted(dt,input)
    local move=Flight.update(flightState,input,dt,Config)
    local p=GetEntityCoords(body)
    local now=GetGameTimer()
    SetEntityRotation(body,flightState.pitch,flightState.roll,flightState.heading,2,true)
    if movementProbe then
        local status,touch=GetShapeTestResult(movementProbe)
        if status==2 then
            if touch==1 or touch==true then corridorStart=nil; corridorEnd=nil
            else corridorStart=probeStart; corridorEnd=probeGoal; corridorTime=now end
            movementProbe=nil
        elseif status==0 or now-probeStarted>200 then
            movementProbe=nil; corridorStart=nil; corridorEnd=nil
        end
    end
    local nextPosition=p+vector3(move.x,move.y,move.z)
    if corridorStart and now-corridorTime<200
        and Flight.insideCorridor(p,corridorStart,corridorEnd,0.08)
        and Flight.insideCorridor(nextPosition,corridorStart,corridorEnd,0.08) then
        SetEntityCoordsNoOffset(body,nextPosition.x,nextPosition.y,nextPosition.z,false,false,false)
        p=nextPosition
    end
    if not movementProbe then
        -- Probe ahead while continuing every frame within previously verified space.
        local velocity=vector3(flightState.vx,flightState.vy,flightState.vz)
        if #velocity>0.005 then
            probeStart=p
            probeGoal=p+velocity*0.12
            RequestCollisionAtCoord(probeGoal.x,probeGoal.y,probeGoal.z)
            movementProbe=StartShapeTestCapsule(p.x,p.y,p.z,probeGoal.x,probeGoal.y,probeGoal.z,0.26,19,body,7)
            probeStarted=now
        end
    end
end
local function createDrone()
    if busy or (body and DoesEntityExist(body)) then return end
    local ped=PlayerPedId()
    if IsPedInAnyVehicle(ped,false) or IsEntityDead(ped) then return end
    busy=true
    local names={'fpv_physics_body','fpv_prop_blur'}
    for _,cfg in ipairs(Config.motors) do names[#names+1]=cfg.model end
    local hashes={}
    for _,name in ipairs(names) do
        hashes[name]=load(name)
        if not hashes[name] then
            for _,h in pairs(hashes) do SetModelAsNoLongerNeeded(h) end
            busy=false; message('Asset ausente ou timeout: '..name); return
        end
    end
    local p=GetOffsetFromEntityInWorldCoords(ped,0.0,1.5,0.1)
    body=CreateObjectNoOffset(hashes.fpv_physics_body,p.x,p.y,p.z,Config.networked,true,false)
    if body==0 then body=nil; busy=false; for _,h in pairs(hashes) do SetModelAsNoLongerNeeded(h) end; return end
    SetEntityHeading(body,GetEntityHeading(ped)); SetEntityDynamic(body,true)
    SetEntityCollision(body,true,true); SetEntityHasGravity(body,true)
    SetEntityLoadCollisionFlag(body,true); SetEntityRecordsCollisions(body,true)
    SetObjectPhysicsParams(body,Config.mass,1.0,0.0,Config.linearDamping,0.0,0.0,Config.angularDamping,0.0,0.001,20.0,1.0)
    -- SET_CGOFFSET throws a native exception for this drawable object on b3258.
    -- Keep the collision asset's physical center instead of overriding it at runtime.
    ActivatePhysics(body)
    for _,cfg in ipairs(Config.motors) do
        local rotor=CreateObjectNoOffset(hashes[cfg.model],p.x,p.y,p.z,false,false,false)
        local blur=CreateObjectNoOffset(hashes.fpv_prop_blur,p.x,p.y,p.z,false,false,false)
        if rotor==0 or blur==0 then
            if rotor~=0 then DeleteEntity(rotor) end; if blur~=0 then DeleteEntity(blur) end
            remove(); busy=false; for _,h in pairs(hashes) do SetModelAsNoLongerNeeded(h) end; message('Falha ao criar rotor.'); return
        end
        SetEntityCollision(rotor,false,false); SetEntityCollision(blur,false,false)
        SetEntityHasGravity(rotor,false); SetEntityHasGravity(blur,false)
        attach(rotor,cfg,0); attach(blur,cfg,0); SetEntityVisible(blur,false,false)
        motors[#motors+1]={cfg=cfg,entity=rotor,blur=blur,current=0,target=0,angle=0}
    end
    for _,h in pairs(hashes) do SetModelAsNoLongerNeeded(h) end
    origin=GetEntityCoords(ped); busy=false
    message('Drone criado. F8: dronevoar | dronedesligar | droneremover')
end
RegisterCommand('drone', function()
    local ok, err = xpcall(createDrone, debug.traceback)
    if not ok then
        remove()
        print('[Drone] Falha na criacao: '..tostring(err))
        message('Falha ao criar drone. Controle liberado; veja o erro no F8 e tente drone novamente.')
    end
end, false)
RegisterCommand('dronevoar',function()
    if flying then shutdown(); return end
    if busy or not origin or #motors ~= #Config.motors or not body or not DoesEntityExist(body) then
        message('Drone ainda nao esta pronto. Use droneremover e depois drone no F8.'); return
    end
    local ped=PlayerPedId()
    if IsEntityDead(ped) or IsPedInAnyVehicle(ped,false) then return end
    TriggerEvent('cidade:preparePilot')
    origin=GetEntityCoords(ped)
    pilot=ped; FreezeEntityPosition(pilot,true); flying=true; armed=true
    FreezeEntityPosition(body,true); SetEntityHasGravity(body,false)
    SetEntityVelocity(body,0.0,0.0,0.0)
    flightState=Flight.new(GetEntityHeading(body))
    camera=CreateCam('DEFAULT_SCRIPTED_CAMERA',true)
    if not camera or camera == 0 then shutdown(); message('Nao foi possivel criar a camera.'); return end
    updateCamera(0,true)
    RenderScriptCams(true,false,0,true,true)
    message('Mouse aponta | WASD move | Shift turbo | V camera | Espaco/Ctrl sobe/desce | Q/E gira')
end,false)
RegisterCommand('dronedesligar',shutdown,false)
RegisterCommand('droneremover',remove,false)
RegisterCommand('dronesom',function(_,args)
    local level=tonumber(args[1])
    if not level or level~=level or level<0 or level>100 then message('Use dronesom 0 a 100. Padrao: 80.'); return end
    soundLevel=level/100
    message('Volume do drone: '..math.floor(level)..'%')
end,false)
RegisterCommand('testarsomdrone',function()
    soundTestUntil=GetGameTimer()+4000
    message('Teste de audio por 4 segundos. Use dronesom 100 para aumentar.')
end,false)
RegisterCommand('dronestatus',function()
    message(('Pilotando: %s | frente %.0f lateral %.0f vertical %.0f giro %.0f'):format(tostring(flying),inputState.forward,inputState.side,inputState.up,inputState.yaw))
end,false)
RegisterCommand('dronerpm',function(_,args)
    if not body then return end
    local id=(args[1] or ''):upper(); local rpm=tonumber(args[2])
    if not rpm or rpm~=rpm or rpm==math.huge or rpm==-math.huge then message('/dronerpm FL 3000 (ou FR/RL/RR)'); return end
    releasePilot(); armed=true
    for _,m in ipairs(motors) do if m.cfg.id==id then m.target=clamp(rpm,0,Config.rpm.max); return end end
    message('Motor inválido: FL, FR, RL ou RR.')
end,false)
RegisterCommand('droneimpacto',function()
    if not body then return end
    shutdown()
    -- Small impulse at one motor: no direct position/rotation assignment.
    ApplyForceToEntity(body,1,0.0,Config.mass*1.5,Config.mass*.4,-.105,.092,0.0,0,true,true,false,false,true)
end,false)
CreateThread(function()
    while true do
        if not body or busy then Wait(100) else
            Wait(0)
            local ok, err = xpcall(function()
            if not DoesEntityExist(body) then remove() else
                local dt=GetFrameTime(); local p=GetEntityCoords(body); local vel=GetEntityVelocity(body)
                if flying then
                    if not pilot or PlayerPedId()~=pilot or IsEntityDead(pilot) then shutdown()
                    else
                        DisableAllControlActions(0); EnableControlAction(0,200,true)
                        local function key(k) return IsDisabledControlPressed(0,k) and 1.0 or 0.0 end
                        if IsDisabledControlJustPressed(0,177) then shutdown() else
                            local focused=IsNuiFocused() or IsPauseMenuActive()
                            local input={forward=0,side=0,up=0,yaw=0,mouseX=0,mouseY=0,boost=false}
                            if not focused then
                                input.forward=key(32)-key(33)
                                input.side=key(35)-key(34)
                                input.up=key(22)-key(36)
                                input.yaw=key(44)-key(38)
                                input.boost=key(21)>0
                                local lookScale=IsUsingKeyboard(0) and 1.0 or dt*12.0
                                input.mouseX=GetDisabledControlNormal(0,1)*lookScale
                                input.mouseY=GetDisabledControlNormal(0,2)*lookScale
                                if IsDisabledControlJustPressed(0,0) then
                                    cameraMode=cameraMode % #Config.cameras+1
                                    StopCamPointing(camera)
                                    message('Camera: '..Config.cameras[cameraMode].name)
                                end
                            end
                            inputState=input
                            moveAssisted(dt,input)
                            for _,m in ipairs(motors) do m.target=Config.rpm.cruise end
                            updateCamera(dt,false)
                        end
                    end
                end
                for _,m in ipairs(motors) do
                    m.current,m.angle=Motor.step(m.current,m.target,m.angle,dt,Config.response,m.cfg.sign)
                    attach(m.entity,m.cfg,m.angle)
                    local blend=clamp((m.current-Config.blurStart)/(Config.blurFull-Config.blurStart),0,1)
                    SetEntityAlpha(m.entity,math.floor(255*(1-blend)),false)
                    SetEntityVisible(m.blur,blend>0,false); SetEntityAlpha(m.blur,math.floor(255*blend),false)
                    -- Four local-Z forces at motor positions naturally create torque when RPM differs.
                    local thrust=Config.mass*Config.gravity/4*(m.current/Config.rpm.cruise)^2
                    if not flying and thrust>.0001 then ApplyForceToEntity(body,0,0.0,0.0,thrust,m.cfg.x,m.cfg.y,m.cfg.z-Config.com[3],0,true,true,false,false,true) end
                    local reaction=-m.cfg.sign*.0015*(m.current/Config.rpm.cruise)^2
                    if not flying and math.abs(reaction)>.000001 then ApplyForceToEntity(body,4,0.0,0.0,reaction,0.0,0.0,0.0,0,true,true,false,false,true) end
                end
                local hit=HasEntityCollidedWithAnything(body)
                if hit and not collisionLast and GetGameTimer()-impactTime>200 then
                    local speed=lastVelocity and #lastVelocity or #vel; impactTime=GetGameTimer()
                    TriggerEvent('fpv_drone:impact',{entity=body,impactSpeed=speed,damageBand=Motor.damageBand(speed)})
                end
                collisionLast=hit; lastVelocity=vel
                -- Swept probes provide an early-contact event; no fabricated native CCD toggle.
                -- Engine contact solving remains responsible for collision response.
                if not flying then
                for i,m in ipairs(motors) do
                    if casts[i] then
                        local status,touch,point,normal,entity=GetShapeTestResult(casts[i])
                        if status~=1 then
                            if status==2 and (touch==1 or touch==true) then
                                TriggerEvent('fpv_drone:predictedContact',{motor=m.cfg.id,point=point,normal=normal,entity=entity})
                                local approach=vel.x*normal.x+vel.y*normal.y+vel.z*normal.z
                                if not flying and Config.sweepGuard and approach < -4.0 then
                                    -- Conservative anticipatory impulse at the threatened motor.
                                    -- This supplements RAGE contact solving; it is not native continuous CCD.
                                    local impulse=-approach*Config.mass*.75
                                    ApplyForceToEntity(body,1,normal.x*impulse,normal.y*impulse,normal.z*impulse,m.cfg.x,m.cfg.y,m.cfg.z,0,false,true,false,false,true)
                                end
                            end
                            casts[i]=nil
                        end
                    else
                        local start=GetOffsetFromEntityInWorldCoords(body,m.cfg.x,m.cfg.y,.025)
                        local span=math.max(dt,1/60)*2; local finish=start+vel*span
                        casts[i]=StartShapeTestCapsule(start.x,start.y,start.z,finish.x,finish.y,finish.z,.016,1,body,7)
                    end
                end
                end
            end
            end, debug.traceback)
            if not ok then
                remove()
                print('[Drone] Falha na simulacao: '..tostring(err))
                message('Pilotagem interrompida por erro. Personagem liberado; veja o F8.')
            end
        end
    end
end)
AddEventHandler('onResourceStop',function(name) if name==GetCurrentResourceName() then remove() end end)

exports('isPiloting', function() return flying end)
exports('isFirstPerson', function() return flying and Config.cameras[cameraMode].firstPerson == true end)
exports('setFirstPerson', function()
    if not flying or not camera then return false end
    for index,mode in ipairs(Config.cameras) do
        if mode.firstPerson then
            cameraMode=index; StopCamPointing(camera); updateCamera(0,true)
            return true
        end
    end
    return false
end)

-- O mesmo WAV fica baixo em hover e aumenta suavemente com deslocamento real.
CreateThread(function()
    local previousPosition, previousTime
    local smoothVolume=0.0
    while true do
        Wait(100)
        local volume = 0.0
        if body and DoesEntityExist(body) and armed and not IsPauseMenuActive() then
            local now=GetGameTimer()
            local position=GetEntityCoords(body)
            local speed=previousPosition and now>previousTime and #(position-previousPosition)/((now-previousTime)/1000.0) or 0.0
            previousPosition,previousTime=position,now
            -- Frozen scripted objects can report an unreliable ground height.
            -- During active piloting the motors must remain audible even in hover.
            if flying or GetEntityHeightAboveGround(body) > 0.22 then
                local rpm = 0.0
                for _, motor in ipairs(motors) do rpm = math.max(rpm, motor.current) end
                if rpm > 300 then
                    local distance = flying and 0.0 or #(GetFinalRenderedCamCoord() - GetEntityCoords(body))
                    volume = Flight.audioVolume(speed,distance)
                end
            end
        else previousPosition=nil; previousTime=nil end
        if GetGameTimer()<soundTestUntil then volume=0.6 end
        volume=volume*soundLevel
        smoothVolume=volume>0 and Flight.smooth(smoothVolume,volume,8.0,0.1) or 0.0
        SendNUIMessage({type='droneAudio', volume=smoothVolume})
    end
end)
