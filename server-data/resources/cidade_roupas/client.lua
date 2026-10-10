local previous, busy
local function notify(text)
    BeginTextCommandThefeedPost('STRING')
    AddTextComponentSubstringPlayerName(text)
    EndTextCommandThefeedPostTicker(false, false)
    print('[Roupas] ' .. text)
end
local function snapshot(ped)
    local state = { model = GetEntityModel(ped), components = {}, props = {} }
    for id = 0, 11 do
        state.components[id] = { GetPedDrawableVariation(ped,id), GetPedTextureVariation(ped,id), GetPedPaletteVariation(ped,id) }
    end
    for id = 0, 7 do
        state.props[id] = { GetPedPropIndex(ped,id), GetPedPropTextureIndex(ped,id) }
    end
    return state
end
local function allowed()
    local ped = PlayerPedId()
    if busy or LocalPlayer.state.wardrobeBusy or IsEntityDead(ped) or IsPedInAnyVehicle(ped,false) or LocalPlayer.state.labElevatorBusy then
        notify('Fique parado, fora do veiculo e do elevador para trocar de roupa.')
        return false
    end
    return true
end
local function switch(model)
    if GetEntityModel(PlayerPedId()) == (type(model)=='number' and model or joaat(model)) then return true end
    return exports.cidade_core:changeCharacter(model,true)
end
local function begin(model)
    if not allowed() then return false end
    busy = true
    local state = snapshot(PlayerPedId())
    if not switch(model) then busy = false; return false end
    if not previous then previous = state end
    return true
end
local function heistCollection(ped)
    for i=0,GetPedCollectionsCount(ped)-1 do
        local name=GetPedCollectionName(ped,i)
        -- Stock YMTs return "Male_Heist", while streamed filenames are lowercase.
        -- Compare normalized names, but pass the game's original name to natives.
        local normalized=type(name)=='string' and name:lower() or ''
        if normalized=='male_heist' or normalized=='mp_m_freemode_01_male_heist' then return name end
    end
end
local function whiteSuit()
    if not begin('mp_m_freemode_01') then return end
    local ped=PlayerPedId()
    local collection=heistCollection(ped)
    if not collection then
        busy=false
        ExecuteCommand('roupaanterior')
        notify('A colecao male_heist nao esta disponivel neste game build.')
        return
    end
    ClearAllPedProps(ped)
    -- Empty base undershirt/accessories; five streamed heist replacements.
    for _,item in ipairs({{2,0},{7,0},{8,15},{9,0},{10,0}}) do
        SetPedCollectionComponentVariation(ped,item[1],'',item[2],0,0)
    end
    for _,item in ipairs({{11,8},{4,7},{3,0},{6,0},{1,20}}) do
        SetPedCollectionComponentVariation(ped,item[1],collection,item[2],0,0)
    end
    busy=false
    notify('Macacao branco equipado. Use /roupaanterior para voltar.')
