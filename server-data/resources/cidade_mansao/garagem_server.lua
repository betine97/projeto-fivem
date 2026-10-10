local resource = GetCurrentResourceName()
local config = json.decode(LoadResourceFile(resource, 'garagem_acesso.json'))
local origin, opened, lastToggle = config.origin, false, {}
local movingUntil = 0
local function inSweep(entity, padding)
    if entity == 0 or not DoesEntityExist(entity) then return false end
    local p = GetEntityCoords(entity)
    local x, y, z = p.x-origin[1], p.y-origin[2], p.z-origin[3]
    return x > 6.25-padding and x < 12.95+padding
        and y > 6.60-padding and y < 9.75+padding and z > -4.50 and z < -.9
end
RegisterNetEvent('cidade_mansao:requestGarageState', function()
    TriggerClientEvent('cidade_mansao:garageState', source, opened, true)
end)
RegisterNetEvent('cidade_mansao:toggleGarage', function()
    local player, now = source, GetGameTimer()
    if now < movingUntil then return end
    if lastToggle[player] and now-lastToggle[player] < 2100 then return end
    local ped = GetPlayerPed(player)
    if ped == 0 then return end
    local p, c = GetEntityCoords(ped), config.interaction
    if p.z-origin[3] >= -1.65 then return end
    local dx, dy, dz = p.x-origin[1]-c[1], p.y-origin[2]-c[2], p.z-origin[3]-c[3]
    if dx*dx+dy*dy+dz*dz > 8.0*8.0 then return end
    if opened then
        for _, other in ipairs(GetPlayers()) do
            if inSweep(GetPlayerPed(other), .35) then
                TriggerClientEvent('cidade_mansao:garageBlocked', player)
                return
            end
        end
        for _, vehicle in ipairs(GetAllVehicles()) do
            if inSweep(vehicle, 2.8) then
                TriggerClientEvent('cidade_mansao:garageBlocked', player)
                return
            end
        end
    end
    lastToggle[player] = now
    movingUntil = now + 1900
    opened = not opened
    TriggerClientEvent('cidade_mansao:garageState', -1, opened, false)
end)
AddEventHandler('playerDropped', function() lastToggle[source] = nil end)
