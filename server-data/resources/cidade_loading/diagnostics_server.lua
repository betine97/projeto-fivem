-- Small per-player trace of entry state. No identifiers, credentials or account data.
local traces, clocks = {}, {}
local function clean(value, depth)
    local kind = type(value)
    if kind == 'boolean' then return value end
    if kind == 'number' then
        if value == value and math.abs(value) < 1e12 then return value end
    elseif kind == 'string' then return value:sub(1, 512)
    elseif kind == 'table' and depth < 4 then
        local out, count = {}, 0
        for key, item in pairs(value) do
            if type(key) == 'string' and #key <= 64 and count < 40 then
                out[key] = clean(item, depth + 1)
                count = count + 1
            end
        end
        return out
    end
end

RegisterNetEvent('cidade_loading:diagnostic', function(data)
    local id, now = tonumber(source), GetGameTimer()
    if not id or id < 1 or type(data) ~= 'table' or type(data.stage) ~= 'string' then return end
    if clocks[id] and now - clocks[id] < 100 then return end
    clocks[id] = now
    local entry = clean(data, 0)
    entry.server_time = os.date('!%Y-%m-%dT%H:%M:%SZ')
    local rows = traces[id] or {}
    rows[#rows + 1] = entry
    while #rows > 64 do table.remove(rows, 1) end
    traces[id] = rows
    SaveResourceFile(GetCurrentResourceName(), 'data/entrada_' .. id .. '.json', json.encode(rows), -1)
    print('[Entrada Cidade] jogador=' .. id .. ' stage=' .. entry.stage .. ' revision=' .. tostring(entry.revision))
end)

AddEventHandler('playerDropped', function()
    local id = tonumber(source)
    traces[id], clocks[id] = nil, nil
end)
