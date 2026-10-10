-- Persistent island edits: verified ADM only; viewers receive the saved world.
local resource=GetCurrentResourceName()
local cfg=json.decode(LoadResourceFile(resource,'ui/cayo.json') or '{}')
local models={};for _,row in ipairs(cfg.objects or {}) do models[row.model]=row end
local catalogFile,catalogIndexFile
local function sendCapturedCatalog(id)
    -- Reuse the JSON read from disk instead of packing every thumbnail table
    -- again on the server thread whenever a capture finishes.
    if catalogFile then TriggerLatentClientEvent('cidade_admin:capturedCatalog',id,1000000,catalogIndexFile,catalogFile)end
end
local function readCapturedCatalog(broadcast)
    local raw=LoadResourceFile(resource,'data/catalogo_capturado_indice.json') or LoadResourceFile(resource,'data/catalogo_capturado.json')
    if not raw or raw==catalogIndexFile then return end
    local ok,data=pcall(json.decode,raw)
    if not ok or type(data)~='table' or type(data.objects)~='table' then print('[Editor Ilha] Catálogo capturado inválido; mantendo a última versão.');return end
    for _,row in ipairs(data.objects)do
        if type(row.model)~='string' or not row.model:match('^[%w_]+$') or type(row.hash)~='number'
            or row.hash%1~=0 or row.hash<1 or row.hash>4294967295 or type(row.bbMin)~='table' or type(row.bbMax)~='table' then return end
    end
    catalogFile=LoadResourceFile(resource,'data/catalogo_capturado.json') or raw
    catalogIndexFile=raw;CidadeCapturedCatalog.merge(data)
    for _,row in ipairs(data.objects)do models[row.model]=row end
    if broadcast and GetNumPlayerIndices()>0 then sendCapturedCatalog(-1)end
    print(('[Editor Ilha] Catálogo compartilhado: %d modelos, revisão %d.'):format(#data.objects,data.revision))
end
readCapturedCatalog(false)
CreateThread(function()while true do Wait(5000);readCapturedCatalog(true)end end)
local store={revision=0,nextId=1,objects={}}
local clocks={}
local function finite(v)return type(v)=='number' and v==v and math.abs(v)<math.huge end
local function integer(v)return finite(v) and v%1==0 end
local function authorized(id)
    return id and id>0 and GetResourceState('cidade_acesso')=='started'
        and IsPlayerAceAllowed(id,'cidade.admin') and exports.cidade_acesso:GetVerifiedRecord(id)
end
local function valid(row)
    if type(row)~='table' or not models[row.model] then return false end
    local b=cfg.bounds
    for _,region in ipairs(cfg.editRegions or {})do
        if finite(row.x)and finite(row.y)and row.x>=region.minX and row.x<=region.maxX and row.y>=region.minY and row.y<=region.maxY then b=region;break end
    end
    return finite(row.x) and row.x>=b.minX and row.x<=b.maxX
        and finite(row.y) and row.y>=b.minY and row.y<=b.maxY
        and finite(row.z) and row.z>=b.minZ and row.z<=b.maxZ
        and finite(row.heading) and row.heading>=0 and row.heading<360
        and finite(row.pitch or 0) and math.abs(row.pitch or 0)<=180
        and finite(row.roll or 0) and math.abs(row.roll or 0)<=180
        and finite(row.scale) and row.scale>=.25 and row.scale<=3
end
local file=LoadResourceFile(resource,'data/island_placements.json')
if file then
    local ok,data=pcall(json.decode,file)
    if not ok or type(data)~='table' or not integer(data.revision) or type(data.objects)~='table' then
        error('[Editor Ilha] Arquivo de colocações inválido; restaure data/island_placements.backup.json.')
    end
    local ids={};store.revision=data.revision
    for _,row in ipairs(data.objects) do
        if not valid(row) or not integer(row.id) or row.id<1 or ids[row.id] then error('[Editor Ilha] Colocação inválida no arquivo salvo.') end
        ids[row.id]=true;store.objects[#store.objects+1]=row;store.nextId=math.max(store.nextId,row.id+1)
    end
end
local function snapshot()return {revision=store.revision,objects=store.objects,maxPlacements=cfg.maxPlacements} end
local function save(nextStore)
    local text=json.encode(nextStore)
    local previous=LoadResourceFile(resource,'data/island_placements.json')
    if previous and not SaveResourceFile(resource,'data/island_placements.backup.json',previous,-1) then return false end
    if not SaveResourceFile(resource,'data/island_placements.json',text,-1) then return false end
    store=nextStore;TriggerClientEvent('cidade_admin:islandWorld',-1,snapshot());return true
end
local function respond(id,nonce,ok,message,data)
    TriggerClientEvent('cidade_admin:islandReply',id,nonce,{ok=ok,message=message,data=data})
end
RegisterNetEvent('cidade_admin:islandSync',function()
    local id=tonumber(source);if not id or id<1 then return end
    local now=GetGameTimer();local key='sync:'..id
    if clocks[key] and now-clocks[key]<1000 then return end
    clocks[key]=now;TriggerClientEvent('cidade_admin:islandWorld',id,snapshot())
    sendCapturedCatalog(id)
end)
RegisterNetEvent('cidade_admin:islandRequest',function(nonce,request)
    local id=tonumber(source)
    if not integer(nonce) or nonce<1 or nonce>2147483647 or type(request)~='table' then return end
    local record=authorized(id)
    if not record then respond(id,nonce,false,'Seu acesso ADM não está autorizado.');return end
    if GetPlayerRoutingBucket(id)~=0 then respond(id,nonce,false,'Edite a ilha na instância principal.');return end
    local action=request.action;local allowed={list=true,begin=true,save=true,delete=true,undo=true}
    if not allowed[action] then respond(id,nonce,false,'Ação inválida.');return end
    local now=GetGameTimer();local key=action..':'..id
    if clocks[key] and now-clocks[key]<300 then respond(id,nonce,false,'Aguarde um instante.');return end
    clocks[key]=now
    readCapturedCatalog(false)
    if action=='list' then sendCapturedCatalog(id)end
    if action=='list' then respond(id,nonce,true,'',snapshot());return end
    if action=='begin' then
        if not models[request.model] then respond(id,nonce,false,'Objeto fora do catálogo da ilha.');return end
        if request.id then
            local found=false
            for _,row in ipairs(store.objects) do if row.id==request.id and row.model==request.model then found=true end end
            if not found then respond(id,nonce,false,'Esse objeto não existe mais. Atualize a lista.');return end
        end
        respond(id,nonce,true,'Posicione a prévia e pressione Enter para salvar.',{revision=store.revision});return
    end
    if request.revision~=store.revision then respond(id,nonce,false,'A ilha foi editada por outro ADM. Atualize a lista.',snapshot());return end
    local nextStore={revision=store.revision+1,nextId=store.nextId,objects={}}
    for _,row in ipairs(store.objects) do nextStore.objects[#nextStore.objects+1]=row end
    local removed=0
    if action=='save' then
        if type(request.rows)~='table' or #request.rows<1 or #request.rows>32 then respond(id,nonce,false,'Aplique entre 1 e 32 objetos por vez.');return end
        if request.id then
            if #request.rows~=1 then respond(id,nonce,false,'Edite um objeto por vez.');return end
            for i,row in ipairs(nextStore.objects) do if row.id==request.id then table.remove(nextStore.objects,i);removed=1;break end end
            if removed~=1 then respond(id,nonce,false,'Objeto não encontrado.');return end
        end
        if #nextStore.objects+#request.rows>cfg.maxPlacements then respond(id,nonce,false,'Limite de colocações atingido.');return end
        local batch=('%d:%d:%d'):format(record.id,store.revision+1,os.time())
        for _,row in ipairs(request.rows) do
            if not valid(row) then respond(id,nonce,false,'Modelo, escala ou posição fora dos limites da ilha.');return end
            local item={id=request.id or nextStore.nextId,model=row.model,x=row.x,y=row.y,z=row.z,heading=row.heading,pitch=row.pitch or 0,roll=row.roll or 0,scale=row.scale,author=record.id,batch=batch}
            if not request.id then nextStore.nextId=nextStore.nextId+1 end
            nextStore.objects[#nextStore.objects+1]=item
        end
    elseif action=='delete' then
        for i,row in ipairs(nextStore.objects) do if row.id==request.id then table.remove(nextStore.objects,i);removed=1;break end end
        if removed==0 then respond(id,nonce,false,'Objeto não encontrado.');return end
    else
        local batch
        for i=#nextStore.objects,1,-1 do if nextStore.objects[i].author==record.id then batch=nextStore.objects[i].batch;break end end
        if not batch then respond(id,nonce,false,'Nenhuma aplicação sua para desfazer.');return end
        for i=#nextStore.objects,1,-1 do local row=nextStore.objects[i];if row.author==record.id and row.batch==batch then table.remove(nextStore.objects,i);removed=removed+1 end end
    end
    if not save(nextStore) then respond(id,nonce,false,'Não foi possível salvar no disco. A colocação não foi aplicada.');return end
    print(('[Editor Ilha] ADM=%d ação=%s revisão=%d objetos=%d'):format(record.id,action,store.revision,#store.objects))
    respond(id,nonce,true,action=='save' and 'Aplicação salva para todos os jogadores.' or 'Aplicação removida e salva.',snapshot())
end)
AddEventHandler('playerDropped',function()
    local suffix=':'..tostring(source)
    for key in pairs(clocks) do if key:sub(-#suffix)==suffix then clocks[key]=nil end end
end)
