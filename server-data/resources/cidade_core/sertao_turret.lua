-- Operator station for this city's single-player sandbox (sv_maxclients 1).
-- The gun is a streamed drawable; its pivot and contacts match the Blender file.
CidadeTurret = { active = false }
local MODEL, GUN = joaat('sertao'), joaat('sertao_torre')
local WEAPON, DICT = joaat('WEAPON_COMBATMG'), 'cidade_sertao_torre'
local guns, station, pending = {}, nil, false
local function clamp(v,a,b) return math.max(a,math.min(b,v)) end
local function help(text)
    BeginTextCommandDisplayHelp('STRING'); AddTextComponentSubstringPlayerName(text)
    EndTextCommandDisplayHelp(0,false,false,-1)
end
local function attachGun(gun,vehicle,yaw,pitch)
    AttachEntityToEntity(gun,vehicle,0,0.0,-1.15,1.61,pitch,0.0,yaw,false,false,false,false,2,true)
end
local function cleanup()
    pending=false
    local s=station;station=nil;CidadeTurret.active=false
    if not s then return end
    if s.cam then RenderScriptCams(false,true,250,true,true);DestroyCam(s.cam,false) end
    if DoesEntityExist(s.ped) then
        DetachEntity(s.ped,true,true)
        SetEntityCollision(s.ped,true,true);SetPedCanRagdoll(s.ped,true)
        SetPedCanArmIk(s.ped,true);SetPedCurrentWeaponVisible(s.ped,true,false,true,true)
        ClearPedTasks(s.ped)
        if DoesEntityExist(s.vehicle) and not IsEntityDead(s.ped) then
            local p=GetOffsetFromEntityInWorldCoords(s.vehicle,0.0,-3.1,0.0)
            local found,z=GetGroundZFor_3dCoord(p.x,p.y,p.z+3.0,false)
            SetEntityCoordsNoOffset(s.ped,p.x,p.y,found and z+1.0 or p.z,false,false,false)
        end
        if s.weapon then SetCurrentPedWeapon(s.ped,s.weapon,true) end
    end
    if DoesEntityExist(s.gun) and DoesEntityExist(s.vehicle) then attachGun(s.gun,s.vehicle,0.0,0.0) end
end
local function mount(vehicle)
    if pending or station then return end
    pending=true
    local p=PlayerPedId()
    RequestAnimDict(DICT);RequestWeaponAsset(WEAPON,31,0);RequestNamedPtfxAsset('core')
    local untilTime=GetGameTimer()+5000
    while pending and GetGameTimer()<untilTime and (not HasAnimDictLoaded(DICT) or not HasWeaponAssetLoaded(WEAPON)) do Wait(0) end
    if not pending then return end
    pending=false
    if not HasAnimDictLoaded(DICT) or not HasWeaponAssetLoaded(WEAPON) or not DoesEntityExist(vehicle)
        or IsEntityDead(p) or IsPedInAnyVehicle(p,false) or not guns[vehicle] or GetEntitySpeed(vehicle)>1.5 then return end
    TriggerEvent('cidade:preparePilot')
    local pos=GetEntityCoords(p)
    local start=GetOffsetFromEntityGivenWorldCoords(vehicle,pos.x,pos.y,pos.z)
    station={vehicle=vehicle,ped=p,gun=guns[vehicle],yaw=0.0,pitch=0.0,weapon=GetSelectedPedWeapon(p),
        start=start,entered=GetGameTimer(),nextShot=0,shots=0,clip=80,reload=0,animCheck=0}
    CidadeTurret.active=true
    SetCurrentPedWeapon(p,joaat('WEAPON_UNARMED'),true)
    SetPedCanRagdoll(p,false);SetEntityCollision(p,false,false);SetPedCanArmIk(p,true)
    TaskPlayAnim(p,DICT,'operador',4.0,-4.0,-1,1,0.0,false,false,false)
    station.cam=CreateCam('DEFAULT_SCRIPTED_CAMERA',true)
    SetCamNearClip(station.cam,.08);SetCamFov(station.cam,65.0)
    RenderScriptCams(true,true,450,true,true)
