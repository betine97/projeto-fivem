local opened, working = false, false
local preview, camera, original, wasFrozen
local sex, origin, heading, session = 'male', nil, 0.0, 0
local available, chosen, baseline = {}, {}, nil
local appearance, appearanceOptions, tattooById = {}, {}, {}
local tattooSource, hairSource = {}, {}
local components = {berd=1, hand=5, accs=7, teef=8, task=9, jbib=11, lowr=4, feet=6}
local props = {p_head=0, p_eyes=1, p_ears=2, p_lwrist=6, p_rwrist=7}
local views = {full=true, head=true, torso=true, legs=true}
local view = 'full'
local rotation, headIdentity = 0, nil
local tags, pendingTags, tagRequest = {}, {}, 0
local topUsesCompatibleArms = false

local function message(text)
    print('[Acervo] '..text)
    BeginTextCommandThefeedPost('STRING')
    AddTextComponentSubstringPlayerName(text)
    EndTextCommandThefeedPostTicker(false, false)
end
local function close()
    if opened then TriggerServerEvent('cidade_acervo:closed', session) end
    for key, callback in pairs(pendingTags) do callback({ok=false,error='O tablet foi fechado.'}); pendingTags[key]=nil end
    session = session + 1
    opened, working = false, false
    SetNuiFocus(false, false)
    SendNUIMessage({type='close'})
    if camera then
        RenderScriptCams(false, false, 0, true, true)
        DestroyCam(camera, false)
        camera = nil
    end
    if preview and DoesEntityExist(preview) then DeleteEntity(preview) end
    preview = nil
    if original and DoesEntityExist(original) then FreezeEntityPosition(original, wasFrozen or false) end
    original = nil
    LocalPlayer.state:set('wardrobeBusy', false, false)
end
local function blocked()
    local ped = PlayerPedId()
    return IsEntityDead(ped) or IsPedInAnyVehicle(ped, false) or LocalPlayer.state.labElevatorBusy
        or IsPauseMenuActive() or (GetResourceState('fpv_drone_runtime')=='started' and exports.fpv_drone_runtime:isPiloting())
end
local function normalize(name)
    name = (name or ''):lower()
    if name:match('^mp_[mf]_freemode_01_p$') or name:match('^mp_[mf]_freemode_01$') then return '' end
    return name:gsub('^mp_[mf]_freemode_01_p_', ''):gsub('^mp_[mf]_freemode_01_', '')
end
local function collectionFor(ped, name)
    local target = normalize(name)
    if target=='' then return '' end
    for i=0,GetPedCollectionsCount(ped)-1 do
        local actual = GetPedCollectionName(ped, i)
        if normalize(actual)==target then return actual end
    end
end
local function positionCamera()
    if not preview or not camera then return end
    local head = GetPedBoneCoords(preview, 31086, 0.0, 0.0, 0.20)
    local left = GetPedBoneCoords(preview, 14201, 0.0, 0.0, -0.12)
    local right = GetPedBoneCoords(preview, 52301, 0.0, 0.0, -0.12)
    local bottom, top = math.min(left.z, right.z), head.z
    local height, centerZ = math.max(top-bottom, 1.8), (top+bottom)/2
    if view=='head' then height, centerZ = 0.72, head.z-0.25
    elseif view=='torso' then height, centerZ = 1.25, top-0.75
    elseif view=='legs' then height, centerZ = 1.25, bottom+0.55 end
    local fov = 40.0
    local distance = height/(2*math.tan(math.rad(fov/2))*0.70)
    local shift = distance*math.tan(math.rad(fov/2))*GetAspectRatio(false)*0.48
    -- Keep the camera fixed when rotating the character.
    local radians = math.rad(heading)
    local p = {x=origin.x-math.sin(radians)*distance, y=origin.y+math.cos(radians)*distance}
    local target = {x=origin.x+math.cos(radians)*shift, y=origin.y+math.sin(radians)*shift}
    SetCamCoord(camera, p.x, p.y, centerZ)
    PointCamAtCoord(camera, target.x, target.y, centerZ)
    SetCamFov(camera, fov)
