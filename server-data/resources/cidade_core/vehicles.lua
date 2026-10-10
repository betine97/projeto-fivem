-- Ferramentas do ambiente local de desenvolvimento.
local spawning = false
local ownedVehicle = nil
local function notify(text)
    print('[Veiculos] ' .. text)
    BeginTextCommandThefeedPost('STRING')
    AddTextComponentSubstringPlayerName(text)
    EndTextCommandThefeedPostTicker(false, false)
end

local function deleteOwned()
    if ownedVehicle and DoesEntityExist(ownedVehicle) then
        SetEntityAsMissionEntity(ownedVehicle, true, true)
        DeleteVehicle(ownedVehicle)
        if DoesEntityExist(ownedVehicle) then return false end
    end
    ownedVehicle = nil
    return true
end

local function spawnVehicle(_, args)
    if spawning then notify('Aguarde o carregamento do veiculo.'); return end
    local name = (args[1] or ''):lower()
    if name == '' then
        notify('Use: veiculo adder (carro), luxor (aviao), buzzard (helicoptero), bati (moto), dinghy (barco).')
        return
    end
    local hash = joaat(name)
    if not IsModelInCdimage(hash) or not IsModelAVehicle(hash) then
        notify('Modelo de veiculo inexistente nesta versao do GTA: ' .. name)
        return
    end
    if IsEntityDead(PlayerPedId()) then notify('Use reviver primeiro.'); return end
    if GetResourceState('fpv_drone_runtime') == 'started' and exports.fpv_drone_runtime:isPiloting() then
        notify('Desligue a pilotagem do drone primeiro: dronedesligar.'); return
    end
    spawning = true
    RequestModel(hash)
    local deadline = GetGameTimer() + 10000
    while not HasModelLoaded(hash) and GetGameTimer() < deadline do Wait(20) end
    local ped = PlayerPedId()
    local piloting = GetResourceState('fpv_drone_runtime') == 'started' and exports.fpv_drone_runtime:isPiloting()
    if not HasModelLoaded(hash) or IsEntityDead(ped) or piloting then
        SetModelAsNoLongerNeeded(hash)
        spawning = false
        notify('Carregamento cancelado ou demorou demais. Tente novamente.')
        return
    end
    TriggerEvent('cidade:preparePilot')
    local minimum, maximum = GetModelDimensions(hash)
    local distance = math.max(5.0, maximum.y - minimum.y + 2.0)
    local position = GetOffsetFromEntityInWorldCoords(ped, 0.0, distance, 0.5)
    local vehicle = CreateVehicle(hash, position.x, position.y, position.z, GetEntityHeading(ped), true, true)
    SetModelAsNoLongerNeeded(hash)
    spawning = false
    if vehicle == 0 or not DoesEntityExist(vehicle) then notify('Nao foi possivel criar o veiculo.'); return end
    if not deleteOwned() then
        DeleteVehicle(vehicle)
        notify('Nao foi possivel remover o veiculo anterior. Tente dv antes.')
        return
    end
    ownedVehicle = vehicle
    SetVehicleOnGroundProperly(vehicle)
    SetVehicleDirtLevel(vehicle, 0.0)
    SetVehicleFuelLevel(vehicle, 100.0)
    SetVehicleEngineOn(vehicle, true, true, false)
    if name == 'sertao' then
        SetVehicleCustomPrimaryColour(vehicle, 66, 72, 42)
        SetVehicleCustomSecondaryColour(vehicle, 40, 44, 30)
        SetVehicleNumberPlateText(vehicle, 'SERTAO')
    end
    SetVehRadioStation(vehicle, 'OFF')
    SetPedIntoVehicle(ped, vehicle, -1)
    notify('Veiculo criado: ' .. name .. '. Use dv para remover. O proximo substitui este.')
end

local function requestVehicle(_,args)
    if #args~=1 then notify('Use veiculo MODELO. Use veiculos para o catalogo.');return end
    TriggerServerEvent('cidade_admin:equipment','vehicle',args[1])
end
AddEventHandler('cidade_core:adminVehicle',function(name)
    if GetInvokingResource()=='cidade_admin' then spawnVehicle(0,{name}) end
end)
RegisterCommand('veiculo', requestVehicle, false)
RegisterCommand('car', requestVehicle, false)
RegisterCommand('carro', requestVehicle, false)
RegisterCommand('sertao', function() requestVehicle(0, {'sertao'}) end, false)
RegisterCommand('jeepmilitar', function() requestVehicle(0, {'jeepmilitar'}) end, false)
AddTextEntry('JEEPMIL', 'Jeep Militar WWII')
AddTextEntry('SERTAO', 'Sertao')
AddTextEntry('CIDADE', 'Cidade')
RegisterCommand('dv', function() TriggerServerEvent('cidade_admin:equipment','deleteVehicle') end,false)
AddEventHandler('cidade_core:adminDeleteVehicle',function()
    if GetInvokingResource()~='cidade_admin' then return end
    if spawning then notify('Aguarde o carregamento.'); return end
    if not ownedVehicle then notify('Nenhum veiculo criado por voce para remover.'); return end
    notify(deleteOwned() and 'Seu veiculo foi removido.' or 'Falha ao remover; tente novamente.')
end)
AddEventHandler('onResourceStop', function(resource)
    if resource == GetCurrentResourceName() then deleteOwned() end
end)
