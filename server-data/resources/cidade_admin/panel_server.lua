-- NUI requests never run commands in the server console. Each action is
-- authorized against the current verified account, then granted to its caller.
local catalog = json.decode(LoadResourceFile(GetCurrentResourceName(),'ui/catalog.json') or '{}')
local models, commandIndex, sessions, clocks = {vehicles={},weapons={},npcs={}}, {}, {}, {}
for kind, index in pairs(models) do
    for _, row in ipairs(catalog[kind] or {}) do index[row.model]=true end
end
for _, row in ipairs(catalog.commands or {}) do commandIndex[row.name]=row end
local ticketCounter=0
local function account(id)
    if not id or id<=0 or GetResourceState('cidade_acesso')~='started' then return nil end
    local r=exports.cidade_acesso:GetVerifiedRecord(id)
    if r and IsPlayerAceAllowed(id,'cidade.admin') then return r end
end
local function sameEntity(row)
    return row.entity and DoesEntityExist(row.entity)
        and NetworkGetNetworkIdFromEntity(row.entity)==row.netId
        and GetEntityModel(row.entity)==row.hash
end
local function discard(session)
    for _,row in pairs(session.npcs) do if sameEntity(row) then DeleteEntity(row.entity) end end
end
local function sessionFor(id,r)
    local s=sessions[id]
    if s and s.permanent~=r.id then discard(s);s=nil end
    if not s then s={permanent=r.id,npcs={},reservations={}};sessions[id]=s end
    return s
end
local function reply(id,nonce,ok,message,data)
    TriggerClientEvent('cidade_admin:panelReply',id,nonce,{ok=ok,message=message,data=data})
end
local function safeModel(value)
    return type(value)=='string' and #value>0 and #value<=64 and value:match('^[%w_]+$') and value:lower()
end
local function throttle(id,action,delay)
    clocks[id]=clocks[id] or {};local now=GetGameTimer();local previous=clocks[id][action]
    if previous and now-previous<delay then return false end
    clocks[id][action]=now;return true
