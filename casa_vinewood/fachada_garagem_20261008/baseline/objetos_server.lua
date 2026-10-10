local resource=GetCurrentResourceName()
local M=CidadeObjetos
local catalog=json.decode(LoadResourceFile(resource,'objetos_catalogo.json'))
local definitions,poses,locks,sessions,limits={},{},{},{},{}
local protected={}
for _,name in ipairs(catalog.protectedModels) do protected[GetHashKey(name)]=true end
for _,d in ipairs(catalog.objects) do definitions[d.id]=d; poses[d.id]=M.copy(d) end
local disk={version=1,positions={},generic={}}
local lastDisk
local storageDamaged=false
local function decodeFile(name)
    local raw=LoadResourceFile(resource,name)
    if not raw then return nil end
    local ok,data=pcall(json.decode,raw)
    if ok and type(data)=='table' and data.version==1 and type(data.positions)=='table' and type(data.generic)=='table' then return data,raw end
end
local loaded,raw=decodeFile('objetos_posicoes.json')
if not loaded and LoadResourceFile(resource,'objetos_posicoes.json') then
    loaded,raw=decodeFile('objetos_posicoes.backup.json')
    print('[objetos] Arquivo de posicoes invalido; tentando backup. Consulte objetos_posicoes.json antes de editar.')
    storageDamaged=not loaded
end
if loaded then
    disk,lastDisk=loaded,raw
    for id,d in pairs(disk.generic) do
        if M.generic(d,protected) and id==M.genericId(d) then definitions[id]=d; poses[id]=M.copy(d) end
    end
    for id,p in pairs(disk.positions) do if definitions[id] and M.pose(p) then poses[id]=M.copy(p) end end
end
local function tell(src,msg) TriggerClientEvent('cidade:objetos:notice',src,msg) end
local function admin(src) return src>0 and IsPlayerAceAllowed(src,'cidade.admin') end
local function playerPosition(src)
    local ped=GetPlayerPed(src); if ped==0 then return nil end
    local v=GetEntityCoords(ped); return {v.x,v.y,v.z}
end
local function near(src,d,p)
    local v=playerPosition(src); return v and M.surfaceDistance(d,p,v)<=4.5
end
local function broadcast(id)
    local l=locks[id]
    TriggerClientEvent('cidade:objetos:state',-1,id,poses[id],l and l.owner or false)
end
local function release(id,restore)
    local l=locks[id]; if not l then return end
    if restore then poses[id]=M.copy(l.original) end
    locks[id]=nil; if sessions[l.owner] then sessions[l.owner].id=nil end
    broadcast(id)
end
local function cancelPlayer(src)
    local s=sessions[src]; if s and s.id then release(s.id,true) end
end
local function rate(src,key,ms)
    limits[src]=limits[src] or {}; local now=GetGameTimer(); local previous=limits[src][key]
    if previous and now-previous<ms then return false end
    limits[src][key]=now; return true
end
RegisterNetEvent('cidade:objetos:snapshotRequest',function()
    local src=source; if not rate(src,'snapshot',2000) then return end
    local owners={}; for id,l in pairs(locks) do owners[id]=l.owner end
    TriggerClientEvent('cidade:objetos:snapshot',src,definitions,poses,owners)
end)
RegisterNetEvent('cidade:objetos:toggle',function(enabled)
    local src=source; if not rate(src,'toggle',300) then return end
    cancelPlayer(src)
    if enabled==true and admin(src) and not storageDamaged then sessions[src]={}; TriggerClientEvent('cidade:objetos:mode',src,true)
    else sessions[src]=nil; TriggerClientEvent('cidade:objetos:mode',src,false)
        if enabled==true then tell(src,storageDamaged and 'Arquivo de posicoes e backup invalidos. Edicao bloqueada para preservar os dados.' or 'Este modo exige permissao de administrador.') end
    end
end)
RegisterNetEvent('cidade:objetos:lock',function(id,generic)
    local src=source
    if not rate(src,'lock',350) or not admin(src) or not sessions[src] or sessions[src].id then return end
    if type(id)~='string' or #id>120 then return end
    local d=definitions[id]
    if not d then
        local count=0; for _ in pairs(definitions) do count=count+1 end
        if count>=512 or not M.generic(generic,protected) or id~=M.genericId(generic) or not near(src,generic,generic) then return end
        d={id=id,model=generic.model,label='Objeto do mapa',p=generic.p,h=generic.h,s=generic.s,lo=generic.lo,hi=generic.hi,basis=generic.basis,generic=true,lod=120}
        definitions[id]=d; poses[id]=M.copy(d)
        TriggerClientEvent('cidade:objetos:definition',-1,d)
    end
    if locks[id] then tell(src,'Outro administrador esta movendo este objeto.'); return end
    if not near(src,d,poses[id]) then tell(src,'Aproxime-se mais do objeto.'); return end
    if GetPlayerRoutingBucket(src)~=0 then tell(src,'Use o editor na instancia principal da cidade.'); return end
    local token=('%d:%d:%d'):format(src,GetGameTimer(),math.random(100000,999999))
    locks[id]={owner=src,token=token,original=M.copy(poses[id]),seq=0,last=GetGameTimer()}
    sessions[src].id=id; broadcast(id)
    TriggerClientEvent('cidade:objetos:locked',src,id,token,poses[id])
end)
local function owned(src,id,token)
    if type(id)~='string' then return end
    local l=locks[id]
    if not l or l.owner~=src or l.token~=token then return end
    if not admin(src) or not sessions[src] or GetPlayerRoutingBucket(src)~=0 then release(id,true); return end
    return l
