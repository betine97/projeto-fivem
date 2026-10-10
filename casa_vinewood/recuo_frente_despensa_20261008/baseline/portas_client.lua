-- Each movable leaf has hinge-space physics, never a fixed world collider.
local resource = GetCurrentResourceName()
local config = json.decode(LoadResourceFile(resource, 'portas_madeira.json'))
local origin = vector3(table.unpack(config.origin))
local states, entities, angles, transitions = {}, {}, {}, {}
local running = true
local function world(p) return origin + vector3(table.unpack(p)) end

local function apply(id, opened, instant)
    states[id] = opened
    local d = config.doors[id]
    if not d or not entities[id] then return end
    local target = opened and d.open_heading or d.closed_heading
    if instant then
        angles[id], transitions[id] = target, nil
        SetEntityRotation(entities[id], 0.0, 0.0, target, 2, true)
    else
        transitions[id] = { from = angles[id] or d.closed_heading,
            target = target, started = GetGameTimer() }
    end
end
RegisterNetEvent('cidade_mansao:doorStates', function(snapshot)
    if type(snapshot) ~= 'table' then return end
    for _, d in ipairs(config.doors) do
        apply(d.id, snapshot[d.id] == true or snapshot[tostring(d.id)] == true, true)
    end
end)
RegisterNetEvent('cidade_mansao:doorState', function(id, opened)
    if type(id) ~= 'number' or type(opened) ~= 'boolean' or not config.doors[id] then return end
    apply(id, opened, false)
end)
local function removeDoors()
    for id, entity in pairs(entities) do
        if DoesEntityExist(entity) then DeleteEntity(entity) end
        entities[id], angles[id], transitions[id] = nil, nil, nil
    end
end
CreateThread(function()
    while running do
        local near = #(GetEntityCoords(PlayerPedId()) - origin) < 85.0
        if near then
            for _, d in ipairs(config.doors) do
                if not entities[d.id] then
                    local hash = GetHashKey(d.model)
                    RequestModel(hash)
                    local deadline = GetGameTimer() + 12000
                    while running and not HasModelLoaded(hash) and GetGameTimer() < deadline do Wait(25) end
                    if running and HasModelLoaded(hash) then
                        local p = world(d.hinge)
                        local entity = CreateObjectNoOffset(hash, p.x, p.y, p.z, false, false, false)
                        if entity ~= 0 then
                            entities[d.id] = entity
                            SetEntityAsMissionEntity(entity, true, true)
                            FreezeEntityPosition(entity, true)
                            SetEntityCollision(entity, true, true)
                            apply(d.id, states[d.id] == true, true)
                        end
                        SetModelAsNoLongerNeeded(hash)
                    end
                end
            end
        elseif next(entities) then removeDoors() end
        Wait(1500)
    end
end)
CreateThread(function()
    TriggerServerEvent('cidade_mansao:requestDoorStates')
    local lastRequest = -1000
    while running do
        local wait = 350
        for id, transition in pairs(transitions) do
            local t = math.min(1.0, (GetGameTimer() - transition.started) / 550.0)
            local ease = t * t * (3.0 - 2.0 * t)
            angles[id] = transition.from + (transition.target - transition.from) * ease
            if entities[id] then SetEntityRotation(entities[id], 0.0, 0.0, angles[id], 2, true) end
            if t >= 1.0 then transitions[id] = nil end
            wait = 0
        end
        local ped = PlayerPedId()
        if IsPedOnFoot(ped) then
            local p = GetEntityCoords(ped)
            local nearest, distance = nil, 1.8
            for _, d in ipairs(config.doors) do
                local delta = #(p - world(d.opening_center))
                if entities[d.id] and delta < distance then nearest, distance = d, delta end
            end
            if nearest then
                wait = 0
                BeginTextCommandDisplayHelp('STRING')
                AddTextComponentSubstringPlayerName('~INPUT_CONTEXT~ ' .. (states[nearest.id] and 'Fechar' or 'Abrir') .. ' porta: ' .. nearest.name)
                EndTextCommandDisplayHelp(0, false, false, -1)
                if IsControlJustReleased(0, 38) and GetGameTimer() - lastRequest > 700 then
                    lastRequest = GetGameTimer()
                    TriggerServerEvent('cidade_mansao:toggleDoor', nearest.id)
                end
            end
        end
        Wait(wait)
    end
end)
RegisterNetEvent('cidade_mansao:doorOccupied', function()
    BeginTextCommandDisplayHelp('STRING')
    AddTextComponentSubstringPlayerName('Afaste-se do vão para fechar a porta.')
    EndTextCommandDisplayHelp(0, false, false, 2500)
end)
AddEventHandler('onResourceStop', function(name)
    if name ~= resource then return end
    running = false
    removeDoors()
end)
