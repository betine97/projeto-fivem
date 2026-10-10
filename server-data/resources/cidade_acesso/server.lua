local endpoint = GetConvar('cidade_acesso_url', 'http://127.0.0.1:8787')
local key = GetConvar('cidade_acesso_key', '')
local adminSessions = {}
local onlineRecords = {}
local teleportCooldowns = {}
local function primaryIdentity(identifiers)
    for _,prefix in ipairs({'license:', 'license2:', 'fivem:'}) do
        for _,value in ipairs(identifiers or {}) do
            if type(value) == 'string' and value:sub(1, #prefix) == prefix then return value end
        end
    end
    return nil
end
local function revokeAdmin(id)
    id = tonumber(id)
    if id then onlineRecords[id] = nil; teleportCooldowns[id] = nil end
    if not id or not adminSessions[id] then return end
    ExecuteCommand(('remove_principal player.%d group.admin'):format(id))
    adminSessions[id] = nil
    if GetPlayerName(id) then Player(id).state:set('cidadeAdmin', false, true) end
end
local function grantAdmin(id)
    if not adminSessions[id] then
        ExecuteCommand(('add_principal player.%d group.admin'):format(id))
        adminSessions[id] = true
    end
    Player(id).state:set('cidadeAdmin', IsPlayerAceAllowed(id, 'cidade.admin'), true)
end
local function sameAccount(snapshot)
    if not GetPlayerName(snapshot.source) then return false end
    return primaryIdentity(snapshot.identifiers) == primaryIdentity(GetPlayerIdentifiers(snapshot.source))
end
local function applyAccess(snapshot, record)
    -- Never give a late response's permissions to another account reusing the handle.
    if not sameAccount(snapshot) then return end
    local id = snapshot.source
    if record.status ~= 'approved' then
        revokeAdmin(id)
        DropPlayer(id, ('Acesso não autorizado. Seu ID é %d. Peça aprovação no painel.'):format(record.id))
    else
        grantAdmin(id)
        onlineRecords[id] = {source=id,id=tonumber(record.id),identifiers=snapshot.identifiers}
        Player(id).state:set('cidadeId', record.id, true)
        Player(id).state:set('cidadeNome', record.name, true)
    end
end
local function request(path, body, callback)
    if key == '' then callback(0, nil); return end
    PerformHttpRequest(endpoint..path, function(code, data)
        local ok, result = pcall(json.decode, data or '')
        callback(code, ok and result or nil)
    end, 'POST', json.encode(body), {['Content-Type']='application/json', ['X-Cidade-Key']=key})
end
AddEventHandler('playerConnecting', function(name, _, deferrals)
    local player = source
    deferrals.defer()
    Wait(0)
    deferrals.update('Conferindo sua autorização na cidade...')
    local complete = false
    local function finish(reason)
        if complete then return end
        complete = true
        Wait(0)
        -- An explicit nil is still one argument: FiveM rejects it as "Unknown error".
        if reason == nil then
            deferrals.done()
        else
            deferrals.done(reason)
        end
    end
    request('/bridge/check', {name=name, identifiers=GetPlayerIdentifiers(player)}, function(code, record)
        if code ~= 200 or not record or not record.id then
            finish('O painel de acesso está indisponível. Peça ao dono para abrir iniciar-painel.cmd.')
        elseif record.status == 'approved' then
            finish()
        elseif record.status == 'blocked' then
            finish(('Seu acesso está bloqueado. Seu ID é %d. Fale com o dono da cidade.'):format(record.id))
        else
            finish(('Seu ID é %d. Aguarde o dono autorizar sua entrada no painel e conecte novamente.'):format(record.id))
        end
    end)
    SetTimeout(12000, function() finish('Tempo esgotado ao consultar o acesso. Tente novamente com o painel aberto.') end)
end)

AddEventHandler('playerJoining', function()
    local id = tonumber(source)
    revokeAdmin(id)
    local snapshot = {source=id,name=GetPlayerName(id),identifiers=GetPlayerIdentifiers(id)}
    request('/bridge/check', snapshot, function(code, record)
        if code == 200 and record and record.id then applyAccess(snapshot, record) end
    end)
end)
AddEventHandler('playerDropped', function() revokeAdmin(source) end)
AddEventHandler('onResourceStop', function(resource)
    if resource ~= GetCurrentResourceName() then return end
    local ids = {}
    for id in pairs(adminSessions) do ids[#ids+1] = id end
    for _,id in ipairs(ids) do revokeAdmin(id) end
end)

local function notice(id, text)
    TriggerClientEvent('cidade_acesso:notice', id, text)
end
local function teleportCommand(command, bring)
    RegisterCommand(command, function(player, args)
        local caller = tonumber(player)
        if not caller or caller <= 0 then print('[Minha Cidade] Use '..command..' ID no F8 do jogador.'); return end
        local callerRecord = onlineRecords[caller]
        if not callerRecord or not sameAccount(callerRecord) or not IsPlayerAceAllowed(caller, 'cidade.admin') then
            notice(caller, 'Este comando precisa da sua autorização ADM. Aguarde carregar seu ID.')
            return
        end
        local permanentId = args[1] and args[1]:match('^%d+$') and tonumber(args[1])
        if not permanentId or permanentId < 1 or #args ~= 1 then notice(caller, 'Use '..command..' ID. Exemplo: '..command..' 2'); return end
        local target
        for id,record in pairs(onlineRecords) do
            if record.id == permanentId and sameAccount(record) then target=id; break end
        end
        if not target then notice(caller, ('O jogador ID %d está offline ou ainda está entrando.'):format(permanentId)); return end
        if target == caller then notice(caller, 'Esse é o seu próprio ID.'); return end
        local now = GetGameTimer()
        if teleportCooldowns[caller] and now-teleportCooldowns[caller] < 2000 then notice(caller, 'Aguarde um instante entre os teletransportes.'); return end
        local moving, destination = bring and target or caller, bring and caller or target
        local ped = GetPlayerPed(destination)
        if not ped or ped == 0 or not DoesEntityExist(ped) then notice(caller, 'O personagem de destino ainda não está pronto.'); return end
        local position = GetEntityCoords(ped)
        teleportCooldowns[caller] = now
        SetPlayerRoutingBucket(moving, GetPlayerRoutingBucket(destination))
        TriggerClientEvent('cidade_acesso:teleport', moving, {x=position.x,y=position.y,z=position.z+0.1,heading=GetEntityHeading(ped)})
        notice(caller, bring and ('Chamando o jogador ID %d para você.'):format(permanentId) or ('Indo até o jogador ID %d.'):format(permanentId))
        if bring then notice(target, ('Você foi chamado pelo ADM ID %d.'):format(callerRecord.id)) end
    end, true)
end
teleportCommand('encontrar', false)
teleportCommand('chamar', true)

-- Other resources use the same verified account snapshots and permanent IDs.
exports('GetVerifiedRecord', function(player)
    local id = tonumber(player)
    local record = id and onlineRecords[id]
    if not record or not sameAccount(record) then return nil end
    return {source=id,id=record.id,name=Player(id).state.cidadeNome or GetPlayerName(id)}
end)
exports('ResolvePermanentId', function(permanentId)
    permanentId = tonumber(permanentId)
    for id,record in pairs(onlineRecords) do
        if record.id == permanentId and sameAccount(record) then
            return {source=id,id=record.id,name=Player(id).state.cidadeNome or GetPlayerName(id)}
        end
    end
end)

CreateThread(function()
    while true do
        local players = {}
        for _,id in ipairs(GetPlayers()) do
            players[#players+1] = {source=tonumber(id),name=GetPlayerName(id),identifiers=GetPlayerIdentifiers(id)}
        end
        request('/bridge/heartbeat', {players=players,server=GetConvar('cidade_servidor_id','ilhas')}, function(code, result)
            if code ~= 200 or not result or not result.players then return end
            for _,record in ipairs(result.players) do
                for _,snapshot in ipairs(players) do
                    if snapshot.source == record.source then applyAccess(snapshot, record); break end
                end
            end
        end)
        Wait(5000)
    end
end)