end
local function npcList(s)
    local rows={}
    for ticket,row in pairs(s.npcs) do
        if sameEntity(row) then rows[#rows+1]={id=ticket,model=row.model,netId=row.netId}
        else s.npcs[ticket]=nil end
    end
    table.sort(rows,function(a,b)return a.id<b.id end);return rows
end
local function playerList()
    local out={}
    for _,handle in ipairs(GetPlayers()) do
        local id=tonumber(handle);local r=exports.cidade_acesso:GetVerifiedRecord(id)
        if r then out[#out+1]={id=r.id,name=r.name,bucket=GetPlayerRoutingBucket(id)} end
    end
    table.sort(out,function(a,b)return a.id<b.id end);return out
end
local function commandList(id)
    local rows,index={},{}
    for name,row in pairs(commandIndex) do
        local copy={};for key,value in pairs(row) do copy[key]=value end
        copy.active=GetResourceState(row.resource)=='started';rows[#rows+1]=copy;index[name]=copy
    end
    for _,row in ipairs(GetRegisteredCommands()) do
        if row.resource and (row.resource:match('^cidade_') or row.resource=='teste_ilha' or row.resource=='fpv_drone_runtime') and not row.name:match('^[%+%-]') then
            if not index[row.name] then
                local entry={name=row.name,usage=row.name,resource=row.resource,category='Outros',description='Comando ativo do recurso '..row.resource..'.',active=true}
                rows[#rows+1]=entry;index[row.name]=entry
            end
            -- Restricted commands retain their own ACE checks when executed.
            index[row.name].server=true
            index[row.name].allowed=row.restricted~=true or IsPlayerAceAllowed(id,'command.'..row.name)
        end
    end
    table.sort(rows,function(a,b)return a.name<b.name end);return rows
end
RegisterNetEvent('cidade_admin:panelRequest',function(nonce,request)
    local id=tonumber(source)
    if type(nonce)~='number' or nonce%1~=0 or nonce<1 or nonce>2147483647 or type(request)~='table' then return end
    local r=account(id)
    if not r then reply(id,nonce,false,'Seu acesso ADM não está autorizado.');return end
    local action=request.action
    local delays={open=500,players=800,vehicle=2500,weapon=800,disarm=800,deleteVehicle=800,npc=800,npcBring=500,npcDelete=500,npcClear=800,command=500,npcList=500}
    if not delays[action] then reply(id,nonce,false,'Ação inválida.');return end
    if not throttle(id,action,delays[action]) then reply(id,nonce,false,'Aguarde um instante antes de repetir.');return end
    local s=sessionFor(id,r)
    if action=='open' then
        reply(id,nonce,true,'',{id=r.id,name=r.name,players=playerList(),commands=commandList(id),npcs=npcList(s)})
    elseif action=='players' then reply(id,nonce,true,'',{players=playerList()})
    elseif action=='npcList' then reply(id,nonce,true,'',{npcs=npcList(s)})
    elseif action=='vehicle' or action=='weapon' then
        local model=safeModel(request.model)
        if not model then reply(id,nonce,false,'Nome de modelo inválido.');return end
        if action=='weapon' then
            if not models.weapons[model] then reply(id,nonce,false,'Arma fora do catálogo.');return end
            local ammo=request.ammo
            if type(ammo)~='number' or ammo~=ammo or ammo%1~=0 or ammo<0 or ammo>9999 then reply(id,nonce,false,'Munição deve ser um inteiro entre 0 e 9999.');return end
        end
        -- Additional streamed vehicles are checked by IsModelAVehicle on the
        -- client, as in the existing veiculo command. No raw console input.
        TriggerClientEvent('cidade_admin:equipmentGranted',id,action,model,request.ammo)
        reply(id,nonce,true,action=='weapon' and 'Arma solicitada.' or 'Veículo solicitado; você entrará ao carregar.')
    elseif action=='disarm' or action=='deleteVehicle' then
        TriggerClientEvent('cidade_admin:equipmentGranted',id,action)
        reply(id,nonce,true,action=='disarm' and 'Remoção de armas solicitada.' or 'Remoção do veículo solicitada.')
    elseif action=='npc' then
        local model=safeModel(request.model)
        if not model or not models.npcs[model] then reply(id,nonce,false,'NPC fora do catálogo.');return end
        local count=#npcList(s)
        for key,pending in pairs(s.reservations) do
            if GetGameTimer()-pending.at>15000 then s.reservations[key]=nil else count=count+1 end
        end
        if count>=12 then reply(id,nonce,false,'Limite de 12 NPCs. Remova um antes de criar outro.');return end
        ticketCounter=ticketCounter+1
        s.reservations[ticketCounter]={model=model,at=GetGameTimer()}
        reply(id,nonce,true,'Carregando NPC…',{ticket=ticketCounter,model=model,permanent=r.id})
    elseif action=='npcBring' or action=='npcDelete' then
        local row=s.npcs[request.id]
        if not row or not sameEntity(row) then reply(id,nonce,false,'Esse NPC não está mais disponível.');return end
        if action=='npcDelete' then DeleteEntity(row.entity);s.npcs[request.id]=nil
        else
            local ped=GetPlayerPed(id)
            if not ped or ped==0 or not DoesEntityExist(ped) then reply(id,nonce,false,'Seu personagem ainda não está pronto.');return end
            local p=GetEntityCoords(ped);local heading=GetEntityHeading(ped);local a=math.rad(heading)
            SetEntityCoords(row.entity,p.x-math.sin(a)*3,p.y+math.cos(a)*3,p.z,false,false,false,false)
            SetEntityHeading(row.entity,heading+180)
        end
        reply(id,nonce,true,action=='npcDelete' and 'NPC removido.' or 'NPC trazido para perto.',{npcs=npcList(s)})
    elseif action=='npcClear' then
        discard(s);s.npcs={};s.reservations={}
        reply(id,nonce,true,'Seus NPCs foram removidos.',{npcs={}})
    elseif action=='command' then
        local name=safeModel(request.name)
        local args=request.args or ''
        if not name or type(args)~='string' or #args>120 or args:find('[^%w_%.%-%+ ]') then reply(id,nonce,false,'Comando ou argumentos inválidos.');return end
        local row=commandIndex[name]
        for _,registered in ipairs(GetRegisteredCommands()) do
            if registered.name==name and registered.resource and (registered.resource:match('^cidade_') or registered.resource=='teste_ilha' or registered.resource=='fpv_drone_runtime') then
                if registered.restricted and not IsPlayerAceAllowed(id,'command.'..name) then reply(id,nonce,false,'Sem permissão para esse comando.');return end
                row=registered;break
            end
        end
        if not row or GetResourceState(row.resource)~='started' then reply(id,nonce,false,'Esse comando pertence a um recurso desligado.');return end
        if name=='painel' or name=='paineladm' or name=='npcs' then reply(id,nonce,false,'O painel já está aberto.');return end
        reply(id,nonce,true,'Comando enviado ao jogo.',{name=name,args=args})
    end
end)
RegisterNetEvent('cidade_admin:panelNpcCreated',function(ticket,netId)
    local id=tonumber(source);local r=account(id);local s=sessions[id]
    if not s or not r or s.permanent~=r.id or type(ticket)~='number' or type(netId)~='number' then return end
    local pending=s.reservations[ticket];if not pending then return end
    if netId==0 then s.reservations[ticket]=nil;return end
    local entity=NetworkGetEntityFromNetworkId(netId)
    if GetGameTimer()-pending.at>15000 or entity==0 or not DoesEntityExist(entity)
        or GetEntityType(entity)~=1 or NetworkGetEntityOwner(entity)~=id
        or GetEntityModel(entity)~=GetHashKey(pending.model) then return end
    for _,handle in ipairs(GetPlayers()) do if GetPlayerPed(tonumber(handle))==entity then return end end
    s.reservations[ticket]=nil
    s.npcs[ticket]={entity=entity,netId=netId,model=pending.model,hash=GetEntityModel(entity)}
    if SetEntityOrphanMode then SetEntityOrphanMode(entity,2) end
    TriggerClientEvent('cidade_admin:panelNpcAck',id,ticket)
    TriggerClientEvent('cidade_admin:panelNpcs',id,npcList(s))
end)
CreateThread(function()
    while true do
        Wait(2000)
        for id,s in pairs(sessions) do
            local r=account(id)
            if not r or r.id~=s.permanent then
                discard(s);sessions[id]=nil;TriggerClientEvent('cidade_admin:panelClose',id)
            else
                for ticket,pending in pairs(s.reservations) do if GetGameTimer()-pending.at>15000 then s.reservations[ticket]=nil end end
            end
        end
    end
end)
AddEventHandler('playerDropped',function()
    local id=tonumber(source);if sessions[id] then discard(sessions[id]) end
    sessions[id]=nil;clocks[id]=nil
end)
AddEventHandler('onResourceStop',function(name)
    if name==GetCurrentResourceName() then for _,s in pairs(sessions) do discard(s) end end
end)