end
local function allowedPose(src,id,p)
    if not M.pose(p) then return false end
    local d=definitions[id]; local v=playerPosition(src)
    return v and M.distance(M.center(d,p),v)<=30 and M.surfaceDistance(d,p,v)<=8
end
RegisterNetEvent('cidade:objetos:update',function(id,token,seq,p)
    local src=source; local l=owned(src,id,token); if not l then return end
    if not M.finite(seq,100000000) or seq%1~=0 or seq<=l.seq or not rate(src,'move',70) or not allowedPose(src,id,p) then return end
    l.seq,l.last=seq,GetGameTimer(); poses[id]=M.copy(p); broadcast(id)
end)
RegisterNetEvent('cidade:objetos:finish',function(id,token,p,commit)
    local src=source; local l=owned(src,id,token); if not l then return end
    if commit~=true then release(id,true); tell(src,'Movimento cancelado; posicao anterior restaurada.'); return end
    if not allowedPose(src,id,p) then release(id,true); tell(src,'Posicao invalida; movimento cancelado.'); return end
    local nextDisk={version=1,positions={},generic={}}
    for k,v in pairs(disk.positions) do nextDisk.positions[k]=v end
    for k,v in pairs(disk.generic) do nextDisk.generic[k]=v end
    nextDisk.positions[id]=M.copy(p)
    if definitions[id].generic then nextDisk.generic[id]=definitions[id] end
    local ok,encoded=pcall(json.encode,nextDisk)
    if ok and lastDisk then ok=SaveResourceFile(resource,'objetos_posicoes.backup.json',lastDisk,-1) end
    if ok then ok=SaveResourceFile(resource,'objetos_posicoes.json',encoded,-1) end
    if not ok then release(id,true); tell(src,'Falha ao salvar no disco. A posicao anterior foi restaurada.'); print('[objetos] ERRO ao salvar objetos_posicoes.json'); return end
    disk,lastDisk=nextDisk,encoded; poses[id]=M.copy(p); release(id,false)
    tell(src,'Posicao salva e compartilhada com todos os jogadores.')
    print(('[objetos] Jogador %d salvou %s em %.3f %.3f %.3f (%.1f graus)'):format(src,id,p.p[1],p.p[2],p.p[3],p.h))
end)
RegisterCommand('restaurarobjeto',function(src)
    if not admin(src) or not sessions[src] then return end
    tell(src,'Selecione a peca com CAPS e pressione HOME para voltar a posicao original; CAPS confirma.')
end,false)
AddEventHandler('playerDropped',function() local src=source; cancelPlayer(src); sessions[src],limits[src]=nil,nil end)
CreateThread(function()
    while true do
        Wait(1000)
        local expired={}
        for id,l in pairs(locks) do
            if GetGameTimer()-l.last>6000 or not admin(l.owner) or GetPlayerPed(l.owner)==0 or GetEntityHealth(GetPlayerPed(l.owner))<=0 then expired[#expired+1]=id end
        end
        for _,id in ipairs(expired) do local src=locks[id].owner; release(id,true); tell(src,'Edicao interrompida; posicao anterior restaurada.') end
        for src in pairs(sessions) do if not admin(src) then cancelPlayer(src); sessions[src]=nil; TriggerClientEvent('cidade:objetos:mode',src,false) end end
    end
end)
