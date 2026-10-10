local resource = GetCurrentResourceName()
local catalog = json.decode(LoadResourceFile(resource, 'catalog.json') or '{"items":[]}')
local exclusives = json.decode(LoadResourceFile(resource, 'exclusives.json') or '{"items":[]}')
local items = {}
for _, item in ipairs(catalog.items) do items[item.id] = item end
for _, item in ipairs(exclusives.items) do
    if item.exclusive == true and not items[item.id] then
        catalog.items[#catalog.items+1] = item
        items[item.id] = item
    end
end
local tattooCatalog = json.decode(LoadResourceFile(resource, 'tattoos.json') or '{"items":[]}')
local hairCatalog = json.decode(LoadResourceFile(resource, 'hair.json') or '{"items":[]}')
local lastRequest = {}
local tagBusy = {}
local viewers = {}
local lastTags = LoadResourceFile(resource, 'tags.json') or '{"items":{}}'

local function snapshot()
    local raw = LoadResourceFile(resource, 'tags.json') or '{"items":{}}'
    local ok, saved = pcall(json.decode, raw)
    local tags = ok and type(saved) == 'table' and type(saved.items) == 'table' and saved.items or {}
    local result, counts = {}, {total=0, male=0, female=0, exclusive=0}
    for _, item in ipairs(catalog.items) do
        local visible = item.exclusive == true
        for _, tag in ipairs(tags[item.id] or {}) do
            if tag == 'OK' then visible = true; break end
        end
        if visible then
            result[#result+1] = item
            counts.total = counts.total+1
            counts[item.sex] = counts[item.sex]+1
            if item.exclusive == true then counts.exclusive = counts.exclusive+1 end
        end
    end
    return {items=result, counts=counts, tags=tags, raw=raw}
end

local function sendItems(player, token, data, includeAppearance)
    TriggerClientEvent('cidade_acervo:items', player, token, data.items, data.counts,
        includeAppearance and {tattoos=tattooCatalog.items, hair=hairCatalog.items} or nil, data.tags)
end

local function syncViewers()
    if not next(viewers) then return end
    local data = snapshot()
    if data.raw == lastTags then return end
    lastTags = data.raw
    for player, token in pairs(viewers) do sendItems(player, token, data, false) end
end

RegisterNetEvent('cidade_acervo:request', function(token)
    local player = source
    local now = GetGameTimer()
    if lastRequest[player] and now - lastRequest[player] < 500 then return end
    lastRequest[player] = now
    viewers[player] = token
    sendItems(player, token, snapshot(), true)
end)
RegisterNetEvent('cidade_acervo:closed', function(token)
    if viewers[source] == token then viewers[source] = nil; lastRequest[source] = nil end
end)
CreateThread(function()
    while true do Wait(2000); syncViewers() end
end)
RegisterNetEvent('cidade_acervo:tags',function(token,request,id,tags)
    local player=source
    local function reply(result) TriggerClientEvent('cidade_acervo:tagsSaved',player,token,request,id,result) end
    if not items[id] or type(tags)~='table' or #tags>3 or tagBusy[player] then reply({ok=false,error='Seleção de tags inválida ou gravação em andamento.'}); return end
    local allowed={['OK']=true,['PEÇA INCORRETA']=true,['DEFEITO NA TEXTURA']=true}
    for _,tag in pairs(tags) do if not allowed[tag] then reply({ok=false,error='Tag inválida.'}); return end end
    tagBusy[player]=true
    -- The web bridge is the single writer; saves from game and browser cannot overwrite each other.
    PerformHttpRequest('http://127.0.0.1:8766/api/tags',function(status,body)
        tagBusy[player]=nil
        local ok,result=pcall(json.decode,body or '')
        if status==200 and ok and result.ok then reply(result); syncViewers()
        else reply({ok=false,error='Não foi possível salvar as tags. Confira se o app Acervo está iniciado.'}) end
    end,'POST','{"id":'..json.encode(id)..',"tags":'..(#tags==0 and '[]' or json.encode(tags))..'}',{['Content-Type']='application/json'})
end)
AddEventHandler('playerDropped', function() lastRequest[source]=nil; tagBusy[source]=nil; viewers[source]=nil end)
