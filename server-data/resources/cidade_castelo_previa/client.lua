local entry = vector3(-951.5, 194.375644, 67.7)
local previous = nil
local travelling = false

local function message(text)
    print('[Castelo] '..text)
    BeginTextCommandThefeedPost('STRING')
    AddTextComponentSubstringPlayerName(text)
    EndTextCommandThefeedPostTicker(false, false)
end
RegisterNetEvent('cidade_castelo:mensagem', message)

local function travel(position, heading)
    if travelling then return end
    travelling = true
    CreateThread(function()
        TriggerEvent('cidade:preparePilot')
        TriggerEvent('cidade:stopProne')
        local ped = PlayerPedId()
        if IsPedInAnyVehicle(ped, false) then
            message('Saia do veiculo para visitar o castelo a pe.')
            travelling = false
            return
        end
        local old = GetEntityCoords(ped)
        local oldHeading = GetEntityHeading(ped)
        RequestCollisionAtCoord(position.x, position.y, position.z)
        NewLoadSceneStartSphere(position.x, position.y, position.z, 100.0, 0)
        local deadline = GetGameTimer() + 7000
        while not IsNewLoadSceneLoaded() and GetGameTimer() < deadline do Wait(0) end
        FreezeEntityPosition(ped, true)
        SetEntityCoordsNoOffset(ped, position.x, position.y, position.z, false, false, false)
        SetEntityHeading(ped, heading)
        deadline = GetGameTimer() + 5000
        while not HasCollisionLoadedAroundEntity(ped) and GetGameTimer() < deadline do
            RequestCollisionAtCoord(position.x, position.y, position.z)
            Wait(0)
        end
        if not HasCollisionLoadedAroundEntity(ped) then
            SetEntityCoordsNoOffset(ped, old.x, old.y, old.z, false, false, false)
            SetEntityHeading(ped, oldHeading)
            message('A colisao ainda nao carregou. Tente novamente em alguns segundos.')
        else
            message('Castelo em escala real. Caminhe pela entrada. Use voltarcastelo para retornar.')
        end
        NewLoadSceneStop()
        FreezeEntityPosition(ped, false)
        travelling = false
    end)
end

RegisterNetEvent('cidade_castelo:visitar', function()
    if travelling then return end
    if not previous then previous = {position=GetEntityCoords(PlayerPedId()), heading=GetEntityHeading(PlayerPedId())} end
    travel(entry, 330.0)
end)
RegisterCommand('voltarcastelo', function()
    if not previous or travelling then return end
    local destination = previous
    travel(destination.position, destination.heading)
    previous = nil
end, false)

AddEventHandler('onResourceStop', function(resource)
    if resource == GetCurrentResourceName() and travelling then
        FreezeEntityPosition(PlayerPedId(), false)
        NewLoadSceneStop()
    end
end)