end
local function fire(s)
    local now=GetGameTimer()
    if now<s.nextShot or s.reload>0 then return end
    if s.clip<=0 then s.reload=now+2600;return end
    local origin=GetOffsetFromEntityInWorldCoords(s.gun,0.0,2.15,.07)
    local direction=GetEntityForwardVector(s.gun)
    local target=origin+direction*800.0
    -- The local shot owns damage; effects do not spawn extra projectiles.
    ShootSingleBulletBetweenCoordsIgnoreEntity(origin.x,origin.y,origin.z,target.x,target.y,target.z,
        45,true,WEAPON,s.ped,true,false,950.0,s.vehicle,false)
    if HasNamedPtfxAssetLoaded('core') then
        UseParticleFxAssetNextCall('core')
        StartParticleFxNonLoopedOnEntity('muz_assault_rifle',s.gun,0.0,2.15,.07,0.0,0.0,0.0,1.4,false,false,false)
    end
    s.flash=now+55;s.nextShot=now+110;s.clip=s.clip-1;s.shots=s.shots+1
    ShakeCam(s.cam,'SMALL_EXPLOSION_SHAKE',.045)
end
local function update()
    local s=station;local p=s.ped;local now=GetGameTimer()
    if p~=PlayerPedId() or not DoesEntityExist(s.vehicle) or not DoesEntityExist(s.gun)
        or IsEntityDead(p) or IsEntityDead(s.vehicle) or IsEntityInWater(s.vehicle) then cleanup();return end
    for _,control in ipairs({1,2,21,22,23,24,25,30,31,36,37,44,45,75,140,141,142,257,263,264}) do DisableControlAction(0,control,true) end
    DisablePlayerFiring(PlayerId(),true)
    if IsDisabledControlJustPressed(0,23) and now-s.entered>950 then cleanup();return end
    local entering=clamp((now-s.entered)/850,0,1)
    local blocked=IsPauseMenuActive() or IsNuiFocused() or entering<1
    if not blocked then
        local speed=IsUsingKeyboard(0) and 8.0 or 95.0*math.min(GetFrameTime(),.05)
        s.yaw=clamp(s.yaw-GetDisabledControlNormal(0,1)*speed,-60,60)
        s.pitch=clamp(s.pitch-GetDisabledControlNormal(0,2)*speed,-12,35)
    end
    attachGun(s.gun,s.vehicle,s.yaw,s.pitch)
    local a=math.rad(s.yaw)
    local x,y,z=math.sin(a)*.90,-1.15-math.cos(a)*.90,1.34
    if entering<1 then
        local t=entering*entering*(3-2*entering)
        x=s.start.x+(x-s.start.x)*t;y=s.start.y+(y-s.start.y)*t;z=s.start.z+(z-s.start.z)*t
    end
    AttachEntityToEntity(p,s.vehicle,0,x,y,z,0.0,0.0,s.yaw,false,false,false,true,2,true)
    if now>=s.animCheck then
        if not IsEntityPlayingAnim(p,DICT,'operador',3) then TaskPlayAnim(p,DICT,'operador',4.0,-4.0,-1,1,0.0,false,false,false) end
        s.animCheck=now+500
    end
    -- IK is refreshed every frame so both hands follow elevation as well as yaw.
    SetIkTarget(p,3,s.gun,-1,-.17,-.52,.05,1,100,100)
    SetIkTarget(p,4,s.gun,-1,.17,-.52,.05,1,100,100)
    local aiming=not blocked and IsDisabledControlPressed(0,25)
    local cam=GetOffsetFromEntityInWorldCoords(s.gun,aiming and .06 or .40,aiming and -.64 or -2.35,aiming and .27 or .85)
    local muzzle=GetOffsetFromEntityInWorldCoords(s.gun,0.0,2.15,.07)
    local target=muzzle+GetEntityForwardVector(s.gun)*800.0
    SetCamCoord(s.cam,cam.x,cam.y,cam.z);PointCamAtCoord(s.cam,target.x,target.y,target.z)
    local fov=GetCamFov(s.cam);SetCamFov(s.cam,fov+((aiming and 38.0 or 65.0)-fov)*math.min(GetFrameTime()*12,1))
    if s.reload>0 and now>=s.reload then s.clip=80;s.reload=0 end
    if not blocked then
        if IsDisabledControlJustPressed(0,45) and s.clip<80 and s.reload==0 then s.reload=now+2600 end
        if IsDisabledControlPressed(0,24) then fire(s) end
        DrawRect(.5,.5,.002,.014,255,255,255,210);DrawRect(.5,.5,.009,.002,255,255,255,210)
        help(('Torre: mouse direciona | direito mira | esquerdo dispara | R recarrega | F sai~n~%s'):format(s.reload>0 and 'Recarregando...' or ('Fita: '..s.clip..'/80')))
    end
    if s.flash and now<s.flash then DrawLightWithRange(muzzle.x,muzzle.y,muzzle.z,255,170,65,5.0,4.0) end
