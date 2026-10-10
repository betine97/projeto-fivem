local resource = GetCurrentResourceName()
local config = json.decode(LoadResourceFile(resource, 'garagem_acesso.json'))
local origin = vector3(table.unpack(config.origin))
local hinge = origin + vector3(table.unpack(config.gate_hinge))
local opened, leaf, angle, transition = false, nil, 0.0, nil
local running, lastToggle, loadReported = true, -2000, false
local function setState(state, instant)
    local desired = state == true
    -- A snapshot answering another load must not snap an ongoing movement.
    if instant and transition and desired == opened then return end
    opened = desired
    local target = opened and -90.0 or 0.0
    if instant then
        angle, transition = target, nil
        if leaf then SetEntityRotation(leaf, angle, 0.0, 0.0, 2, true) end
    else transition = {from = angle, target = target, start = GetGameTimer()} end
end
RegisterNetEvent('cidade_mansao:garageState', function(state, instant) setState(state, instant) end)
RegisterNetEvent('cidade_mansao:garageBlocked', function()
    BeginTextCommandDisplayHelp('STRING')
    AddTextComponentSubstringPlayerName('Afaste pessoas e veiculos da area do portao para fecha-lo.')
    EndTextCommandDisplayHelp(0, false, false, 3000)
end)
CreateThread(function()
    TriggerServerEvent('cidade_mansao:requestGarageState')
    while running do
        local near = #(GetEntityCoords(PlayerPedId()) - hinge) < 160.0
        if near and not leaf then
            local hash = GetHashKey(config.gate_model)
            RequestModel(hash)
            local deadline = GetGameTimer() + 12000
            while running and not HasModelLoaded(hash) and GetGameTimer() < deadline do Wait(25) end
            if running and HasModelLoaded(hash) then
                local object = CreateObjectNoOffset(hash, hinge.x, hinge.y, hinge.z, false, false, false)
                if object ~= 0 then
                    leaf = object
                    SetEntityAsMissionEntity(leaf, true, true)
                    SetEntityLodDist(leaf,220)
                    SetEntityAlwaysPrerender(leaf,true)
                    FreezeEntityPosition(leaf, true)
                    SetEntityCollision(leaf, true, true)
                    setState(opened, true)
                    TriggerServerEvent('cidade_mansao:requestGarageState')
                end
                SetModelAsNoLongerNeeded(hash)
            elseif not loadReported then
                print('[cidade_mansao:garagem] Nao foi possivel carregar o modelo ' .. config.gate_model)
                loadReported = true
            end
        elseif not near and leaf then
            if DoesEntityExist(leaf) then DeleteEntity(leaf) end
            leaf = nil
        end
        Wait(1200)
    end
end)
CreateThread(function()
    local interaction = origin + vector3(table.unpack(config.interaction))
    while running do
        local wait = 300
        if leaf and transition then
            local t = math.min(1.0, (GetGameTimer() - transition.start) / 1800.0)
            local ease = t * t * (3.0 - 2.0 * t)
            angle = transition.from + (transition.target - transition.from) * ease
            SetEntityRotation(leaf, angle, 0.0, 0.0, 2, true)
            if t >= 1 then transition = nil end
            wait = 0
        end
        local playerPosition = GetEntityCoords(PlayerPedId())
        if leaf and playerPosition.z-origin.z < -1.65 and #(playerPosition - interaction) < 7.0 then
            wait = 0
            BeginTextCommandDisplayHelp('STRING')
            AddTextComponentSubstringPlayerName('~INPUT_CONTEXT~ ' .. (opened and 'Fechar' or 'Abrir') .. ' portao da garagem')
            EndTextCommandDisplayHelp(0, false, false, -1)
            if IsControlJustReleased(0, 38) and not transition and GetGameTimer() - lastToggle > 2000 then
                lastToggle = GetGameTimer()
                TriggerServerEvent('cidade_mansao:toggleGarage')
            end
        end
        Wait(wait)
    end
end)
AddEventHandler('onResourceStop', function(name)
    if name ~= resource then return end
    running = false
    if leaf and DoesEntityExist(leaf) then DeleteEntity(leaf) end
end)

-- Read-only diagnostics for the streamed movable gate.
RegisterCommand('garagemdebug',function()
    local info={loaded=leaf~=nil,opened=opened,angle=angle,moving=transition~=nil}
    if leaf and DoesEntityExist(leaf) then
        info.visible=IsEntityVisible(leaf);info.onScreen=IsEntityOnScreen(leaf)
        info.occluded=IsEntityOccluded(leaf)
    end
    print('[GARAGEM] '..json.encode(info))
end,false)
