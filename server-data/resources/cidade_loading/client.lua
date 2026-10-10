-- Only a successful spawn can enable entry. Progress percentages never do.
local function nativeTrue(value) return value == true or value == 1 end
local holding = nativeTrue(GetIsLoadingScreenActive())
local prepared = false
local entering = false
local failed = false
local detail = 'Carregando o mundo e preparando seu personagem.'
local lastPed = nil
local retryAt = -5000
local uiReady = false
local uiStarting = false
local uiActive = false
local initialNuiClosed = false
local revision = 'entrada-nui-20261009-4'

local function snapshot()
    return { revision = revision, holding = holding, ready = prepared, entering = entering,
        failed = failed, detail = detail }
end

local function diagnostics()
    local data = snapshot()
    local ped = PlayerPedId()
    local p = GetEntityCoords(ped)
    local camera = GetGameplayCamCoord()
    local ground, z = GetGroundZFor_3dCoord(p.x, p.y, p.z + 100.0, false)
    data.ui = { ready = uiReady, starting = uiStarting, active = uiActive,
        initial_closed = initialNuiClosed, focused = nativeTrue(IsNuiFocused()) }
    data.world = { position = { x = p.x, y = p.y, z = p.z },
        ground = { found = nativeTrue(ground), z = z }, collision = nativeTrue(HasCollisionLoadedAroundEntity(ped)),
        camera = { gameplay = nativeTrue(IsGameplayCamRendering()), x = camera.x, y = camera.y, z = camera.z },
        faded_out = nativeTrue(IsScreenFadedOut()), fading_out = nativeTrue(IsScreenFadingOut()),
        switching = nativeTrue(IsPlayerSwitchInProgress()), loading = nativeTrue(GetIsLoadingScreenActive()) }
    return data
end

local function report(stage, browser)
    local data = diagnostics()
    data.stage = stage
    data.time_ms = GetGameTimer()
    if type(browser) == 'table' then data.browser = browser end
    print('[Entrada Cidade] ' .. json.encode(data))
    TriggerServerEvent('cidade_loading:diagnostic', data)
end

local function publish()
    local message = { eventName = 'cidadeLoadingState', state = snapshot() }
    if uiStarting or uiActive then SendNUIMessage(message) end
    if not initialNuiClosed then SendLoadingScreenMessage(json.encode(message)) end
end

local function closeInitialNui()
    if initialNuiClosed then return end
    ShutdownLoadingScreenNui()
    initialNuiClosed = true
end

local function activateInteractive(audio, progress)
    if not holding or entering or not uiReady or uiStarting or uiActive then return end
    uiStarting = true
    -- The hidden regular frame has already loaded its playlist. It acknowledges
    -- visibility before we remove the old frame and give it native input focus.
    SendNUIMessage({ eventName = 'cidadeLoadingActivate', state = snapshot(),
        audio = type(audio) == 'table' and audio or {}, progress = tonumber(progress) or 0 })
    report('interface_ativacao_enviada')
end

local function protect()
    local ped = PlayerPedId()
    if not nativeTrue(DoesEntityExist(ped)) then return end
    lastPed = ped
    FreezeEntityPosition(ped, true)
    SetEntityHasGravity(ped, false)
    SetEntityInvincible(ped, true)
    SetPlayerInvincible(PlayerId(), true)
    SetPlayerControl(PlayerId(), false, 0)
end

local function release()
    local ped = PlayerPedId()
    if lastPed and lastPed ~= ped and nativeTrue(DoesEntityExist(lastPed)) then
        FreezeEntityPosition(lastPed, false)
        SetEntityHasGravity(lastPed, true)
        SetEntityInvincible(lastPed, false)
    end
    if nativeTrue(DoesEntityExist(ped)) then
        FreezeEntityPosition(ped, false)
        SetEntityHasGravity(ped, true)
        SetEntityInvincible(ped, false)
        SetEntityVelocity(ped, 0.0, 0.0, 0.0)
    end
    SetPlayerInvincible(PlayerId(), false)
    SetPlayerControl(PlayerId(), true, 0)
    SetNuiFocus(false, false)
    SetNuiFocusKeepInput(false)
    lastPed = nil
end

exports('isHolding', function() return holding end)
exports('beginLoading', function()
    -- A resource restart after entry has no loading HTML to display.
    if not holding and not nativeTrue(GetIsLoadingScreenActive()) then return false end
    holding = true
    prepared = false
    failed = false
    entering = false
    detail = 'Carregando o mundo e preparando seu personagem.'
    protect()
    publish()
    report('preparacao_iniciada')
    return true
end)
exports('markWaiting', function()
    if not holding or entering then return end
    prepared = false
    failed = false
    detail = 'Preparando seu personagem e conferindo o ponto de entrada.'
    protect()
    publish()
    report('spawn_aguardando')
end)
exports('markFailed', function()
    if not holding or entering then return end
    prepared = false
    failed = true
    detail = 'O ponto de entrada ainda não está pronto. Tente carregar novamente.'
    protect()
    publish()
    report('spawn_falhou')
end)
exports('markReady', function()
    if not holding or entering then return false end
    local ped = PlayerPedId()
    prepared = nativeTrue(NetworkIsSessionStarted()) and nativeTrue(NetworkIsPlayerActive(PlayerId()))
        and nativeTrue(DoesEntityExist(ped)) and not nativeTrue(IsEntityDead(ped))
        and nativeTrue(HasCollisionLoadedAroundEntity(ped))
    failed = not prepared
    detail = prepared and 'Tudo pronto. Clique abaixo para assumir seu personagem.'
        or 'Aguardando o carregamento do ponto de entrada. Tente novamente.'
    protect()
    publish()
    report(prepared and 'spawn_pronto' or 'spawn_nao_confirmado')
    return prepared
end)

