local function message(text)
    print('[Minha Cidade] '..text)
    BeginTextCommandThefeedPost('STRING')
    AddTextComponentSubstringPlayerName(text)
    EndTextCommandThefeedPostTicker(false,false)
end
RegisterCommand('id', function()
    local id = LocalPlayer.state.cidadeId
    local name = LocalPlayer.state.cidadeNome
    local text = id and ('Seu ID: %s | Nome: %s'):format(id, name or GetPlayerName(PlayerId())) or 'Seu ID está sendo carregado. Tente novamente em alguns segundos.'
    message(text)
end, false)

RegisterNetEvent('cidade_acesso:notice', function(text)
    if source ~= 65535 or type(text) ~= 'string' then return end
    message(text)
end)
local teleporting, teleportPed = false, nil
local function finishTeleport()
    if teleportPed and DoesEntityExist(teleportPed) then FreezeEntityPosition(teleportPed, false) end
    NewLoadSceneStop()
    if IsScreenFadedOut() or IsScreenFadingOut() then DoScreenFadeIn(150) end
    teleportPed, teleporting = nil, false
end
RegisterNetEvent('cidade_acesso:teleport', function(destination)
    if source ~= 65535 or type(destination) ~= 'table' then return end
    for _,axis in ipairs({'x','y','z','heading'}) do
        local value = destination[axis]
        if type(value) ~= 'number' or value ~= value or math.abs(value) > 100000 then return end
    end
    if teleporting then message('Um teletransporte já está em andamento.'); return end
    teleporting = true
    CreateThread(function()
        local ok, err = pcall(function()
            if GetResourceState('fpv_drone_runtime') == 'started' then ExecuteCommand('dronedesligar') end
            TriggerEvent('cidade:preparePilot')
            TriggerEvent('cidade:stopProne')
            teleportPed = PlayerPedId()
            if IsPedInAnyVehicle(teleportPed, false) then
                TaskLeaveVehicle(teleportPed, GetVehiclePedIsIn(teleportPed, false), 16)
                local deadline = GetGameTimer()+1000
                while IsPedInAnyVehicle(teleportPed, false) and GetGameTimer()<deadline do Wait(0) end
                if IsPedInAnyVehicle(teleportPed, false) then error('Não foi possível sair do veículo. Tente novamente.') end
            end
            ClearPedTasksImmediately(teleportPed)
            FreezeEntityPosition(teleportPed, true)
            DoScreenFadeOut(150)
            RequestCollisionAtCoord(destination.x, destination.y, destination.z)
            NewLoadSceneStartSphere(destination.x, destination.y, destination.z, 60.0, 0)
            local deadline = GetGameTimer()+5000
            while not IsNewLoadSceneLoaded() and GetGameTimer()<deadline do Wait(0) end
            SetEntityCoordsNoOffset(teleportPed, destination.x, destination.y, destination.z, false, false, false)
            SetEntityHeading(teleportPed, destination.heading)
            SetEntityVelocity(teleportPed, 0.0, 0.0, 0.0)
            deadline = GetGameTimer()+3000
            while not HasCollisionLoadedAroundEntity(teleportPed) and GetGameTimer()<deadline do
                RequestCollisionAtCoord(destination.x, destination.y, destination.z)
                Wait(0)
            end
        end)
        finishTeleport()
        message(ok and 'Teletransporte concluído.' or ('Falha no teletransporte: '..tostring(err)))
    end)
end)
AddEventHandler('onResourceStop', function(resource)
    if resource == GetCurrentResourceName() and teleporting then finishTeleport() end
end)
