-- Comandos de desenvolvimento para os convidados autorizados por cidade_acesso.
-- O modelo inicial abaixo e igual para todos os jogadores desta base.
local flying = false
local flightPed = nil
local ready = false
local spawningIsland = false
local spawn = { x = 195.17, y = -933.77, z = 30.69, heading = 144.0, model = 'a_m_y_business_01' }

local function holdingLoadingScreen()
    return GetResourceState('cidade_loading') == 'started' and exports.cidade_loading:isHolding()
end

local function loadingState(action)
    if GetResourceState('cidade_loading') == 'started' then exports.cidade_loading[action]() end
end

local function message(text)
    print('[Minha Cidade] ' .. text)
    BeginTextCommandThefeedPost('STRING')
    AddTextComponentSubstringPlayerName(text)
    EndTextCommandThefeedPostTicker(false, false)
end

local function stopFlying()
    flying = false
    if flightPed and DoesEntityExist(flightPed) then
        FreezeEntityPosition(flightPed, false)
        SetEntityCollision(flightPed, true, true)
        SetEntityHasGravity(flightPed, true)
        SetEntityInvincible(flightPed, false)
        SetPedCanRagdoll(flightPed, true)
        SetEntityVelocity(flightPed, 0.0, 0.0, 0.0)
    end
    flightPed = nil
end

local function revive()
    if not ready then return end
    TriggerEvent('cidade:stopProne')
    if GetResourceState('fpv_drone_runtime') == 'started' then ExecuteCommand('dronedesligar') end
    stopFlying()
    local ped = PlayerPedId()
    local position = GetEntityCoords(ped)
    local heading = GetEntityHeading(ped)
    if IsEntityDead(ped) then
        NetworkResurrectLocalPlayer(position.x, position.y, position.z, heading, 0, false)
    end
    ped = PlayerPedId()
    ClearPedTasksImmediately(ped)
    SetEntityMaxHealth(ped, 200)
    SetEntityHealth(ped, 200)
    ClearPedBloodDamage(ped)
    ResetPedVisibleDamage(ped)
    SetEntityInvincible(ped, false)
    SetPlayerInvincible(PlayerId(), false)
    SetPlayerControl(PlayerId(), true, 0)
    ClearPlayerWantedLevel(PlayerId())
    if IsScreenFadedOut() then DoScreenFadeIn(300) end
    message('Voce foi revivido e sua vida foi recuperada.')
end

local function toggleFlight()
    if not ready then return end
    TriggerEvent('cidade:stopProne')
    if GetResourceState('fpv_drone_runtime') == 'started' and exports.fpv_drone_runtime:isPiloting() then
        message('Use dronedesligar antes de voar com o personagem.')
        return
    end
    if flying then
        stopFlying()
        message('Voo desativado. A gravidade voltou; desligue perto do chao.')
        return
    end
    local ped = PlayerPedId()
    if IsPedInAnyVehicle(ped, false) then
        message('Saia do veiculo antes de ativar o voo.')
        return
    end
    if IsEntityDead(ped) then
        message('Digite reviver no F8 antes de voar.')
        return
    end
    ClearPedTasksImmediately(ped)
    flightPed = ped
    flying = true
    SetEntityInvincible(ped, true)
    SetEntityCollision(ped, false, false)
    FreezeEntityPosition(ped, true)
    SetPedCanRagdoll(ped, false)
    message('Voo ativado: WASD, E sobe, Q desce, Shift acelera, Ctrl desacelera. Velocidade dobrada.')
end

RegisterCommand('reviver', revive, false)
RegisterCommand('voar', toggleFlight, false)
RegisterCommand('noclip', toggleFlight, false)
AddEventHandler('cidade:preparePilot', stopFlying)
RegisterCommand('ajuda', function()
    message('F8: reviver | voar | veiculo adder | dv | drone | dronevoar | droneremover')
    print('[Minha Cidade] prone | deitar | levantar | arma pistola 120 | arma lanterna 0 | desarmar | nightvision | dia | tarde | noite | noiteescura | hora 18 30 | tempolivre | clima chuva | dronesom 80 | testarsomdrone | recuperartela')
    print('[Combate] C alterna agachado/em pe, com ou sem arma; WASD anda, Shift acelera agachado. Z deita; W/S rasteja, A/D vira; outro Z levanta em 1,5 s. Pode sacar/guardar carabina/fuzil e recarregar sem levantar. Alt + mouse olha ao redor. Cobertura com Q removida.')
    print('[Veiculos] sertao ou veiculo sertao: picape com torre visual; dv remove.')
    print('[ADM] encontrar ID: ir ate o jogador | chamar ID: trazer o jogador. Use o ID permanente do painel.')
end, false)

