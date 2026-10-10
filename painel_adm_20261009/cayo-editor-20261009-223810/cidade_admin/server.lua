local tracking, limits = {}, {}
local function notice(id,text) TriggerClientEvent('cidade_acesso:notice',id,text) end
local function record(id)
    if GetResourceState('cidade_acesso') ~= 'started' then return nil end
    return exports.cidade_acesso:GetVerifiedRecord(id)
end
local function authorized(id)
    id=tonumber(id)
    return id and id>0 and record(id) and IsPlayerAceAllowed(id,'cidade.admin')
end
local function gate(id,action,delay)
    if not authorized(id) then notice(id,'Este comando precisa da sua autorizacao ADM no painel.');return false end
    limits[id]=limits[id] or {}
    local now=GetGameTimer();local last=limits[id][action]
    if last and now-last<(delay or 800) then notice(id,'Aguarde um instante antes de repetir.');return false end
    limits[id][action]=now;return true
end
local function snapshot(r)
    local ped=GetPlayerPed(r.source)
    if not ped or ped==0 or not DoesEntityExist(ped) then return nil end
    local p=GetEntityCoords(ped)
    return {id=r.id,name=r.name,x=p.x,y=p.y,z=p.z,bucket=GetPlayerRoutingBucket(r.source),heading=GetEntityHeading(ped)}
end
local function target(id,args,command)
    if #args~=1 or not args[1]:match('^%d+$') or tonumber(args[1])<1 then notice(id,'Use '..command..' ID. Exemplo: '..command..' 2');return nil end
    local r=exports.cidade_acesso:ResolvePermanentId(tonumber(args[1]))
    if not r then notice(id,'Esse ID esta offline ou ainda esta entrando.');return nil end
    local s=snapshot(r)
    if not s then notice(id,'O personagem desse jogador ainda nao esta pronto.');return nil end
    return s
end
RegisterCommand('jogadores',function(id,args)
    if id<=0 then print('[ADM] Use jogadores no F8.');return end
    if not gate(id,'players',1000) then return end
    if #args>0 then notice(id,'Use jogadores, sem argumentos.');return end
    local result={}
    for _,handle in ipairs(GetPlayers()) do local r=record(tonumber(handle));if r then local s=snapshot(r);if s then result[#result+1]=s end end end
    table.sort(result,function(a,b)return a.id<b.id end)
    TriggerClientEvent('cidade_admin:players',id,result)
end,true)
for _,command in ipairs({'onde','localizar','rastrear'}) do
    RegisterCommand(command,function(id,args)
        if id<=0 then print('[ADM] Use '..command..' ID no F8.');return end
        if not gate(id,'locate',800) then return end
        local s=target(id,args,command);if not s then return end
        tracking[id]=nil
        if command=='rastrear' then tracking[id]={permanent=s.id,owner=record(id).id} end
        TriggerClientEvent('cidade_admin:location',id,s,command=='rastrear')
    end,true)
end
RegisterCommand('pararrastreio',function(id)
    tracking[id]=nil
    if id>0 then TriggerClientEvent('cidade_admin:clearTracking',id);notice(id,'Rastreamento encerrado.') end
end,false)
RegisterNetEvent('cidade_admin:equipment',function(action,value,ammo)
    local id=tonumber(source)
    if type(action)~='string' or (action~='weapon' and action~='vehicle' and action~='disarm' and action~='deleteVehicle') then return end
    if not gate(id,action,action=='vehicle' and 2500 or 800) then return end
    if action=='weapon' or action=='vehicle' then
        if type(value)~='string' or #value>64 or not value:match('^[%w_]+$') then notice(id,'Nome de modelo invalido.');return end
        value=value:lower()
    end
    if action=='weapon' then
        if type(ammo)~='number' or ammo~=ammo or ammo%1~=0 or ammo<0 or ammo>9999 then notice(id,'Municao deve ser um inteiro entre 0 e 9999.');return end
        for _,v in ipairs(CidadeAdminCatalogo.armas) do if v[1]==value then value='weapon_'..v[2]:lower();break end end
        if value:sub(1,7)~='weapon_' then value='weapon_'..value end
    end
    TriggerClientEvent('cidade_admin:equipmentGranted',id,action,value,ammo)
    print(('[ADM] ID %d: %s %s'):format(record(id).id,action,value or ''))
end)
RegisterCommand('comandosservidor',function(id,args)
    if not gate(id,'commands',1000) then return end
    local filter=(args[1] or ''):lower();local out={}
    if #filter>64 or #args>1 then notice(id,'Use comandos [filtro].');return end
    for _,v in ipairs(GetRegisteredCommands()) do
        if v.resource and v.resource:sub(1,7)=='cidade_' and (filter=='' or v.name:lower():find(filter,1,true)) and IsPlayerAceAllowed(id,'command.'..v.name) then out[#out+1]={name=v.name,resource=v.resource} end
    end
    TriggerClientEvent('cidade_admin:serverCommands',id,out)
end,true)
CreateThread(function()
    while true do
        Wait(2000)
        for id,t in pairs(tracking) do
            local owner=record(id)
            if not authorized(id) or not owner or owner.id~=t.owner then
                tracking[id]=nil;TriggerClientEvent('cidade_admin:clearTracking',id)
            else
                local r=exports.cidade_acesso:ResolvePermanentId(t.permanent);local s=r and snapshot(r)
                if not s then tracking[id]=nil;TriggerClientEvent('cidade_admin:clearTracking',id);notice(id,'O jogador rastreado saiu ou ainda nao tem personagem.')
                else TriggerClientEvent('cidade_admin:trackingTick',id,s) end
            end
        end
    end
end)
AddEventHandler('playerDropped',function()tracking[tonumber(source)]=nil;limits[tonumber(source)]=nil end)
AddEventHandler('onResourceStop',function(name)if name==GetCurrentResourceName() then TriggerClientEvent('cidade_admin:clearTracking',-1) end end)
