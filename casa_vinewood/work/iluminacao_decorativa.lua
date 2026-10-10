-- Visible fixtures are native emissive geometry. This single controller owns
-- diffuse ceiling, room bounce, pendant and stair lighting with a shared budget.
local config = json.decode(LoadResourceFile(GetCurrentResourceName(), 'iluminacao_ambiente.json'))
local origin = vector3(config.origin[1], config.origin[2], config.origin[3])
local lights, active, target = {}, {}, {}
local gain, lastCount, lastStrength = 1.0, 0, 0
for _, row in ipairs(config.lights) do
    row.world = origin + vector3(row.position[1], row.position[2], row.position[3])
    lights[#lights+1] = row
end

local function nightStrength()
    local hour = GetClockHours() + GetClockMinutes()/60.0
    local night
    if hour >= 20.0 or hour < 5.0 then night = 1.0
    elseif hour >= 18.0 then night = (hour-18.0)/2.0
    elseif hour < 8.0 then night = (8.0-hour)/3.0
    else night = 0.0 end
    night = night*night*(3.0-2.0*night)
    return config.day_multiplier + night*(config.night_multiplier-config.day_multiplier)
end

local function selectLights(camera, player)
    local level = player.z-origin.z > 3.1 and 'superior' or 'terreo'
    local groups = {ambient={}, fixture={}, pendant={}, stair={}}
    for _, row in ipairs(lights) do
        local distance = math.min(#(row.world-camera), #(row.world-player))
        if distance < config.selection_distance then
            local score = distance
            -- Prefer the occupied storey. Keep the double-height living room
            -- available when viewed from the mezzanine, without selecting all floors.
            if row.level ~= 'both' and row.level ~= level then score = score + 6.0 end
            if target[row.id] then score = score - .8 end -- stable selection near ties
            groups[row.kind][#groups[row.kind]+1] = {row=row, score=score}
        end
    end
    target = {}
    for kind, candidates in pairs(groups) do
        table.sort(candidates, function(a,b)
            if a.score == b.score then return a.row.id < b.row.id end
            return a.score < b.score
        end)
        local chosen = {}
        for _, item in ipairs(candidates) do
            local spaced = true
            if kind == 'ambient' then
                for _, row in ipairs(chosen) do
                    if row.level == item.row.level and #(row.world-item.row.world) < 4.0 then
                        spaced = false; break
                    end
                end
            end
            if spaced then
                chosen[#chosen+1] = item.row
                target[item.row.id] = true
                if not active[item.row.id] then
                    active[item.row.id] = {row=item.row, fade=0.0}
                end
                if #chosen >= config.budgets[kind] then break end
            end
        end
    end
    -- Reserve four draw slots for fading lights; all categories share this cap.
    local retire, count = {}, 0
    for id, state in pairs(active) do
        if target[id] then count=count+1
        else retire[#retire+1] = {id=id, fade=state.fade} end
    end
    table.sort(retire, function(a,b) return a.fade > b.fade end)
    for i=config.max_lights-count+1,#retire do active[retire[i].id] = nil end
end

RegisterCommand('luzmansao', function(_, args)
    local value = tonumber(args[1])
    if value then gain = math.max(.5, math.min(2.0, value)) end
    print(('[Mansao luz] intensidade %.2f; %d/%d luzes; fator horario %.2f'):format(
        gain, lastCount, config.max_lights, lastStrength))
end, false)

CreateThread(function()
    local nextSelection, previous = 0, GetGameTimer()
    while true do
        local player, camera = GetEntityCoords(PlayerPedId()), GetGameplayCamCoord()
        if #(player-origin) < 45.0 or #(camera-origin) < 45.0 then
            local now = GetGameTimer()
            if now >= nextSelection then
                selectLights(camera, player)
                nextSelection = now + config.selection_ms
            end
            local delta = math.max(0, math.min(100, now-previous))/config.fade_ms
            previous = now
            local strength = nightStrength()*gain
            lastStrength, lastCount = strength, 0
            for id, state in pairs(active) do
                state.fade = math.max(0, math.min(1, state.fade + (target[id] and delta or -delta)))
                if state.fade <= 0 and not target[id] then active[id] = nil
                elseif state.fade > 0 then
                    local row = state.row
                    local p, c = row.world, row.rgb
                    local fade = state.fade*state.fade*(3.0-2.0*state.fade)
                    DrawLightWithRange(p.x,p.y,p.z,c[1],c[2],c[3],row.range,row.intensity*strength*fade)
                    lastCount = lastCount+1
                end
            end
            Wait(0)
        else
            active, target = {}, {}
            nextSelection, lastCount = 0, 0
            Wait(1000)
            previous = GetGameTimer()
        end
    end
end)