local function restoreIslandView()
    -- Finish both loading layers and return rendering to the gameplay camera.
    ShutdownLoadingScreen()
    if not holdingLoadingScreen() then ShutdownLoadingScreenNui() end
    if IsPlayerSwitchInProgress() then StopPlayerSwitch() end
    RenderScriptCams(false, false, 0, true, false)
    ClearFocus()
    SetGameplayCamRelativeHeading(0.0)
    SetGameplayCamRelativePitch(0.0, 1.0)
    SetEntityVisible(PlayerPedId(), true, false)
    SetPlayerControl(PlayerId(), not holdingLoadingScreen(), 0)
    DoScreenFadeIn(300)
end

local function reportIslandView(stage, grounded)
    local ped=PlayerPedId()
    local p=GetEntityCoords(ped)
    local cam=GetGameplayCamCoord()
    local found,z=GetGroundZFor_3dCoord(p.x,p.y,p.z+100.0,false)
    local report={stage=stage,revision='entrada-20261009-2',grounded=grounded,
        position={x=p.x,y=p.y,z=p.z},ground={found=found,z=z},
        camera={x=cam.x,y=cam.y,z=cam.z,gameplay=IsGameplayCamRendering()},
        faded_out=IsScreenFadedOut(),fading_out=IsScreenFadingOut(),
        switching=IsPlayerSwitchInProgress(),collision=HasCollisionLoadedAroundEntity(ped)}
    print('[Entrada Ilha] '..json.encode(report))
    if GetResourceState('porto_esperanca')=='started' then TriggerServerEvent('porto_esperanca:spawnDiagnostic',report) end
end

local function spawnIsland()
    if spawningIsland then return end
    if IsPedInAnyVehicle(PlayerPedId(),false) then message('Saia do veiculo antes de recuperar a entrada.');return end
    spawningIsland=true
    loadingState('markWaiting')
    TriggerEvent('cidade:stopProne')
    if GetResourceState('fpv_drone_runtime')=='started' then ExecuteCommand('dronedesligar') end
    stopFlying()
    local grounded=false
    local ped=PlayerPedId()
    local function protect()
        ped=PlayerPedId()
        FreezeEntityPosition(ped,true)
        SetEntityHasGravity(ped,false)
        SetEntityInvincible(ped,true)
        SetEntityVelocity(ped,0.0,0.0,0.0)
    end
    protect()
    local ok,err=xpcall(function()
        reportIslandView('antes',false)
        local deadline=GetGameTimer()+15000
        while GetResourceState('teste_ilha')~='started' and GetGameTimer()<deadline do Wait(100) end
        if GetResourceState('teste_ilha')~='started' then error('recurso da ilha indisponivel') end
        spawn=exports.teste_ilha:getSpawn()
        -- Protection precedes preparation, which yields while loading the map/water.
        exports.teste_ilha:prepareSpawn()
        if not ready then
            local model=GetHashKey(spawn.model)
            RequestModel(model)
            deadline=GetGameTimer()+10000
            while not HasModelLoaded(model) and GetGameTimer()<deadline do Wait(50) end
            if not HasModelLoaded(model) then SetModelAsNoLongerNeeded(model);error('modelo inicial indisponivel') end
            SetPlayerModel(PlayerId(),model)
            SetModelAsNoLongerNeeded(model)
            protect()
            SetPedDefaultComponentVariation(ped)
        end
        RequestIpl('ti_pista_map')
        SetEntityCoordsNoOffset(ped,spawn.x,spawn.y,spawn.z,false,false,false)
        NetworkResurrectLocalPlayer(spawn.x,spawn.y,spawn.z,spawn.heading,true,true,false)
        protect()
        SetEntityCollision(ped,true,true)
        ClearPedTasksImmediately(ped)
        SetEntityHeading(ped,spawn.heading)
        SetFocusPosAndVel(spawn.x,spawn.y,spawn.z,0.0,0.0,0.0)
        NewLoadSceneStartSphere(spawn.x,spawn.y,spawn.z,220.0,0)
        -- A general collision flag can be true while the authored floor is absent.
        deadline=GetGameTimer()+20000
        repeat
            RequestCollisionAtCoord(spawn.x,spawn.y,spawn.z)
            Wait(50)
            local found,z=GetGroundZFor_3dCoord(spawn.x,spawn.y,spawn.z+100.0,false)
            if found and math.abs(z-(spawn.z-1.15))<0.5 and HasCollisionLoadedAroundEntity(ped) then
                SetEntityCoordsNoOffset(ped,spawn.x,spawn.y,z+1.15,false,false,false)
                grounded=true
                break
            end
        until GetGameTimer()>=deadline
        SetEntityMaxHealth(ped,200)
        SetEntityHealth(ped,200)
        SetMaxWantedLevel(0)
        ClearPlayerWantedLevel(PlayerId())
        ready=true
    end,debug.traceback)
    NewLoadSceneStop()
    if grounded then
        SetEntityVelocity(ped,0.0,0.0,0.0)
        if not holdingLoadingScreen() then
            SetEntityHasGravity(ped,true)
            SetEntityInvincible(ped,false)
            SetPlayerInvincible(PlayerId(),false)
            FreezeEntityPosition(ped,false)
        end
        TriggerEvent('playerSpawned',spawn)
    end
    -- Errors/timeouts also restore the picture, but keep the ped protected.
    restoreIslandView()
    if not ok then print('[Entrada Ilha] '..tostring(err)) end
    message(grounded and 'Entrada recuperada. F8: porto | ilha | voar | admin.' or 'Solo ainda nao confirmado. Personagem protegido; F8: recuperartela para tentar novamente.')
    Wait(1500)
    if IsScreenFadedOut() or IsScreenFadingOut() or IsPlayerSwitchInProgress() or not IsGameplayCamRendering() then restoreIslandView();Wait(500) end
    reportIslandView('depois',grounded)
    spawningIsland=false
    loadingState(grounded and ok and 'markReady' or 'markFailed')