RegisterNUICallback('loadingStatus', function(_, cb)
    cb(snapshot())
end)

RegisterNUICallback('loadingDiagnostics', function(_, cb)
    cb(diagnostics())
end)

RegisterNUICallback('loadingLog', function(data, cb)
    cb({ ok = true })
    if type(data) ~= 'table' or type(data.stage) ~= 'string' or #data.stage > 80 then return end
    if #json.encode(data) > 4096 then return end
    report('nui:' .. data.stage, data)
end)

RegisterCommand('entradadiag', function()
    report('comando_diagnostico')
    SendNUIMessage({ eventName = 'cidadeLoadingDiagnose' })
end, false)

RegisterNUICallback('loadingUiReady', function(_, cb)
    cb({ ok = holding })
    if not holding or uiReady then return end
    uiReady = true
    report('interface_carregada')
    SendLoadingScreenMessage(json.encode({ eventName = 'cidadeLoadingHandoff' }))
    CreateThread(function()
        Wait(1500)
        -- A missing audio response must never prevent the entry UI from opening.
        if holding and not uiStarting and not uiActive then report('audio_transferencia_timeout') end
        activateInteractive({}, 95)
    end)
end)

RegisterNUICallback('loadingHandoff', function(data, cb)
    local accepted = holding and not entering and uiReady and not uiStarting and not uiActive
    cb({ ok = accepted })
    report(accepted and 'audio_transferido' or 'audio_transferencia_ignorada')
    if accepted then activateInteractive(data.audio, data.progress) end
end)

RegisterNUICallback('loadingUiActive', function(_, cb)
    -- A lost HTTP reply can be retried without resetting native focus.
    if holding and uiActive then cb({ ok = true }); return end
    if not holding or entering or not uiStarting then cb({ ok = false }); return end
    uiStarting = false
    uiActive = true
    cb({ ok = true })
    closeInitialNui()
    report('interface_visivel')
    CreateThread(function()
        Wait(0)
        if not holding or not uiActive then return end
        SetNuiFocusKeepInput(false)
        SetNuiFocus(true, true)
        publish()
        report('interface_com_foco')
    end)
end)

RegisterNUICallback('loadingAdvance', function(_, cb)
    if not holding or entering or not prepared then
        report('entrada_clique_rejeitado')
        cb({ ok = false, detail = 'Aguarde a preparação do personagem.' })
        return
    end
    if not nativeTrue(NetworkIsSessionStarted()) or not nativeTrue(NetworkIsPlayerActive(PlayerId()))
        or nativeTrue(IsEntityDead(PlayerPedId())) or not nativeTrue(HasCollisionLoadedAroundEntity(PlayerPedId())) then
        prepared = false
        failed = true
        detail = 'O ponto de entrada precisa ser carregado novamente.'
        publish()
        report('entrada_colisao_perdida')
        cb({ ok = false, detail = detail })
        return
    end
    entering = true
    report('entrada_clique_aceito')
    cb({ ok = true })
    CreateThread(function()
        publish()
        -- Music/UI fade while the ped remains protected.
        Wait(550)
        ShutdownLoadingScreen()
        closeInitialNui()
        holding = false
        SendNUIMessage({ eventName = 'cidadeLoadingClose' })
        uiActive = false
        RenderScriptCams(false, false, 0, true, false)
        if nativeTrue(IsPlayerSwitchInProgress()) then StopPlayerSwitch() end
        ClearFocus()
        release()
        DoScreenFadeIn(500)
        TriggerEvent('cidade_loading:entered')
        report('entrada_liberada')
        CreateThread(function()
            Wait(1500)
            report('apos_entrada')
            SendNUIMessage({ eventName = 'cidadeLoadingDiagnose' })
        end)
    end)
end)

RegisterNUICallback('loadingRetry', function(_, cb)
    if not holding or entering or prepared or GetGameTimer() - retryAt < 5000 then
        cb({ ok = false })
        return
    end
    if GetResourceState('cidade_core') ~= 'started' then
        cb({ ok = false, detail = 'Aguardando os recursos do personagem.' })
        return
    end
    retryAt = GetGameTimer()
    failed = false
    detail = 'Tentando carregar o ponto de entrada novamente.'
    publish()
    local ok = pcall(function() exports.cidade_core:retryLoadingSpawn() end)
    report(ok and 'spawn_nova_tentativa' or 'spawn_tentativa_erro')
    cb({ ok = ok })
end)

CreateThread(function()
    local nextUpdate = 0
    while true do
        if holding then
            protect()
            DisableAllControlActions(0)
            DisablePlayerFiring(PlayerId(), true)
            HideHudAndRadarThisFrame()
            if GetGameTimer() >= nextUpdate then
                publish()
                nextUpdate = GetGameTimer() + 1000
            end
            Wait(0)
        else
            Wait(250)
        end
    end
end)

AddEventHandler('onClientResourceStop', function(name)
    if name == GetCurrentResourceName() and holding then
        holding = false
        ShutdownLoadingScreen()
        closeInitialNui()
        SendNUIMessage({ eventName = 'cidadeLoadingClose' })
        uiActive = false
        release()
        DoScreenFadeIn(300)
        report('recurso_parado')
    end
end)

CreateThread(function() Wait(0); report('recurso_iniciado') end)