end
RegisterCommand('macacaobranco',whiteSuit,false)
RegisterCommand('trajelab',whiteSuit,false)
local function casualOutfit(withShirt,withAccessories)
    if not begin('mp_m_freemode_01') then return end
    local ped=PlayerPedId()
    local collection=heistCollection(ped)
    if not collection then
        busy=false
        ExecuteCommand('roupaanterior')
        notify('A colecao male_heist nao esta disponivel neste game build.')
        return
    end
    local bareFeet
    for i=0,GetPedCollectionsCount(ped)-1 do
        local name=GetPedCollectionName(ped,i)
        local normalized=type(name)=='string' and name:lower() or ''
        if normalized=='male_apt01' or normalized=='mp_m_freemode_01_male_apt01' then
            bareFeet=name
            break
        end
    end
    ClearAllPedProps(ped)
    -- Keep the existing Freemode face and hair; equip only the new trousers.
    for _,item in ipairs({{1,0},{3,15},{7,0},{8,15},{9,0},{10,0},{11,15}}) do
        SetPedCollectionComponentVariation(ped,item[1],'',item[2],0,0)
    end
    SetPedCollectionComponentVariation(ped,4,collection,8,0,0)
    -- Apartment collection 1 is the native bare foot, not an empty foot slot.
    SetPedCollectionComponentVariation(ped,6,bareFeet or '',bareFeet and 1 or 5,0,0)
    if withShirt then SetPedCollectionComponentVariation(ped,11,collection,9,0,0) end
    -- Apply empty neck/undershirt slots after the jacket's stock dependencies.
    for _,item in ipairs({{7,0},{8,15},{9,0},{10,0}}) do
        SetPedCollectionComponentVariation(ped,item[1],'',item[2],0,0)
    end
    if withAccessories then
        SetPedCollectionComponentVariation(ped,6,collection,1,0,0)
        -- The separate wrist mesh is skinned to the left forearm.
        SetPedCollectionComponentVariation(ped,7,collection,1,0,0)
    end
    busy=false
    notify(withAccessories and 'Conjunto completo equipado. Use /roupaanterior para voltar.' or (withShirt and 'Camisa estampada e calca bege equipadas. Use /roupaanterior para voltar.' or 'Calca bege equipada, sem camisa. Use /roupaanterior para voltar.'))
end
RegisterCommand('calcabege',function() casualOutfit(false) end,false)
RegisterCommand('camisaestampada',function() casualOutfit(true) end,false)
RegisterCommand('conjuntocompleto',function() casualOutfit(true,true) end,false)
RegisterCommand('crachadea',function()
    if not begin('mp_m_freemode_01') then return end
    local ped=PlayerPedId()
    local collection=heistCollection(ped)
    if not collection or not IsPedCollectionComponentVariationValid(ped,9,collection,0,0) then
        busy=false
        ExecuteCommand('roupaanterior')
        notify('O slot de teste do cracha DEA nao esta disponivel neste game build.')
        return
    end
    SetPedCollectionComponentVariation(ped,9,collection,0,0,0)
    busy=false
    notify('Cracha DEA equipado. Use /roupaanterior para voltar.')
end,false)
RegisterCommand('calcatatica',function()
    if not begin('mp_m_freemode_01') then return end
    local ped=PlayerPedId()
    local collection=heistCollection(ped)
    if not collection or not IsPedCollectionComponentVariationValid(ped,4,collection,6,0) then
        busy=false
        ExecuteCommand('roupaanterior')
        notify('O slot de teste da calca tatica nao esta disponivel neste game build.')
        return
    end
    SetPedCollectionComponentVariation(ped,4,collection,6,0,0)
    busy=false
    notify('Calca tatica equipada. Use /roupaanterior para voltar.')
end,false)
RegisterCommand('guardavermelho',function()
    if not begin('guardalab') then return end
    local ped=PlayerPedId()
    for _,component in ipairs({0,2,3,4,11}) do SetPedComponentVariation(ped,component,0,0,0) end
    busy=false
    notify('Traje de guarda equipado. Use /roupaanterior para voltar.')
end,false)
RegisterCommand('person2',function()
    if not begin('person2') then return end
    local ped=PlayerPedId()
    ClearAllPedProps(ped)
    for _,component in ipairs({0,2,3,4,11}) do SetPedComponentVariation(ped,component,0,0,0) end
    busy=false
    notify('Personagem person2 equipado. Use /roupaanterior para voltar.')
end,false)
RegisterCommand('roupaanterior',function()
    if not previous or not allowed() then return end
    busy=true
    if not switch(previous.model) then busy=false;return end
    local ped=PlayerPedId()
    for id,item in pairs(previous.components) do SetPedComponentVariation(ped,id,item[1],item[2],item[3]) end
    ClearAllPedProps(ped)
    for id,item in pairs(previous.props) do
        if item[1]>=0 then SetPedPropIndex(ped,id,item[1],item[2],true) end
    end
    previous=nil;busy=false
    notify('Roupa anterior restaurada.')
end,false)
