-- Independent jeans collection. Changes component 4 only.
local collection = '__COLLECTION__'
local model = joaat('mp_m_freemode_01')
local previous = nil
local function message(text) print('[Calca exclusiva] '..text) end
local function capture(ped)
    local result = {ped=ped, model=GetEntityModel(ped), components={}}
    for _,slot in ipairs({4}) do
        result.components[slot] = {
            drawable=GetPedDrawableVariation(ped,slot),
            texture=GetPedTextureVariation(ped,slot),
            palette=GetPedPaletteVariation(ped,slot)
        }
    end
    return result
end
local function restore()
    local ped = PlayerPedId()
    if not previous or previous.ped~=ped or previous.model~=GetEntityModel(ped) then
        previous=nil; message('Nenhuma calca anterior salva para este personagem.'); return
    end
    for _,slot in ipairs({4}) do
        local item=previous.components[slot]
        SetPedComponentVariation(ped,slot,item.drawable,item.texture,item.palette)
    end
    previous=nil; message('Calca anterior restaurada.')
end
RegisterCommand('calcajeans',function()
    local ped=PlayerPedId()
    if GetEntityModel(ped)~=model then
        message('Selecione o personagem masculino freemode para testar esta peca.'); return
    end
    local actual=nil
    for i=0,GetPedCollectionsCount(ped)-1 do
        local name=GetPedCollectionName(ped,i)
        if name and name:lower()==collection:lower() then actual=name; break end
    end
    if not actual or not IsPedCollectionComponentVariationValid(ped,4,actual,0,0) then
        message('Colecao nao carregada. Ative cidade_jeans_washed no servidor e reconecte ao jogo.'); return
    end
    if not previous or previous.ped~=ped or previous.model~=model then previous=capture(ped) end
    SetPedCollectionComponentVariation(ped,4,actual,0,0,0)
    message('Calca exclusiva aplicada. jeansanterior restaura a calca anterior.')
end,false)
RegisterCommand('jeansanterior',restore,false)
AddEventHandler('onResourceStop',function(resource)
    if resource~=GetCurrentResourceName() or not previous then return end
    local ped=PlayerPedId()
    local name=GetPedCollectionNameFromDrawable(ped,4,GetPedDrawableVariation(ped,4))
    if name and name:lower()==collection:lower() then restore() end
end)