end
local function capture(ped)
    local saved = {components={}, props={}}
    for id=0,11 do saved.components[id]={GetPedDrawableVariation(ped,id),GetPedTextureVariation(ped,id),GetPedPaletteVariation(ped,id)} end
    for id=0,7 do saved.props[id]={GetPedPropIndex(ped,id),GetPedPropTextureIndex(ped,id)} end
    return saved
end
local function restore(ped, saved)
    for id,item in pairs(saved.components) do SetPedComponentVariation(ped,id,item[1],item[2],item[3]) end
    ClearAllPedProps(ped)
    for id,item in pairs(saved.props) do if item[1]>=0 then SetPedPropIndex(ped,id,item[1],item[2],true) end end
end
local function restoreSlot(category)
    local armsChanged = category=='jbib' and topUsesCompatibleArms
    if armsChanged then
        local arms = baseline.components[3]
        SetPedComponentVariation(preview,3,arms[1],arms[2],arms[3])
        topUsesCompatibleArms = false
    end
    local slot = components[category]
    if slot then
        local item = baseline.components[slot]
        SetPedComponentVariation(preview,slot,item[1],item[2],item[3])
    else
        slot = props[category]
        local item = baseline.props[slot]
        if item[1]<0 then ClearPedProp(preview,slot) else SetPedPropIndex(preview,slot,item[1],item[2],true) end
    end
    chosen[category] = nil
    return armsChanged
end
local function preserveOtherSlots(saved, componentSlot, propSlot, armsChanged)
    -- Preserve other pieces even if a native drawable has forced dependencies.
    for id,item in pairs(saved.components) do
        if id~=componentSlot and not (id==3 and armsChanged) and (GetPedDrawableVariation(preview,id)~=item[1] or GetPedTextureVariation(preview,id)~=item[2] or GetPedPaletteVariation(preview,id)~=item[3]) then
            SetPedComponentVariation(preview,id,item[1],item[2],item[3])
        end
    end
    for id,item in pairs(saved.props) do
        if id~=propSlot and (GetPedPropIndex(preview,id)~=item[1] or GetPedPropTextureIndex(preview,id)~=item[2]) then
            if item[1]<0 then ClearPedProp(preview,id) else SetPedPropIndex(preview,id,item[1],item[2],true) end
        end
    end
end
local function blankAppearance()
    return {hair=0, hairColor=0, beard=255, beardColor=0, tattoos={}}
end
local function readHeadIdentity(ped)
    -- GTA writes ten fields at eight-byte intervals. Never pass a scalar pointer.
    local buffer = string.rep('\0', 80)
    local valid = Citizen.InvokeNative(0x2746BD9D88C5C5D0, ped, buffer, Citizen.ReturnResultAnyway())
    if not valid or valid==0 then return nil end
    local identity = {parents={}, mixes={}, features={}, eyes=GetPedEyeColor(ped)}
    for i=0,5 do
        local value = string.unpack('<i4',buffer,1+i*8)
        if value<0 or value>255 then return nil end
        identity.parents[i+1]=value
    end
    for i=0,2 do
        local value = string.unpack('<f',buffer,49+i*8)
        if value~=value or value<0 or value>1 then return nil end
        identity.mixes[i+1]=value
    end
    for i=0,19 do identity.features[i]=GetPedFaceFeature(ped,i) end
    return identity
end
local function initializeHead(ped, identity, token)
    local p,m = identity.parents,identity.mixes
    SetPedHeadBlendData(ped,p[1],p[2],p[3],p[4],p[5],p[6],m[1],m[2],m[3],false)
    local deadline = GetGameTimer()+5000
    while not HasPedHeadBlendFinished(ped) and opened and session==token and GetGameTimer()<deadline do Wait(10) end
    if not opened or session~=token or not HasPedHeadBlendFinished(ped) then return false end
    for index,value in pairs(identity.features) do SetPedFaceFeature(ped,index,value) end
    if identity.eyes>=0 then SetPedEyeColor(ped,identity.eyes) end
    return true
