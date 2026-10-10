local resource = GetCurrentResourceName()
local config = json.decode(LoadResourceFile(resource, 'portas_madeira.json'))
local origin = config.origin
local states, lastToggle = {}, {}
for _, d in ipairs(config.doors) do states[d.id] = false end
RegisterNetEvent('cidade_mansao:requestDoorStates', function()
    TriggerClientEvent('cidade_mansao:doorStates', source, states)
end)
RegisterNetEvent('cidade_mansao:toggleDoor', function(id)
    local player = source
    if type(id) ~= 'number' or id % 1 ~= 0 or not config.doors[id] then return end
    local now = GetGameTimer()
    if lastToggle[player] and now - lastToggle[player] < 650 then return end
    local d, ped = config.doors[id], GetPlayerPed(player)
    if ped == 0 then return end
    local p = GetEntityCoords(ped)
    local c = d.opening_center
    local dx, dy, dz = p.x-origin[1]-c[1], p.y-origin[2]-c[2], p.z-origin[3]-c[3]
    if dx*dx + dy*dy + dz*dz > 2.7*2.7 then return end
    if states[id] then
        local b = d.opening_bounds
        for _, other in ipairs(GetPlayers()) do
            local q = GetPlayerPed(other)
            if q ~= 0 then
                local at = GetEntityCoords(q)
                local x,y,z = at.x-origin[1], at.y-origin[2], at.z-origin[3]
                if x > b[1]-.30 and x < b[2]+.30 and y > b[3]-.35 and y < b[4]+.35
                    and z > b[5] and z < b[6]+.3 then
                    TriggerClientEvent('cidade_mansao:doorOccupied', player)
                    return
                end
            end
        end
    end
    lastToggle[player] = now
    states[id] = not states[id]
    TriggerClientEvent('cidade_mansao:doorState', -1, id, states[id])
end)
AddEventHandler('playerDropped', function() lastToggle[source] = nil end)