end
-- Stream one local visual per truck. The sandbox has one player; no duplicate network props.
CreateThread(function()
    RequestModel(GUN)
    while true do
        Wait(500)
        local p=GetEntityCoords(PlayerPedId());local seen={}
        for _,v in ipairs(GetGamePool('CVehicle')) do
            if GetEntityModel(v)==MODEL and #(GetEntityCoords(v)-p)<160.0 then
                seen[v]=true
                if not guns[v] or not DoesEntityExist(guns[v]) then
                    RequestModel(GUN)
                    if HasModelLoaded(GUN) then
                        local c=GetEntityCoords(v);local g=CreateObjectNoOffset(GUN,c.x,c.y,c.z,false,false,false)
                        if g~=0 then SetEntityCollision(g,false,false);SetEntityAsMissionEntity(g,true,true);guns[v]=g;attachGun(g,v,0.0,0.0) end
                    end
                end
            end
        end
        for v,g in pairs(guns) do
            if not seen[v] or not DoesEntityExist(v) or GetEntityModel(v)~=MODEL then
                if station and station.vehicle==v then cleanup() end
                if DoesEntityExist(g) then DeleteEntity(g) end;guns[v]=nil
            end
        end
    end
end)
CreateThread(function()
    while true do
        Wait(0)
        if station then
            local ok,err=pcall(update)
            if not ok then cleanup();print('[Sertao] '..tostring(err)) end
        elseif not pending and not IsPedInAnyVehicle(PlayerPedId(),false) and not IsEntityDead(PlayerPedId()) and not IsPauseMenuActive() and not IsNuiFocused() then
            local p=GetEntityCoords(PlayerPedId())
            for v in pairs(guns) do
                if DoesEntityExist(v) and GetEntitySpeed(v)<1.5 then
                    local at=GetOffsetFromEntityInWorldCoords(v,0.0,-2.65,.3)
                    if #(p-at)<1.9 then
                        DisableControlAction(0,23,true);help('Pressione ~INPUT_ENTER~ para subir e operar a torre.')
                        if IsDisabledControlJustPressed(0,23) then CreateThread(function() mount(v) end) end
                        break
                    end
                end
            end
        end
    end
end)
RegisterCommand('sertaoinfo',function()
    print('[Sertao] modelo='..tostring(IsModelInCdimage(GUN))..' carregado='..tostring(HasModelLoaded(GUN))..' operador='..tostring(station~=nil))
    if station then print(('[Sertao] yaw=%.2f pitch=%.2f disparos=%d fita=%d'):format(station.yaw,station.pitch,station.shots,station.clip)) end
end,false)
-- Local development inspection: uses the same station and firing implementation.
RegisterCommand('sertaoteste',function(_,args)
    CreateThread(function()
        local mode=args[1] or 'ver'
        if mode=='sair' then cleanup();return end
        if mode=='tiro' and station then
            for _=1,3 do fire(station);Wait(150) end
            print('[Sertao QA] shots='..station.shots);return
        end
        if mode=='giro' and station then station.yaw=35;station.pitch=15;return end
        if mode=='posto' then
            local p=PlayerPedId();local v=GetVehiclePedIsIn(p,false)
            if v==0 then v=GetVehiclePedIsIn(p,true) end
            if v~=0 and GetEntityModel(v)==MODEL then
                ClearPedTasksImmediately(p)
                local at=GetOffsetFromEntityInWorldCoords(v,0,-3.0,.45)
                SetEntityCoordsNoOffset(p,at.x,at.y,at.z,false,false,false)
                Wait(500);mount(v)
            end
            return
        end
        SetFollowVehicleCamViewMode(1);SetFollowPedCamViewMode(1)
        SetGameplayCamRelativeHeading(135.0)
    end)
end,false)
AddEventHandler('cidade:preparePilot',cleanup)
AddEventHandler('onResourceStop',function(name)
    if name~=GetCurrentResourceName() then return end
    cleanup();for _,g in pairs(guns) do if DoesEntityExist(g) then DeleteEntity(g) end end
end)