end
local function applyAppearance(ped)
    ClearPedDecorations(ped)
    for id in pairs(appearance.tattoos) do
        local tattoo = tattooById[id]
        if tattoo then AddPedDecorationFromHashes(ped,joaat(tattoo.collection),joaat(tattoo.overlay)) end
    end
    SetPedComponentVariation(ped,2,appearance.hair,0,0)
    SetPedHairTint(ped,appearance.hairColor,appearance.hairColor)
    SetPedHeadOverlay(ped,1,appearance.beard,appearance.beard==255 and 0.0 or 1.0)
    SetPedHeadOverlayColor(ped,1,1,appearance.beardColor,appearance.beardColor)
    SetPedHeadOverlay(ped,10,255,0.0)
end
local function underwear(ped, nextSex)
    ClearAllPedProps(ped)
    for _,item in ipairs({{1,0},{2,0},{3,15},{5,0},{7,0},{8,15},{9,0},{10,0},{11,15}}) do
        SetPedCollectionComponentVariation(ped,item[1],'',item[2],0,0)
    end
    local lower = nextSex=='male' and collectionFor(ped,'mp_m_valentines_02') or ''
    local lowerIndex = nextSex=='male' and 1 or 15
    if lower==nil or not IsPedCollectionComponentVariationValid(ped,4,lower,lowerIndex,0) then return false end
    SetPedCollectionComponentVariation(ped,4,lower,lowerIndex,0,0)
    local bareFeet = collectionFor(ped,nextSex=='male' and 'male_apt01' or 'female_apt01')
    if bareFeet==nil or not IsPedCollectionComponentVariationValid(ped,6,bareFeet,1,0) then return false end
    SetPedCollectionComponentVariation(ped,6,bareFeet,1,0,0)
    SetPedHeadOverlay(ped,1,255,0.0)
    SetPedHeadOverlay(ped,10,255,0.0)
    ClearPedDecorations(ped)
    return true
