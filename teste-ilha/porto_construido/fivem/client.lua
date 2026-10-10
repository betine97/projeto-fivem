local cfg=json.decode(LoadResourceFile(GetCurrentResourceName(),'data/config.json'))
local busy=false
local function notice(message)
    print('[Porto Esperanca] '..message)
    BeginTextCommandThefeedPost('STRING');AddTextComponentSubstringPlayerName(message);EndTextCommandThefeedPostTicker(false,false)
end
local function release(ped)
    ClearFocus();NewLoadSceneStop();ShutdownLoadingScreen();ShutdownLoadingScreenNui()
    RenderScriptCams(false,false,0,true,false);SetEntityVisible(ped,true,false);SetPlayerControl(PlayerId(),true,0)
    SetEntityCollision(ped,true,true);SetEntityHasGravity(ped,true);FreezeEntityPosition(ped,false);DoScreenFadeIn(300)
end
RegisterCommand('porto',function()
    if busy then return end
    local ped=PlayerPedId()
    if IsPedInAnyVehicle(ped,false) then notice('Saia do veiculo para visitar o porto.');return end
    busy=true;local before=GetEntityCoords(ped);local oldHeading=GetEntityHeading(ped);local reached=false
    local ok,err=xpcall(function()
        if GetResourceState('fpv_drone_runtime')=='started' and exports.fpv_drone_runtime:isPiloting() then ExecuteCommand('dronedesligar') end
        TriggerEvent('cidade:preparePilot');TriggerEvent('cidade:stopProne')
        FreezeEntityPosition(ped,true);SetEntityHasGravity(ped,false);SetEntityVelocity(ped,0,0,0)
        exports.teste_ilha:prepareSpawn()
        DoScreenFadeOut(200);Wait(250)
        for _,name in ipairs(cfg.maps) do RequestIpl(name) end
        for _,name in ipairs(cfg.probe_models) do RequestModel(GetHashKey(name)) end
        local p=cfg.spawn;SetFocusPosAndVel(p.x,p.y,p.z,0.0,0.0,0.0);NewLoadSceneStartSphere(p.x,p.y,p.z,550.0,0)
        SetEntityCoordsNoOffset(ped,p.x,p.y,p.z+60,false,false,false)
        local deadline=GetGameTimer()+15000
        repeat
            RequestCollisionAtCoord(p.x,p.y,p.z);Wait(100)
            local found,z=GetGroundZFor_3dCoord(p.x,p.y,p.z+200,false)
            if found and math.abs(z-cfg.ground_z)<1 and HasCollisionLoadedAroundEntity(ped) then
                SetEntityCoordsNoOffset(ped,p.x,p.y,z+1.15,false,false,false);SetEntityHeading(ped,p.heading);SetEntityVelocity(ped,0,0,0);reached=true;break
            end
        until GetGameTimer()>=deadline
        if not reached then error('colisao da praca ainda nao carregou') end
    end,debug.traceback)
    if not ok then
        SetEntityCoordsNoOffset(ped,before.x,before.y,before.z,false,false,false);SetEntityHeading(ped,oldHeading);notice('Nao foi possivel carregar o porto: '..tostring(err))
    else notice('Porto Esperanca: cais, bairro, casas e vegetacao carregados.') end
    release(ped);busy=false
    for _,name in ipairs(cfg.probe_models) do SetModelAsNoLongerNeeded(GetHashKey(name)) end
end,false)
RegisterCommand('portodiag',function()
    local report={revision=cfg.revision,models={},ground={},water_quads=GetWaterQuadCount()}
    for _,name in ipairs(cfg.probe_models) do
        local hash=GetHashKey(name);report.models[#report.models+1]={name=name,in_cdimage=IsModelInCdimage(hash),valid=IsModelValid(hash)}
    end
    for _,p in ipairs(cfg.ground_probes) do
        RequestCollisionAtCoord(p.x,p.y,p.z);local found,z=GetGroundZFor_3dCoord(p.x,p.y,p.z+150,false)
        report.ground[#report.ground+1]={name=p.name,found=found,z=z,expected=p.expected}
    end
    print('[Porto Esperanca] '..json.encode(report));TriggerServerEvent('porto_esperanca:diagnostic',report)
end,false)
CreateThread(function()
    while not NetworkIsSessionStarted() do Wait(500) end
    for _,name in ipairs(cfg.maps) do RequestIpl(name) end
    local b=AddBlipForCoord(cfg.spawn.x,cfg.spawn.y,cfg.spawn.z);SetBlipSprite(b,410);SetBlipScale(b,.8);SetBlipAsShortRange(b,true)
    BeginTextCommandSetBlipName('STRING');AddTextComponentSubstringPlayerName('Porto Esperanca');EndTextCommandSetBlipName(b)
    SetWindSpeed(.7)
end)
AddEventHandler('onClientResourceStop',function(name)
    if name==GetCurrentResourceName() and busy then release(PlayerPedId()) end
end)
