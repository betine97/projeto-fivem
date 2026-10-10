local resource=GetCurrentResourceName()
local active,selected,hover,test,waiting=false,nil,nil,nil,false
local cursor={x=.5,y=.5};local pending,seq={},0
local function say(text)
    print('^5[Captura de objetos]^7 '..text)
    BeginTextCommandThefeedPost('STRING');AddTextComponentSubstringPlayerName(text);EndTextCommandThefeedPostTicker(false,false)
end
local function close()
    active=false;selected=nil;hover=nil;test=nil;waiting=false
    SetNuiFocus(false,false);SetNuiFocusKeepInput(false);SendNUIMessage({type='close'})
end
local function request(data,cb)
    seq=seq%2147483646+1;pending[seq]={cb=cb,at=GetGameTimer()}
    TriggerServerEvent('cidade_captura:request',seq,data)
end
RegisterNetEvent('cidade_captura:reply',function(nonce,result)
    if source~=65535 or type(result)~='table' or not pending[nonce] then return end
    local cb=pending[nonce].cb;pending[nonce]=nil;cb(result)
end)
local function vec(v)return {x=v.x,y=v.y,z=v.z}end
local function inspect(entity,point)
    if entity~=0 and DoesEntityExist(entity) and GetEntityType(entity)~=1 and GetEntityType(entity)~=2 then
        local hash=GetEntityModel(entity)%4294967296
        local lo,hi=GetModelDimensions(hash)
        return {entity=entity,kind='object',hash=hash,position=vec(GetEntityCoords(entity)),hit=vec(point),rotation=vec(GetEntityRotation(entity,2)),bbMin=vec(lo),bbMax=vec(hi)}
    end
    return {entity=0,kind='surface',position=vec(point),hit=vec(point)}
end
local function outline(row)
    if not row then return end
    local h=row.hit
    DrawMarker(28,h.x,h.y,h.z,0,0,0,0,0,0,.12,.12,.12,100,255,190,210,false,false,2,false,nil,nil,false)
    if row.entity==0 or not DoesEntityExist(row.entity) then return end
    local lo,hi=row.bbMin,row.bbMax;local points={}
    for _,z in ipairs({lo.z,hi.z}) do for _,y in ipairs({lo.y,hi.y}) do for _,x in ipairs({lo.x,hi.x}) do points[#points+1]=GetOffsetFromEntityInWorldCoords(row.entity,x,y,z) end end end
    for _,edge in ipairs({{1,2},{1,3},{2,4},{3,4},{5,6},{5,7},{6,8},{7,8},{1,5},{2,6},{3,7},{4,8}}) do
        local a,b=points[edge[1]],points[edge[2]];DrawLine(a.x,a.y,a.z,b.x,b.y,b.z,100,255,190,230)
    end
end
RegisterCommand('capturarobjeto',function()
    if active then close();return end
    if not LocalPlayer.state.cidadeAdmin then say('Aguarde sua autorização ADM carregar.');return end
    if IsNuiFocused() then say('Feche o painel atual antes de selecionar objetos.');return end
    active=true;selected=nil;hover=nil;cursor={x=.5,y=.5}
    SetNuiFocus(true,true);SetNuiFocusKeepInput(false);SendNUIMessage({type='open'})
    say('Clique no objeto de Los Santos ou Cayo Perico e salve no catálogo compartilhado. Esc fecha para caminhar ou voar.')
end,false)
RegisterCommand('capturas',function()request({action='list'},function(r)
    say(r.message or '')
    for _,row in ipairs(r.rows or {}) do print(('[Captura] #%d | %s | %s | %s'):format(row.id,row.name,row.model or 'trecho para análise',row.status))end
end)end,false)
RegisterNUICallback('close',function(_,cb)close();cb({ok=true})end)
RegisterNUICallback('cursor',function(data,cb)
    if active and type(data.x)=='number' and type(data.y)=='number' then cursor.x=math.max(0,math.min(1,data.x));cursor.y=math.max(0,math.min(1,data.y))end
    cb({ok=true})
end)
RegisterNUICallback('pick',function(_,cb)
    if not active or waiting or not hover then cb({ok=false,message='Aponte para um objeto próximo e aguarde a marcação verde.'});return end
    selected=hover;waiting=true
    local data={action='resolve'};for k,v in pairs(selected)do if k~='entity' then data[k]=v end end
    request(data,function(r)waiting=false;if not r.ok then selected=nil end;if active then SendNUIMessage({type='selection',data=r})end;cb(r)end)
end)
RegisterNUICallback('again',function(_,cb)selected=nil;SendNUIMessage({type='clear'});cb({ok=true})end)
RegisterNUICallback('save',function(data,cb)
    if not active or waiting or not selected then cb({ok=false,message='Selecione um objeto primeiro.'});return end
    waiting=true;local row={action='capture',name=data.name,category=data.category}
    for k,v in pairs(selected)do if k~='entity' then row[k]=v end end
    request(row,function(r)waiting=false;if r.ok then selected=nil;SendNUIMessage({type='clear'});say(r.message)end;cb(r)end)
end)
CreateThread(function()
    while true do
        if not active then Wait(250)else
            Wait(0)
            if not LocalPlayer.state.cidadeAdmin or IsEntityDead(PlayerPedId())then close()else
                DisableControlAction(0,24,true);DisableControlAction(0,25,true)
                outline(selected or hover)
                if not selected then
                    if test then
                        local state,hit,pos,_,entity=GetShapeTestResult(test)
                        if state~=1 then
                            test=nil;hover=(state==2 and (hit==true or hit==1))and inspect(entity,pos)or nil
                            SendNUIMessage({type='hover',object=hover and hover.kind=='object' or false,hit=hover~=nil})
                        end
                    else
                        local origin,direction=GetWorldCoordFromScreenCoord(cursor.x,cursor.y)
                        local target=origin+direction*250
                        test=StartShapeTestRay(origin.x,origin.y,origin.z,target.x,target.y,target.z,273,PlayerPedId(),7)
                    end
                end
            end
        end
    end
end)
CreateThread(function()
    while true do Wait(500);for nonce,row in pairs(pending)do if GetGameTimer()-row.at>15000 then
        pending[nonce]=nil;waiting=false;row.cb({ok=false,message='Tempo esgotado. Tente novamente.'})
    end end end
end)
AddEventHandler('onResourceStop',function(name)if name==resource then close()end end)
