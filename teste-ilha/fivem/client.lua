local cfg=json.decode(LoadResourceFile(GetCurrentResourceName(),'data/config.json'))
local originalMaps=json.decode(LoadResourceFile(GetCurrentResourceName(),'data/mapas_originais.json')) or {}
local waterReady=false
local mapOpen=false
local teleporting=false
local mapsCleared=false
local lastWaterResult='nao iniciado'
local lastTeleport='nao iniciado'
local function cityLoaded()
    -- Sentinel exists in the stock downtown metadata, excluded from this level.
    return IsModelInCdimage(GetHashKey('dt1_props_combo0107_01_lod')) or IsIplActive('dt1_00')
end
local function waterCount()
    local ok,count=pcall(GetWaterQuadCount)
    return ok and count or -1
end
local function notice(text)
    print('[Teste Ilha] '..text)
    BeginTextCommandThefeedPost('STRING');AddTextComponentSubstringPlayerName(text);EndTextCommandThefeedPostTicker(false,false)
end
local function closeMap()mapOpen=false;SetNuiFocus(false,false);SendNUIMessage({action='close'})end
local function clearOriginalMaps()
    for i,name in ipairs(originalMaps) do
        RemoveIpl(name)
        if i%32==0 then Wait(0) end
    end
    mapsCleared=true
end
local function prepareWater()
    if waterReady and waterCount()~=cfg.water_quads then waterReady=false end
    if not waterReady then
        local ok,result=pcall(LoadWaterFromPath,GetCurrentResourceName(),'data/water.xml')
        lastWaterResult=tostring(result)
        -- The native return confirms the file opened, not that its regions loaded.
        local deadline=GetGameTimer()+3000
        repeat
            Wait(50)
            waterReady=ok and (result==true or result==1) and waterCount()==cfg.water_quads
        until waterReady or GetGameTimer()>=deadline or not ok or not result
        print(('[Teste Ilha] Agua nativa: %s | retorno=%s | setores=%s/%s'):format(tostring(waterReady),lastWaterResult,waterCount(),cfg.water_quads))
        if not waterReady then notice('Agua personalizada ainda nao carregou. O movimento continua liberado. F8: ilhadiag') end
    end
    -- Keep the engine's water clipping grid. Expanding its rectangle while the
    -- stock 559-region water array remains active can cause invalid quad reads.
    SetDeepOceanScaler(0.15)
end
local function releasePlayer(ped)
    NewLoadSceneStop();ClearFocus();RenderScriptCams(false,false,0,true,false)
    SetEntityCollision(ped,true,true);SetEntityVisible(ped,true,false)
    SetEntityHasGravity(ped,true);SetPlayerControl(PlayerId(),true,0)
    FreezeEntityPosition(ped,false);DoScreenFadeIn(300)
end
local function stopMovementModes()
    if GetResourceState('fpv_drone_runtime')=='started' and exports.fpv_drone_runtime:isPiloting() then ExecuteCommand('dronedesligar') end
    TriggerEvent('cidade:preparePilot');TriggerEvent('cidade:stopProne')
    closeMap();ClearFocus();RenderScriptCams(false,false,0,true,false)
end
local function loadDestination(ped,s)
    local expected=s.z-1.15
    SetFocusPosAndVel(s.x,s.y,s.z,0.0,0.0,0.0)
    NewLoadSceneStartSphere(s.x,s.y,s.z,500.0,0)
    -- Stream while frozen at the destination, then verify its authored height.
    SetEntityCoordsNoOffset(ped,s.x,s.y,s.z+80.0,false,false,false)
    local deadline=GetGameTimer()+12000
    local found,height=false,0.0
    repeat
        RequestCollisionAtCoord(s.x,s.y,s.z)
        Wait(50)
        found,height=GetGroundZFor_3dCoord(s.x,s.y,s.z+250.0,false)
        if found and math.abs(height-expected)<=3.0 and HasCollisionLoadedAroundEntity(ped) then
            SetEntityCoordsNoOffset(ped,s.x,s.y,height+1.15,false,false,false)
            SetEntityHeading(ped,s.heading);SetEntityVelocity(ped,0.0,0.0,0.0)
            lastTeleport=('ok | esperado=%.2f | solo=%.2f'):format(expected,height)
            return true
        end
    until GetGameTimer()>=deadline
    lastTeleport=('falha | esperado=%.2f | solo=%s %.2f'):format(expected,tostring(found),height or 0)
    return false
