local resource=GetCurrentResourceName()
local catalog=json.decode(LoadResourceFile(resource,'ui/catalog.json') or '{}')
local islandCatalog=json.decode(LoadResourceFile(resource,'ui/cayo.json') or '{}')
local opened, opening, npcBusy=false,false,false
local requests, sequence, owned, commandIndex, confirmations={},0,{},{},{}
local function message(text)
    print('^5[Painel ADM]^7 '..text)
    BeginTextCommandThefeedPost('STRING');AddTextComponentSubstringPlayerName(text);EndTextCommandThefeedPostTicker(false,false)
end
local function close()
    opened=false;opening=false;SetNuiFocus(false,false);SendNUIMessage({type='close'})
end
local function request(data,callback)
    sequence=sequence%2147483646+1
    requests[sequence]={callback=callback,at=GetGameTimer(),action=data.action}
    TriggerServerEvent('cidade_admin:panelRequest',sequence,data)
end
RegisterNetEvent('cidade_admin:panelReply',function(nonce,result)
    if source~=65535 or type(result)~='table' then return end
    local pending=requests[nonce];if not pending then return end
    requests[nonce]=nil;pending.callback(result)
end)
RegisterNetEvent('cidade_admin:panelClose',function()if source==65535 then close() end end)
RegisterNetEvent('cidade_admin:panelNpcs',function(rows)
    if source~=65535 or type(rows)~='table' then return end
    SendNUIMessage({type='npcs',rows=rows})
end)
RegisterNetEvent('cidade_admin:panelNpcAck',function(ticket)
    if source==65535 then confirmations[ticket]=true end
end)
local filtered
local function availableCatalog()
    -- Re-evaluate streamed add-ons whenever opening (resources can start later).
    local out={vehicles={},weapons={},npcs={}}
    local seen={}
    for kind,rows in pairs(out) do
        for index,row in ipairs(catalog[kind] or {}) do
            local hash=joaat(row.model)
            local valid=kind=='weapons' and IsWeaponValid(hash)
                or kind=='vehicles' and IsModelInCdimage(hash) and IsModelAVehicle(hash)
                or kind=='npcs' and IsModelInCdimage(hash) and IsModelAPed(hash)
            if valid then rows[#rows+1]=row;if kind=='vehicles' then seen[row.model]=true end end
            if index%150==0 then Wait(0) end
        end
    end
    for _,name in ipairs(GetAllVehicleModels()) do
        name=name:lower()
        if not seen[name] and IsModelAVehicle(joaat(name)) then
            out.vehicles[#out.vehicles+1]={model=name,name=name,category='Outros modelos carregados',image='fallback.svg'}
        end
    end
    out.cayo={}
    for index,row in ipairs(islandCatalog.objects or {}) do
        if IsModelInCdimage(joaat(row.model)) and IsModelValid(joaat(row.model)) then out.cayo[#out.cayo+1]=row end
        if index%100==0 then Wait(0) end
    end
    for _,row in ipairs(CidadeCapturedCatalog.objects)do
        -- Keep captures visible even before their streamed archetype is ready.
        -- Loading is checked again when starting the preview.
        out.cayo[#out.cayo+1]=row
    end
    filtered=out;return out
end
local function commands(rows)
    local index={};commandIndex={}
    for _,row in ipairs(rows or {}) do index[row.name]=row end
    for _,row in ipairs(GetRegisteredCommands()) do
        if row.resource and (row.resource:match('^cidade_') or row.resource=='teste_ilha' or row.resource=='fpv_drone_runtime') and not row.name:match('^[%+%-]') then
            if not index[row.name] then index[row.name]={name=row.name,usage=row.name,resource=row.resource,category='Outros',description='Comando ativo do recurso '..row.resource..'.'} end
            index[row.name].active=true
        end
    end
    local result={}
    for name,row in pairs(index) do result[#result+1]=row;commandIndex[name]=row end
    table.sort(result,function(a,b)return a.name<b.name end);return result
end
local function open(tab)
    if opening then return end
    if opened then close();return end
    opening=true
    request({action='open'},function(result)
        if not opening then return end
        if not result.ok then opening=false;message(result.message);return end
        CreateThread(function()
            local list=availableCatalog()
            if not opening or not LocalPlayer.state.cidadeAdmin then opening=false;return end
            local data=result.data;data.commands=commands(data.commands)
            data.catalog=list;data.tab=tab or 'vehicles'
            data.captured= CidadeCapturedCatalog.objects
            data.captureMarks= CidadeCapturedCatalog.marks
            opening=false;opened=true
            SendNUIMessage({type='open',data=data});SetNuiFocus(true,true)
        end)
    end)
end
RegisterCommand('painel',function(_,args)
    if #args==1 and args[1]:lower()=='adm' then open()
    else message('Use painel adm no F8.') end
end,false)
RegisterCommand('paineladm',function()open()end,false)
RegisterCommand('npcs',function()open('npcs')end,false)
RegisterCommand('editorilha',function()open('cayo')end,false)
CidadeAdminPanel={close=close,open=open,message=message,isOpen=function()return opened end}
RegisterNUICallback('close',function(_,cb)close();cb({ok=true})end)
local function modelValid(action,model)
    if type(model)~='string' or #model>64 or not model:match('^[%w_]+$') then return false end
    local hash=joaat(model)
    if action=='weapon' then return IsWeaponValid(hash) end
    if action=='vehicle' then return IsModelInCdimage(hash) and IsModelAVehicle(hash) end
    return IsModelInCdimage(hash) and IsModelAPed(hash)
end
local function spawnNpc(data,cb)
    if npcBusy then cb({ok=false,message='Um NPC já está carregando.'});return end
    npcBusy=true
    request({action='npc',model=data.model},function(result)
        if not result.ok then npcBusy=false;cb(result);return end
        local grant=result.data
        CreateThread(function()
            local hash=joaat(grant.model);RequestModel(hash)
            local deadline=GetGameTimer()+10000
            while not HasModelLoaded(hash) and GetGameTimer()<deadline do Wait(20) end
            local player=PlayerPedId()
            if not HasModelLoaded(hash) or not LocalPlayer.state.cidadeAdmin or LocalPlayer.state.cidadeId~=grant.permanent or IsEntityDead(player) then
                SetModelAsNoLongerNeeded(hash);TriggerServerEvent('cidade_admin:panelNpcCreated',grant.ticket,0)
                npcBusy=false;cb({ok=false,message='Carregamento do NPC cancelado. Verifique o modelo ou use reviver.'});return
            end
            local offset=GetOffsetFromEntityInWorldCoords(player,0.0,3.0,0.0)
            local found,z=GetGroundZFor_3dCoord(offset.x,offset.y,offset.z+2.0,false)
            local ped=CreatePed(4,hash,offset.x,offset.y,found and z or offset.z,GetEntityHeading(player)+180,true,true)
            SetModelAsNoLongerNeeded(hash)
            if ped==0 or not DoesEntityExist(ped) then
                TriggerServerEvent('cidade_admin:panelNpcCreated',grant.ticket,0);npcBusy=false;cb({ok=false,message='Não foi possível criar esse NPC.'});return
            end
            SetEntityAsMissionEntity(ped,true,true);SetPedCanRagdoll(ped,true)
            SetBlockingOfNonTemporaryEvents(ped,true);SetPedDefaultComponentVariation(ped)
            TaskStandStill(ped,-1)
            local netId=NetworkGetNetworkIdFromEntity(ped)
            SetNetworkIdCanMigrate(netId,true)
            owned[ped]={netId=netId,hash=hash}
            -- Retry registration briefly while OneSync creates the server entity.
            for _=1,8 do
                TriggerServerEvent('cidade_admin:panelNpcCreated',grant.ticket,netId);Wait(250)
                if confirmations[grant.ticket] then break end
            end
            if not confirmations[grant.ticket] then
                if DoesEntityExist(ped) then DeleteEntity(ped) end
                owned[ped]=nil;TriggerServerEvent('cidade_admin:panelNpcCreated',grant.ticket,0)
                npcBusy=false;cb({ok=false,message='O servidor não confirmou o NPC. Tente novamente.'});return
            end
            confirmations[grant.ticket]=nil
            npcBusy=false;cb({ok=true,message='NPC criado perto de você: '..grant.model})
            request({action='npcList'},function(r)if r.ok then SendNUIMessage({type='npcs',rows=r.data.npcs}) end end)
        end)
    end)
end
RegisterCommand('npc',function(_,args)
    if #args~=1 or not modelValid('npc',args[1]) then message('Use npc MODELO. Exemplo: npc s_m_y_cop_01');return end
    spawnNpc({model=args[1]:lower()},function(r)message(r.message)end)
end,false)
RegisterNUICallback('action',function(data,cb)
    if not opened or not LocalPlayer.state.cidadeAdmin then cb({ok=false,message='Abra o painel com acesso ADM.'});return end
    if type(data)~='table' then cb({ok=false,message='Pedido inválido.'});return end
    local action=data.action
    if action=='npc' then
        if not modelValid(action,data.model) then cb({ok=false,message='NPC indisponível nesta versão.'});return end
        spawnNpc(data,cb);return
    end
    if action=='vehicle' or action=='weapon' then
        if GetResourceState('cidade_core')~='started' then cb({ok=false,message='O recurso cidade_core está desligado.'});return end
        if not modelValid(action,data.model) then cb({ok=false,message='Modelo indisponível nesta versão.'});return end
    elseif action=='command' then
        local row=commandIndex[data.name]
        if not row or not row.active then cb({ok=false,message='Recurso do comando desligado.'});return end
    elseif action~='players' and action~='npcBring' and action~='npcDelete' and action~='npcClear' and action~='npcList' and action~='disarm' and action~='deleteVehicle' then
        cb({ok=false,message='Ação inválida.'});return
    end
    request(data,function(result)
        if result.ok and action=='command' then
            local row=commandIndex[result.data.name]
            if row and row.active then
                close();ExecuteCommand(result.data.name..(result.data.args~='' and ' '..result.data.args or ''))
            end
        elseif result.ok and action=='vehicle' then close() end
        cb(result)
    end)
end)
CreateThread(function()
    while true do
        Wait(500)
        if (opened or opening) and not LocalPlayer.state.cidadeAdmin then close() end
        for nonce,pending in pairs(requests) do
            if GetGameTimer()-pending.at>12000 then
                requests[nonce]=nil;pending.callback({ok=false,message='Servidor não respondeu. Tente novamente.'})
            end
        end
        for ped,row in pairs(owned) do
            if not DoesEntityExist(ped) or NetworkGetNetworkIdFromEntity(ped)~=row.netId or GetEntityModel(ped)~=row.hash then owned[ped]=nil end
        end
    end
end)
AddEventHandler('onResourceStop',function(name)
    if name~=resource then return end
    close()
    for ped,row in pairs(owned) do
        if DoesEntityExist(ped) and NetworkGetNetworkIdFromEntity(ped)==row.netId and GetEntityModel(ped)==row.hash then DeleteEntity(ped) end
    end
end)
