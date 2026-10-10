-- Read collision from GTA itself; do not teleport or change the player's physics.
local origin = vector3(-976.101013, 676.730896, 157.835037)
local revision = 'jantar-cozinha-2026-10-07'
local configuredDoors = json.decode(LoadResourceFile(GetCurrentResourceName(), 'portas_madeira.json'))
local doorModels = {}
for _, door in ipairs(configuredDoors.doors) do doorModels[GetHashKey(door.model)] = true end
local running = false
local function position(p, height)
    return origin + vector3(p[1], p[2], p[3] + height)
end
local function awaitShape(handle)
    local deadline = GetGameTimer() + 2000
    while GetGameTimer() < deadline do
        local state, hit, endpoint, normal, entity = GetShapeTestResult(handle)
        -- Depending on the native binding BOOL may arrive as numeric 0/1.
        -- Lua treats 0 as true, so normalize before counting a collision.
        if state == 2 then return hit == true or hit == 1, endpoint, normal, entity end
        if state == 0 then return nil end
        Wait(0)
    end
    return nil
end
local function audit()
    if running then return end
    if #(GetEntityCoords(PlayerPedId()) - origin) > 65.0 then
        print('[Mansao audit] Aproxime-se da mansao para carregar as colisoes.')
        return
    end
    running = true
    RequestCollisionAtCoord(origin.x, origin.y, origin.z)
    Wait(2500)
    local paths = json.decode(LoadResourceFile(GetCurrentResourceName(), 'auditoria_rotas.json'))
    local report = {revision=revision, routes={}, tests=0, unresolved=0, blockers=0, expected_closed_door_hits=0, passed=true}
    for _, path in ipairs(paths) do
        local result = {name=path.name, hits={}, passed=true}
        for _, direction in ipairs({1, -1}) do
            for i=1,#path.points-1 do
                local p, q = path.points[i], path.points[i+1]
                if direction == -1 then p, q = q, p end
                for _, height in ipairs({0.35, 0.85, 1.50}) do
                    local a, b = position(p, height), position(q, height)
                    local radius = height == 0.85 and 0.30 or 0.28
                    -- Include world, objects and glass; ignore only the player.
                    local handle = StartShapeTestCapsule(a.x,a.y,a.z,b.x,b.y,b.z,radius,511,PlayerPedId(),4)
                    local hit, endpoint, normal, entity = awaitShape(handle)
                    report.tests = report.tests + 1
                    if hit == nil then
                        report.unresolved = report.unresolved + 1
                        result.passed = false
                    elseif hit and entity ~= 0 and doorModels[GetEntityModel(entity)] == true then
                        -- An intentional closed door is opened with E. Record
                        -- it separately from unexplained invisible barriers.
                        report.expected_closed_door_hits = report.expected_closed_door_hits + 1
                        result.requires_open_door = true
                    elseif hit then
                        report.blockers = report.blockers + 1
                        result.passed = false
                        result.hits[#result.hits+1] = {
                            height=height, direction=direction,
                            relative={endpoint.x-origin.x,endpoint.y-origin.y,endpoint.z-origin.z},
                            normal={normal.x,normal.y,normal.z},
                            entity=entity, model=entity ~= 0 and GetEntityModel(entity) or 0
                        }
                    end
                end
            end
        end
        report.routes[#report.routes+1] = result
        if not result.passed then report.passed = false end
    end
    TriggerServerEvent('cidade_mansao:collisionAudit', report)
    print(('[Mansao audit] %s: %d testes, %d bloqueios inesperados, %d contatos com portas, %d pendentes.'):format(
        revision,report.tests,report.blockers,report.expected_closed_door_hits,report.unresolved))
    running = false
end
RegisterCommand('mansaoverificar', function() CreateThread(audit) end, false)
CreateThread(function()
    Wait(6000)
    while #(GetEntityCoords(PlayerPedId()) - origin) > 45.0 do Wait(1500) end
    audit()
end)