end
local function visit(s,label,isSample)
    if teleporting then notice('Aguarde o teleporte em andamento.');return end
    local ped=PlayerPedId()
    if IsPedInAnyVehicle(ped,false) then notice('Saia do veiculo antes de usar este teleporte.');return end
    teleporting=true
    local before=GetEntityCoords(ped);local heading=GetEntityHeading(ped)
    local reached=false
    local ok,err=xpcall(function()
        stopMovementModes();FreezeEntityPosition(ped,true);DoScreenFadeOut(250);Wait(300)
        if not mapsCleared then clearOriginalMaps() end
        prepareWater()
        if isSample then
            RequestIpl('ti_amostra_natural')
            for _,name in ipairs(cfg.natural_sample.models) do RequestModel(GetHashKey(name)) end
            local modelDeadline=GetGameTimer()+8000
            local missing={}
            repeat
                Wait(50);missing={}
                for _,name in ipairs(cfg.natural_sample.models) do
                    if not HasModelLoaded(GetHashKey(name)) then missing[#missing+1]=name end
                end
            until #missing==0 or GetGameTimer()>=modelDeadline
            if #missing>0 then
                lastTeleport='modelos ausentes: '..table.concat(missing,', ')
                notice('Amostra nao carregou os modelos; voce continua na origem. F8: amostradiag')
                return
            end
        end
        reached=loadDestination(ped,s)
        if not reached then
            local failed=lastTeleport
            if isSample then reached=loadDestination(ped,cfg.spawn) end
            if not reached then
                SetEntityCoordsNoOffset(ped,before.x,before.y,before.z,false,false,false)
                SetEntityHeading(ped,heading);SetEntityVelocity(ped,0.0,0.0,0.0)
            end
            lastTeleport=failed..(reached and ' | retorno=pista' or ' | retorno=origem')
            notice('Destino sem solo confirmado; retorno de seguranca. F8: amostradiag')
        else notice(label) end
    end,debug.traceback)
    if not ok then
        SetEntityCoordsNoOffset(ped,before.x,before.y,before.z,false,false,false)
        SetEntityHeading(ped,heading);lastTeleport='erro: '..tostring(err);print('[Teste Ilha] '..lastTeleport)
    end
    releasePlayer(ped)
    if isSample then for _,name in ipairs(cfg.natural_sample.models) do SetModelAsNoLongerNeeded(GetHashKey(name)) end end
    teleporting=false
end
exports('getSpawn',function() return cfg.spawn end)
exports('prepareSpawn',function()
    if not mapsCleared then clearOriginalMaps() end
    if cityLoaded() then notice('Mapa antigo ainda carregado! Feche completamente o FiveM e abra novamente para entrar apenas na ilha.') end
    prepareWater()
    RequestCollisionAtCoord(cfg.spawn.x,cfg.spawn.y,cfg.spawn.z)
    return true
end)
RegisterCommand('ilha',function()
    visit(cfg.spawn,'Voce esta na pista da ilha. F8: amostrailha | mapailha | voar | admin',false)
end,false)
RegisterCommand('ilhadiag',function()
    local p=GetEntityCoords(PlayerPedId());local ok,h=GetGroundZFor_3dCoord(p.x,p.y,p.z+250,false)
    waterReady=waterReady and waterCount()==cfg.water_quads
    print(('[Teste Ilha] revisao=%s | pos=%.2f %.2f %.2f | solo=%s %.2f | colisao=%s | cidade_antiga=%s | agua=%s | setores=%s/%s | retorno=%s | teleporte=%s'):format(cfg.revision,p.x,p.y,p.z,tostring(ok),h or 0,tostring(HasCollisionLoadedAroundEntity(PlayerPedId())),tostring(cityLoaded()),tostring(waterReady),waterCount(),cfg.water_quads,lastWaterResult,lastTeleport))
end,false)
RegisterCommand('amostrailha',function()
    local sample=cfg.natural_sample
    if not sample then notice('Amostra natural ainda nao instalada.');return end
    visit(sample.spawn,'Amostra natural: palmeiras, arvores, pedras, grama, terra, areia e barro. F8: ilha para voltar a pista.',true)
end,false)
RegisterCommand('amostradiag',function()
    if not cfg.natural_sample then print('[Teste Ilha] Amostra ausente.');return end
    local missing={};local visible=0;local p=GetEntityCoords(PlayerPedId())
    for _,name in ipairs(cfg.natural_sample.models) do
        local hash=GetHashKey(name)
        if not IsModelInCdimage(hash) then missing[#missing+1]=name end
        if GetClosestObjectOfType(p.x,p.y,p.z,200.0,hash,false,false,false)~=0 then visible=visible+1 end
    end
    local active=0
    for _,name in ipairs(originalMaps) do if IsIplActive(name) then active=active+1 end end
    print(('[Teste Ilha] Amostra: mapa=%s | tipos de objetos proximos=%s/12 | ausentes=%s | mapas originais ativos=%s'):format(tostring(IsIplActive('ti_amostra_natural')),visible,table.concat(missing,', '),active))
    ExecuteCommand('ilhadiag')
end,false)
RegisterCommand('mapailha',function()
    if mapOpen then closeMap();return end
    mapOpen=true;SetNuiFocus(true,true);SendNUIMessage({action='open',spawn=cfg.spawn})
end,false)
RegisterNUICallback('close',function(_,cb)closeMap();cb({ok=true})end)
CreateThread(function()
    clearOriginalMaps();RequestIpl('ti_amostra_natural')
    Wait(5000);clearOriginalMaps()
end)
CreateThread(function()
    while true do
        Wait(0)
        -- The stock city radar is excluded; the authored island map is in NUI.
        DisplayRadar(false)
        SetPedDensityMultiplierThisFrame(0.0);SetScenarioPedDensityMultiplierThisFrame(0.0,0.0)
        SetVehicleDensityMultiplierThisFrame(0.0);SetRandomVehicleDensityMultiplierThisFrame(0.0);SetParkedVehicleDensityMultiplierThisFrame(0.0)
        SetGarbageTrucks(false);SetRandomBoats(false)
    end
end)
CreateThread(function()
    while true do
        Wait(1000)
        local ped=PlayerPedId();local p=GetEntityCoords(ped)
        if mapOpen then SendNUIMessage({action='position',x=p.x,y=p.y,heading=GetEntityHeading(ped)}) end
        if not teleporting and p.z < -75.0 and p.x>cfg.limits.minX and p.x<cfg.limits.maxX and p.y>cfg.limits.minY and p.y<cfg.limits.maxY then
            ExecuteCommand('ilha');notice('Retorno de seguranca: queda abaixo do terreno. Use ilhadiag para conferir a colisao.')
        end
    end
end)
AddEventHandler('onClientResourceStop',function(name)
    if name~=GetCurrentResourceName() then return end
    closeMap();if teleporting then releasePlayer(PlayerPedId()) end
    DisplayRadar(true);ResetDeepOceanScaler();ResetWater()
end)
