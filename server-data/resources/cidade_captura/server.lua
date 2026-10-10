local url=GetConvar('cidade_captura_url','http://127.0.0.1:8788')
local key=GetConvar('cidade_acesso_key','')
local clocks={}
local function finite(v)return type(v)=='number' and v==v and math.abs(v)<math.huge end
local function vector(v,limit)
    return type(v)=='table' and finite(v.x) and finite(v.y) and finite(v.z)
        and math.abs(v.x)<=limit and math.abs(v.y)<=limit and math.abs(v.z)<=limit
end
RegisterNetEvent('cidade_captura:request',function(nonce,data)
    local id=tonumber(source)
    local function reply(result)TriggerClientEvent('cidade_captura:reply',id,nonce,result)end
    if not id or id<1 or not finite(nonce) or nonce%1~=0 or nonce<1 or nonce>2147483647 or type(data)~='table' then return end
    local record=exports.cidade_acesso:GetVerifiedRecord(id)
    if not record or not IsPlayerAceAllowed(id,'cidade.admin') then reply({ok=false,message='Seu acesso ADM ainda não está autorizado.'});return end
    if GetPlayerRoutingBucket(id)~=0 then reply({ok=false,message='Use a instância principal da cidade.'});return end
    local now=GetGameTimer()
    if clocks[id] and now-clocks[id]<400 then reply({ok=false,message='Aguarde um instante.'});return end
    clocks[id]=now
    local path
    if data.action=='list' then path='/list';data={}
    elseif data.action=='resolve' or data.action=='capture' then
        if not vector(data.position,20000) then reply({ok=false,message='Posição inválida.'});return end
        local ped=GetPlayerPed(id)
        if ped==0 or not DoesEntityExist(ped) then reply({ok=false,message='Seu personagem ainda está carregando.'});return end
        local p=GetEntityCoords(ped);local t=data.position
        if (p.x-t.x)^2+(p.y-t.y)^2+(p.z-t.z)^2>350^2 then reply({ok=false,message='Aproxime-se do objeto (até 350 metros).'});return end
        if data.kind~='surface' then
            if not finite(data.hash) or data.hash%1~=0 or data.hash<1 or data.hash>4294967295
                or not vector(data.bbMin,1000) or not vector(data.bbMax,1000) then reply({ok=false,message='Modelo inválido.'});return end
        end
        path=data.action=='capture' and '/capture' or '/resolve'
        data.author={id=record.id,name=record.name}
        data.origin=GetConvar('cidade_modo','ilha')=='cidade' and 'Los Santos' or (t.x>=1750 and t.x<=4750 and t.y>=-1700 and t.y<=1700 and 'Cayo Perico' or 'Nossa ilha')
    else reply({ok=false,message='Ação inválida.'});return end
    local identity=record.id
    PerformHttpRequest(url..path,function(code,body)
        local current=exports.cidade_acesso:GetVerifiedRecord(id)
        if not current or current.id~=identity or not IsPlayerAceAllowed(id,'cidade.admin') then return end
        local ok,result=pcall(json.decode,body or '')
        if code~=200 or not ok or type(result)~='table' then
            reply({ok=false,message='Serviço de captura indisponível. Abra iniciar-captura.cmd.'})
            print('[Captura de objetos] falha HTTP '..tostring(code));return
        end
        reply(result)
    end,'POST',json.encode(data),{['Content-Type']='application/json',['X-Cidade-Key']=key})
end)
AddEventHandler('playerDropped',function()clocks[tonumber(source)]=nil end)
