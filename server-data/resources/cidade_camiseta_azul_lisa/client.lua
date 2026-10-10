-- Independent collection. Only the shirt and its compatible arms/undershirt change.
local collection = 'cidade_camiseta_azul_lisa_r001'
local model = joaat('mp_m_freemode_01')
local previous = nil
local function message(text) print('[Camiseta exclusiva] '..text) end
local function capture(ped)
    local result = {ped=ped, model=GetEntityModel(ped), components={}}
    for _,slot in ipairs({3,8,11}) do
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
        previous=nil; message('Nenhuma camiseta anterior salva para este personagem.'); return
    end
    for _,slot in ipairs({3,8,11}) do
        local item=previous.components[slot]
        SetPedComponentVariation(ped,slot,item.drawable,item.texture,item.palette)
    end
    previous=nil; message('Camiseta, braços e peça interna anteriores restaurados.')
end
RegisterCommand('provar_camiseta_azul_lisa',function()
    local ped=PlayerPedId()
    if GetEntityModel(ped)~=model then
        message('Selecione o personagem masculino freemode para testar esta peça.'); return
    end
    local actual=nil
    for i=0,GetPedCollectionsCount(ped)-1 do
        local name=GetPedCollectionName(ped,i)
        if name and name:lower()==collection:lower() then actual=name; break end
    end
    if not actual or not IsPedCollectionComponentVariationValid(ped,11,actual,0,0) then
        message('Coleção não carregada. Ative cidade_camiseta_azul_lisa no servidor e reconecte ao jogo.'); return
    end
    if not IsPedCollectionComponentVariationValid(ped,3,'',0,0)
        or not IsPedCollectionComponentVariationValid(ped,8,'',15,0) then
        message('Braços ou peça interna incompatíveis com este build.'); return
    end
    if not previous or previous.ped~=ped or previous.model~=model then previous=capture(ped) end
    SetPedCollectionComponentVariation(ped,3,'',0,0,0)
    SetPedCollectionComponentVariation(ped,8,'',15,0,0)
    SetPedCollectionComponentVariation(ped,11,actual,0,0,0)
    message('Camiseta exclusiva aplicada. restaurar_camiseta_azul_lisa restaura a peça anterior.')
end,false)
RegisterCommand('restaurar_camiseta_azul_lisa',restore,false)
AddEventHandler('onResourceStop',function(resource)
    if resource~=GetCurrentResourceName() or not previous then return end
    local ped=PlayerPedId()
    local name=GetPedCollectionNameFromDrawable(ped,11,GetPedDrawableVariation(ped,11))
    if name and name:lower()==collection:lower() then restore() end
end)