end

RegisterCommand('recuperartela',function()
    if GetConvar('cidade_modo','cidade')=='ilha' then CreateThread(spawnIsland) end
end,false)

local function spawnCity()
    exports.spawnmanager:spawnPlayer(spawn, function()
        ready = true
        SetEntityMaxHealth(PlayerPedId(), 200)
        SetEntityHealth(PlayerPedId(), 200)
        SetMaxWantedLevel(0)
        if holdingLoadingScreen() then
            loadingState('markReady')
        else
            ShutdownLoadingScreenNui()
        end
        message('Bem-vindo! Abra F8 e digite ajuda para ver os comandos.')
    end)
end

exports('retryLoadingSpawn', function()
    if not holdingLoadingScreen() then return end
    loadingState('markWaiting')
    if GetConvar('cidade_modo','cidade')=='ilha' then
        CreateThread(spawnIsland)
    else
        spawnCity()
    end
end)

CreateThread(function()
    loadingState('beginLoading')
    while not NetworkIsSessionStarted() do Wait(100) end
    exports.spawnmanager:setAutoSpawn(false)
    local islandMode=GetConvar('cidade_modo','cidade')=='ilha'
    if islandMode then
        ExecuteCommand('recuperartela')
        return
    end
    spawnCity()
end)

CreateThread(function()
    while true do
        if not flying then
            Wait(200)
        else
            Wait(0)
            local ped = PlayerPedId()
            if ped ~= flightPed or IsEntityDead(ped) then
                stopFlying()
            else
                for _, control in ipairs({ 21, 22, 24, 25, 30, 31, 32, 33, 34, 35, 36, 38, 44, 75 }) do
                    DisableControlAction(0, control, true)
                end
                DisablePlayerFiring(PlayerId(), true)
                -- Nao movimentar o personagem ao digitar comandos ou abrir menus.
                if not IsPauseMenuActive() and not IsNuiFocused() then
                    local rotation = GetGameplayCamRot(2)
                    local yaw, pitch = math.rad(rotation.z), math.rad(rotation.x)
                    local forward = vector3(-math.sin(yaw) * math.cos(pitch), math.cos(yaw) * math.cos(pitch), math.sin(pitch))
                    local right = vector3(math.cos(yaw), math.sin(yaw), 0.0)
                    local direction = vector3(0.0, 0.0, 0.0)
                    if IsDisabledControlPressed(0, 32) then direction = direction + forward end
                    if IsDisabledControlPressed(0, 33) then direction = direction - forward end
                    if IsDisabledControlPressed(0, 35) then direction = direction + right end
                    if IsDisabledControlPressed(0, 34) then direction = direction - right end
                    if IsDisabledControlPressed(0, 38) then direction = direction + vector3(0.0, 0.0, 1.0) end
                    if IsDisabledControlPressed(0, 44) then direction = direction - vector3(0.0, 0.0, 1.0) end
                    local speed = 24.0
                    if IsDisabledControlPressed(0, 21) then speed = 100.0 end
                    if IsDisabledControlPressed(0, 36) then speed = 6.0 end
                    if #direction > 0.0 then
                        local position = GetEntityCoords(ped) + (direction / #direction) * speed * math.min(GetFrameTime(), 0.05)
                        RequestCollisionAtCoord(position.x, position.y, position.z)
                        SetEntityCoordsNoOffset(ped, position.x, position.y, position.z, false, false, false)
                    end
                    SetEntityHeading(ped, rotation.z)
                    SetEntityVelocity(ped, 0.0, 0.0, 0.0)
                end
                BeginTextCommandDisplayHelp('STRING')
                AddTextComponentSubstringPlayerName('VOO | WASD: mover | E/Q: subir/descer | SHIFT/CTRL: velocidade | F8: voar')
                EndTextCommandDisplayHelp(0, false, false, -1)
            end
        end
    end
end)

AddEventHandler('onResourceStop', function(resource)
    if resource == GetCurrentResourceName() then stopFlying() end
end)