end
local function rebuildAppearanceOptions()
    local hairImages = {}
    for _,item in ipairs(hairSource) do
        if item.sex==sex then hairImages[normalize(item.collection)..':'..item.index]=item.image end
    end
    local hairs, colors, tattoos = {}, {}, {}
    for index=0,GetNumberOfPedDrawableVariations(preview,2)-1 do
        local collection = GetPedCollectionNameFromDrawable(preview,2,index)
        local localIndex = GetPedCollectionLocalIndexFromDrawable(preview,2,index)
        hairs[#hairs+1]={index=index,title=index==0 and 'Sem cabelo' or ('Cabelo '..index),image=hairImages[normalize(collection)..':'..localIndex]}
    end
    for index=0,GetNumHairColors()-1 do
        local r,g,b = GetPedHairRgbColor(index)
        colors[#colors+1]={index=index,r=r,g=g,b=b}
    end
    tattooById = {}
    for _,item in ipairs(tattooSource) do
        local zone = GetPedDecorationZoneFromHashes(joaat(item.collection),joaat(item.overlay))
        if item.sex==sex and zone>=0 and zone<7 then
            local title = item.label and item.label~='' and GetLabelText(item.label) or ''
            if title=='' or title=='NULL' then title=item.overlay end
            local tattoo={id=item.id,collection=item.collection,overlay=item.overlay,zone=item.zone,title=title}
            tattoos[#tattoos+1]=tattoo
            tattooById[item.id]=tattoo
        end
    end
    appearanceOptions = {hair=hairs,colors=colors,beardCount=GetPedHeadOverlayNum(1),tattoos=tattoos}
end
local function state(includeOptions)
    local result = {ok=true, sex=sex, chosen=chosen, appearance=appearance, view=view,rotation=rotation}
    if includeOptions then result.options=appearanceOptions end
    return result
end
local function makePreview(nextSex)
    local token = session
    local model = joaat(nextSex=='female' and 'mp_f_freemode_01' or 'mp_m_freemode_01')
    RequestModel(model)
    local deadline = GetGameTimer()+10000
    while not HasModelLoaded(model) and GetGameTimer()<deadline and opened and session==token do Wait(20) end
    if not opened or session~=token or not HasModelLoaded(model) then SetModelAsNoLongerNeeded(model); return false end
    local nextPed
    if GetEntityModel(original)==model then nextPed=ClonePed(original,heading,false,false)
    else nextPed=CreatePed(nextSex=='female' and 5 or 4,model,origin.x,origin.y,origin.z,heading,false,false) end
    SetModelAsNoLongerNeeded(model)
    if not nextPed or nextPed==0 then return false end
    if GetEntityModel(nextPed)~=model then DeleteEntity(nextPed); return false end
    local identity = GetEntityModel(original)==model and readHeadIdentity(original) or nil
    if not identity then
        local parent = nextSex=='female' and 21 or 0
        identity={parents={parent,parent,0,parent,parent,0},mixes={0.5,0.5,0.0},features={},eyes=0}
    end
    if GetEntityModel(original)~=model then SetPedDefaultComponentVariation(nextPed) end
    if not initializeHead(nextPed,identity,token) then DeleteEntity(nextPed); return false end
    if not underwear(nextPed,nextSex) then DeleteEntity(nextPed); return false end
    if preview and DoesEntityExist(preview) then DeleteEntity(preview) end
    preview, sex, chosen, appearance, view = nextPed, nextSex, {}, blankAppearance(), 'full'
    topUsesCompatibleArms = false
    rotation,headIdentity = 0,identity
    SetEntityAsMissionEntity(preview,true,true)
    SetEntityVisible(preview,true,false)
    ResetEntityAlpha(preview)
    SetEntityCoordsNoOffset(preview,origin.x,origin.y,origin.z,false,false,false)
    SetEntityCollision(preview,false,false)
    FreezeEntityPosition(preview,true)
    SetEntityInvincible(preview,true)
    SetBlockingOfNonTemporaryEvents(preview,true)
    ClearPedTasksImmediately(preview)
    SetCurrentPedWeapon(preview,joaat('WEAPON_UNARMED'),true)
    Wait(0)
    if not opened or session~=token then return false end
    baseline = capture(preview)
    applyAppearance(preview)
    rebuildAppearanceOptions()
    positionCamera()
    return true
end
local function applyPiece(item)
    local collection = collectionFor(preview,item.collection)
    if collection==nil then return false,'Esta coleção não está disponível no build da cidade.' end
    local texture, slot, prop = item.textureIndex or 0, components[item.category], props[item.category]
    if slot then
        if not IsPedCollectionComponentVariationValid(preview,slot,collection,item.index,texture) then return false,'Esta peça ou textura não está disponível no build da cidade.' end
    elseif prop==nil or item.index>=GetNumberOfPedCollectionPropDrawableVariations(preview,prop,collection)
        or texture>=GetNumberOfPedCollectionPropTextureVariations(preview,prop,collection,item.index) then
        return false,'Este acessório não está disponível no build da cidade.'
    end
    -- This native T-shirt needs its matching short-sleeve arms, while all
    -- separately chosen clothes, undershirts, props and appearance stay intact.
    local compatibleArms = item.exclusive==true and item.category=='jbib' and item.compatibleArmsIndex
    if compatibleArms and not IsPedCollectionComponentVariationValid(preview,3,'',compatibleArms,0) then
        return false,'Os braços compatíveis desta camiseta não estão disponíveis.'
    end
    local saved = capture(preview)
    local armsChanged = item.category=='jbib' and (topUsesCompatibleArms or compatibleArms~=nil and compatibleArms~=false)
    if slot then SetPedCollectionComponentVariation(preview,slot,collection,item.index,texture,0)
    else SetPedCollectionPropIndex(preview,prop,collection,item.index,texture,true) end
    if item.category=='jbib' then
        if compatibleArms then SetPedCollectionComponentVariation(preview,3,'',compatibleArms,0,0)
        elseif topUsesCompatibleArms then
            local arms = baseline.components[3]
            SetPedComponentVariation(preview,3,arms[1],arms[2],arms[3])
        end
        topUsesCompatibleArms = compatibleArms~=nil and compatibleArms~=false
    end
    preserveOtherSlots(saved,slot,prop,armsChanged)
    chosen[item.category] = item.id
    return true
end
RegisterCommand('roupas',function()
    if opened then close(); return end
    if blocked() or IsNuiFocused() then message('Fique de pé, fora do veículo e feche os outros menus.'); return end
    TriggerEvent('cidade:stopProne'); TriggerEvent('cidade:preparePilot')
    original = PlayerPedId()
    origin, heading = GetEntityCoords(original),GetEntityHeading(original)
    wasFrozen = IsEntityPositionFrozen(original)
    FreezeEntityPosition(original,true)
    opened, working, session = true,true,session+1
    available, chosen = {},{}
    LocalPlayer.state:set('wardrobeBusy',true,false)
    camera = CreateCam('DEFAULT_SCRIPTED_CAMERA',true)
    sex = GetEntityModel(original)==joaat('mp_f_freemode_01') and 'female' or 'male'
    local success, ok = pcall(makePreview,sex)
    if not success or not ok then close(); message('Não foi possível carregar a prévia de roupa íntima. '..(success and '' or tostring(ok))); return end
    working = false
    RenderScriptCams(true,false,0,true,true)
    SetNuiFocus(true,true)
    local payload=state(true); payload.type='open'; payload.items={}
    SendNUIMessage(payload)
    TriggerServerEvent('cidade_acervo:request',session)
end,false)
RegisterNetEvent('cidade_acervo:items',function(token,items,counts,appearanceData,itemTags)
    while opened and token==session and working do Wait(0) end
    if not opened or token~=session then return end
    available = {}
    tags = itemTags or {}
    for _,item in ipairs(items) do available[item.id]=item end
    local removed = {}
    for category,id in pairs(chosen) do if not available[id] then removed[#removed+1]=category end end
    for _,category in ipairs(removed) do
        local saved = capture(preview)
        local armsChanged = restoreSlot(category)
        preserveOtherSlots(saved,components[category],props[category],armsChanged)
    end
    if appearanceData then
        tattooSource, hairSource = appearanceData.tattoos or {},appearanceData.hair or {}
        rebuildAppearanceOptions()
    end
    local payload=state(true); payload.type='items'; payload.items=items; payload.counts=counts; payload.tags=tags
    SendNUIMessage(payload)
end)
RegisterNUICallback('refresh',function(_,cb)
    if opened then TriggerServerEvent('cidade_acervo:request',session) end
    cb({ok=opened})
end)
RegisterNUICallback('close',function(_,cb) close(); cb({ok=true}) end)
RegisterNUICallback('sex',function(input,cb)
    if not opened or working or (input.sex~='male' and input.sex~='female') then cb({ok=false}); return end
    working = true
    local success, ok = pcall(makePreview,input.sex)
    working = false
    if success and ok then cb(state(true)) else cb({ok=false,error='Não foi possível carregar o personagem de roupa íntima.'}) end
end)
RegisterNUICallback('select',function(input,cb)
    local item = available[input.id]
    if not opened or working or not item or item.sex~=sex then cb({ok=false,error='Selecione uma peça OK ou exclusiva deste personagem.'}); return end
    local removed = chosen[item.category]==item.id
    local ok, error = true,nil
    if removed then
        local saved = capture(preview)
        local armsChanged = restoreSlot(item.category)
        preserveOtherSlots(saved,components[item.category],props[item.category],armsChanged)
    else ok,error=applyPiece(item) end
    local result=state(); result.ok=ok; result.error=error; result.removed=removed
    cb(result)
end)
local function integer(value,min,max)
    return type(value)=='number' and value==math.floor(value) and value>=min and value<=max
end
RegisterNUICallback('appearance',function(input,cb)
    if not opened or working then cb({ok=false}); return end
    local previous={hair=appearance.hair,hairColor=appearance.hairColor,beard=appearance.beard,beardColor=appearance.beardColor,tattoos={}}
    for id,value in pairs(appearance.tattoos) do previous.tattoos[id]=value end
    local kind, value = input.kind,input.value
    if kind=='hair' and integer(value,0,#appearanceOptions.hair-1) then appearance.hair=value
    elseif kind=='beard' and (value==255 or integer(value,0,appearanceOptions.beardCount-1)) then appearance.beard=value
    elseif (kind=='hairColor' or kind=='beardColor') and integer(value,0,#appearanceOptions.colors-1) then appearance[kind]=value
    elseif kind=='tattoo' and type(value)=='string' and tattooById[value] then appearance.tattoos[value]=not appearance.tattoos[value] or nil
    else cb({ok=false,error='Esta opção não está disponível para este personagem.'}); return end
    applyAppearance(preview)
    local beardOK,beardValue,_,beardColor,_,opacity=GetPedHeadOverlayData(preview,1)
    if GetPedHairColor(preview)~=appearance.hairColor or not beardOK or beardValue~=appearance.beard
        or (appearance.beard~=255 and (beardColor~=appearance.beardColor or opacity<0.99)) then
        print('[Acervo] Falha na aplicação da aparência: '..tostring(kind)..' '..tostring(value))
        appearance=previous; applyAppearance(preview)
        cb({ok=false,error='O jogo não confirmou a aparência. Feche e abra o tablet para recarregar o rosto.'}); return
    end
    cb(state())
end)
RegisterNUICallback('view',function(input,cb)
    if not opened or working or not views[input.view] then cb({ok=false}); return end
    view=input.view; positionCamera(); cb({ok=true,view=view})
end)
RegisterNUICallback('rotate',function(input,cb)
    if not opened or working or not integer(input.angle,0,360) then cb({ok=false}); return end
    rotation=input.angle
    SetEntityHeading(preview,(heading+rotation)%360)
    cb({ok=true,rotation=rotation})
end)
RegisterNUICallback('tags',function(input,cb)
    if not opened or not available[input.id] or type(input.tags)~='table' then cb({ok=false,error='Peça indisponível.'}); return end
    tagRequest=tagRequest+1
    local request=tagRequest
    pendingTags[request]=cb
    TriggerServerEvent('cidade_acervo:tags',session,request,input.id,input.tags)
    SetTimeout(8000,function()
        if pendingTags[request] then pendingTags[request]({ok=false,error='Não foi possível salvar as tags. Tente novamente.'}); pendingTags[request]=nil end
    end)
end)
RegisterNetEvent('cidade_acervo:tagsSaved',function(token,request,id,result)
    if not opened or token~=session or not pendingTags[request] then return end
    local cb=pendingTags[request]; pendingTags[request]=nil
    if result.ok then tags[id]=result.tags; result.tags=tags end
    cb(result)
end)
RegisterNUICallback('reset',function(_,cb)
    if not opened or working or not baseline then cb({ok=false}); return end
    restore(preview,baseline)
    chosen, appearance, view = {},blankAppearance(),'full'
    topUsesCompatibleArms = false
    rotation=0
    applyAppearance(preview)
    SetEntityHeading(preview,heading)
    positionCamera()
    cb(state())
end)
RegisterNUICallback('apply',function(_,cb)
    if not opened or working or blocked() then cb({ok=false,error='Aguarde para aplicar o visual.'}); return end
    working = true
    local token, model, saved = session,GetEntityModel(preview),capture(preview)
    if GetEntityModel(PlayerPedId())~=model and not exports.cidade_core:changeCharacter(model,true) then working=false; cb({ok=false,error='Não foi possível trocar o personagem.'}); return end
    if not opened or token~=session then working=false; cb({ok=false}); return end
    local ped = PlayerPedId()
    if not initializeHead(ped,headIdentity,token) then working=false; cb({ok=false,error='Não foi possível carregar o rosto.'}); return end
    restore(ped,saved)
    applyAppearance(ped)
    close(); cb({ok=true}); message('Visual aplicado.')
end)
CreateThread(function()
    while true do
        if not opened then Wait(250) else
            Wait(0)
            if not original or PlayerPedId()~=original and not working or IsEntityDead(PlayerPedId()) then close()
            else
                SetEntityLocallyInvisible(original)
                DisablePlayerFiring(PlayerId(),true)
                DisableAllControlActions(0)
                HideHudAndRadarThisFrame()
            end
        end
    end
end)
AddEventHandler('onResourceStop',function(resource) if resource==GetCurrentResourceName() then close() end end)
