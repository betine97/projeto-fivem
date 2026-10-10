local marker, watching, lastTick, label = nil,false,0,nil
local function line(text) print('^5[ADM]^7 '..text) end
local function serverEvent() return source==65535 end
local function clear()
    if marker then RemoveBlip(marker);marker=nil end
    watching=false;label=nil
end
local function locate(s,track,quiet)
    if type(s)~='table' or type(s.x)~='number' or type(s.y)~='number' or type(s.z)~='number' or type(s.id)~='number' then return end
    local me=GetEntityCoords(PlayerPedId());local d=#(me-vector3(s.x,s.y,s.z));local zone=GetNameOfZone(s.x,s.y,s.z);local region=GetLabelText(zone);if region=='NULL' then region=zone end
    if not quiet then line(('ID %d | %s | %s | %.1f m | x=%.2f y=%.2f z=%.2f | instancia %s'):format(s.id,s.name,region,d,s.x,s.y,s.z,s.bucket));line('Use encontrar '..s.id..' para ir ate ele ou chamar '..s.id..' para traze-lo.') end
    if not marker then marker=AddBlipForCoord(s.x,s.y,s.z);SetBlipSprite(marker,1);SetBlipColour(marker,5);SetBlipScale(marker,.85);SetBlipAsShortRange(marker,false) else SetBlipCoords(marker,s.x,s.y,s.z) end
    BeginTextCommandSetBlipName('STRING');AddTextComponentSubstringPlayerName(('ID %d - %s'):format(s.id,s.name));EndTextCommandSetBlipName(marker)
    watching=track;label=('Rastreando ID %d - %s | %.0f m | instancia %s'):format(s.id,s.name,d,s.bucket);lastTick=GetGameTimer()
end
RegisterNetEvent('cidade_admin:location',function(s,track)if serverEvent() then clear();locate(s,track,false) end end)
RegisterNetEvent('cidade_admin:trackingTick',function(s)if serverEvent() and watching then locate(s,true,true) end end)
RegisterNetEvent('cidade_admin:clearTracking',function()if serverEvent() then clear() end end)
RegisterNetEvent('cidade_admin:players',function(players)
    if not serverEvent() or type(players)~='table' then return end
    line(('Jogadores online: %d. IDs permanentes do painel:'):format(#players))
    for _,p in ipairs(players) do line(('ID %d | %s | %.2f, %.2f, %.2f | instancia %s'):format(p.id,p.name,p.x,p.y,p.z,p.bucket)) end
end)
RegisterNetEvent('cidade_admin:equipmentGranted',function(action,value,ammo)
    if not serverEvent() then return end
    if action=='weapon' then TriggerEvent('cidade_core:adminWeapon',value,ammo)
    elseif action=='vehicle' then TriggerEvent('cidade_core:adminVehicle',value)
    elseif action=='disarm' then TriggerEvent('cidade_core:adminDisarm')
    elseif action=='deleteVehicle' then TriggerEvent('cidade_core:adminDeleteVehicle') end
end)
RegisterCommand('admin',function()
    line('Ajuda no F8. Use os IDs permanentes do painel. Seu ADM: '..(LocalPlayer.state.cidadeAdmin and 'autorizado' or 'aguardando autorizacao'))
    for _,v in ipairs(CidadeAdminCatalogo.comandos) do line(v[1]..' — '..v[2]) end
end,false)
RegisterCommand('coords',function()
    local ped=PlayerPedId();local p=GetEntityCoords(ped);line(('x=%.3f y=%.3f z=%.3f heading=%.2f'):format(p.x,p.y,p.z,GetEntityHeading(ped)))
end,false)
RegisterCommand('armas',function(_,args)
    local filter=table.concat(args,' '):lower();local count=0;line('Armas disponiveis nesta versao:')
    for _,v in ipairs(CidadeAdminCatalogo.armas) do
        if IsWeaponValid(joaat('WEAPON_'..v[2])) and (filter=='' or table.concat(v,' '):lower():find(filter,1,true)) then line(('arma %s 120 | %s | WEAPON_%s'):format(v[1],v[3],v[2]));count=count+1 end
    end
    line(count..' armas. Tambem aceita o nome WEAPON_ completo. Use desarmar para remover suas armas.')
end,false)
RegisterCommand('veiculos',function(_,args)
    local filter=table.concat(args,' '):lower();local count=0
    if filter=='todos' then
        local models=GetAllVehicleModels();table.sort(models);line('Todos os modelos carregados:')
        local page={};for _,name in ipairs(models) do if IsModelAVehicle(joaat(name)) then page[#page+1]=name;count=count+1;if #page==9 then line(table.concat(page,' | '));page={} end end end
        if #page>0 then line(table.concat(page,' | ')) end
    else
        line('Catalogo de veiculos; use veiculos todos para ver todos os modelos carregados.')
        for _,v in ipairs(CidadeAdminCatalogo.veiculos) do if IsModelInCdimage(joaat(v[1])) and IsModelAVehicle(joaat(v[1])) and (filter=='' or table.concat(v,' '):lower():find(filter,1,true)) then line('veiculo '..v[1]..' | '..v[2]);count=count+1 end end
    end
    line(count..' modelos. Exemplo: veiculo ambulance. O proximo substitui o seu anterior; dv remove.')
end,false)
RegisterCommand('comandos',function(_,args)
    local filter=table.concat(args,' '):lower();local out={};line('Comandos do cliente ativos na cidade:')
    for _,v in ipairs(GetRegisteredCommands()) do
        if v.resource and (v.resource:sub(1,7)=='cidade_' or v.resource=='fpv_drone_runtime') and not v.name:match('^[%+%-]') and (filter=='' or v.name:lower():find(filter,1,true)) then out[#out+1]=v.name..' ['..v.resource..']' end
    end
    table.sort(out);for _,v in ipairs(out) do line(v) end
    line('Use admin para exemplos; armas e veiculos mostram os catalogos.')
    if #args<=1 then ExecuteCommand('comandosservidor'..(args[1] and ' '..args[1] or '')) end
end,false)
RegisterNetEvent('cidade_admin:serverCommands',function(rows)if serverEvent() then line('Comandos do servidor autorizados:');table.sort(rows,function(a,b)return a.name<b.name end);for _,v in ipairs(rows) do line(v.name..' ['..v.resource..']') end end end)
CreateThread(function()
    while true do
        if marker and (not LocalPlayer.state.cidadeAdmin or GetGameTimer()-lastTick>(watching and 7500 or 60000)) then clear() end
        if watching and label then BeginTextCommandDisplayHelp('STRING');AddTextComponentSubstringPlayerName(label..'~n~F8: pararrastreio para encerrar.');EndTextCommandDisplayHelp(0,false,true,2100) end
        Wait(1000)
    end
end)
AddEventHandler('onResourceStop',function(name)if name==GetCurrentResourceName() then clear() end end)
