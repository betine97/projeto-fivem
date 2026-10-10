local resource=GetCurrentResourceName()
local cfg=json.decode(LoadResourceFile(resource,'data/config.json'))
local teleporting=false
local lastTeleport='nao iniciado'
local blips={}
local lastRescue=0
local function notice(text)
    print('[Cayo Vizinha] '..text)
    BeginTextCommandThefeedPost('STRING');AddTextComponentSubstringPlayerName(text);EndTextCommandThefeedPostTicker(false,false)
end
local function requestMaps()
    for _,name in ipairs(cfg.maps) do RequestIpl(name) end
end
local function release(ped)
    NewLoadSceneStop();ClearFocus();RenderScriptCams(false,false,0,true,false)
    SetEntityCollision(ped,true,true);SetEntityHasGravity(ped,true)
    SetEntityVisible(ped,true,false);FreezeEntityPosition(ped,false)
    SetPlayerControl(PlayerId(),true,0);DoScreenFadeIn(250)
end
local function diagnostic(stage)
    local ped=PlayerPedId();local p=GetEntityCoords(ped)
    local found,ground=GetGroundZFor_3dCoord(p.x,p.y,p.z+250.0,false)
    local active=0;local missing={}
    for _,name in ipairs(cfg.maps) do if IsIplActive(name) then active=active+1 end end
    for _,name in ipairs(cfg.sentinels) do if not IsModelInCdimage(GetHashKey(name)) then missing[#missing+1]=name end end
    local report={revision=cfg.revision,stage=stage,position={x=p.x,y=p.y,z=p.z},
        ground={found=found,z=ground},collision=HasCollisionLoadedAroundEntity(ped),
        active_maps=active,total_maps=#cfg.maps,missing_models=missing,
        faded_out=IsScreenFadedOut(),last_teleport=lastTeleport}
    print('[Cayo Vizinha] '..json.encode(report));TriggerServerEvent('cayo_vizinha:diagnostic',report)
    return report
end
local function visit(place)
    local s=cfg.destinations[place or 'pista']
    if not s then notice('F8: cayo | cayo porto | cayo mansao | ilha | porto');return end
    if teleporting then notice('Aguarde o teleporte em andamento.');return end
    local ped=PlayerPedId()
    if IsPedInAnyVehicle(ped,false) then notice('Saia do veiculo antes de usar este teleporte.');return end
    teleporting=true
    local before=GetEntityCoords(ped);local heading=GetEntityHeading(ped)
    local reached=false
    local ok,err=xpcall(function()
        if GetResourceState('fpv_drone_runtime')=='started' and exports.fpv_drone_runtime:isPiloting() then ExecuteCommand('dronedesligar') end
        TriggerEvent('cidade:preparePilot');TriggerEvent('cidade:stopProne')
        if GetResourceState('teste_ilha')=='started' then exports.teste_ilha:closeMap() end
        FreezeEntityPosition(ped,true);SetEntityHasGravity(ped,false)
        DoScreenFadeOut(200);Wait(250);requestMaps()
        if GetResourceState('teste_ilha')=='started' then exports.teste_ilha:prepareWater() end
        SetFocusPosAndVel(s.x,s.y,s.z,0.0,0.0,0.0)
        NewLoadSceneStartSphere(s.x,s.y,s.z,500.0,0)
        SetEntityCoordsNoOffset(ped,s.x,s.y,s.z+30.0,false,false,false)
        local deadline=GetGameTimer()+20000
        repeat
            RequestCollisionAtCoord(s.x,s.y,s.z);Wait(50)
            local found,height=GetGroundZFor_3dCoord(s.x,s.y,s.z+150.0,false)
            if found and math.abs(height-s.ground_z)<2.0 and HasCollisionLoadedAroundEntity(ped) then
                SetEntityCoordsNoOffset(ped,s.x,s.y,height+1.15,false,false,false)
                SetEntityHeading(ped,s.heading);SetEntityVelocity(ped,0.0,0.0,0.0)
                lastTeleport=('ok %s | solo=%.3f'):format(place or 'pista',height);reached=true;break
            end
        until GetGameTimer()>=deadline
        if not reached then lastTeleport='chao nao confirmado; retorno a origem' end
    end,debug.traceback)
    if not ok then lastTeleport='erro: '..tostring(err) end
    if not reached then
        SetEntityCoordsNoOffset(ped,before.x,before.y,before.z,false,false,false)
        SetEntityHeading(ped,heading);SetEntityVelocity(ped,0.0,0.0,0.0)
    end
    release(ped);teleporting=false
    notice(reached and 'Cayo Perico. F8: cayo porto | cayo mansao | ilha | porto | cayodiag' or 'Cayo ainda sem chao carregado; voce voltou a origem. F8: cayodiag')
    diagnostic('teleporte')
end
RegisterCommand('cayo',function(_,args) visit(args[1] or 'pista') end,false)
RegisterCommand('cayodiag',function() diagnostic('comando') end,false)
exports('getConfig',function() return cfg end)
CreateThread(function()
    requestMaps()
    for name,s in pairs(cfg.destinations) do
        local b=AddBlipForCoord(s.x,s.y,s.z);SetBlipSprite(b,90);SetBlipColour(b,2);SetBlipScale(b,0.8);SetBlipAsShortRange(b,true)
        BeginTextCommandSetBlipName('STRING');AddTextComponentSubstringPlayerName('Cayo Perico · '..name);EndTextCommandSetBlipName(b)
        blips[#blips+1]=b
    end
    Wait(8000);print(('[Cayo Vizinha] %s | %s mapas | deslocamento %.0f %.0f | F8: cayo'):format(cfg.revision,#cfg.maps,cfg.offset.x,cfg.offset.y))
end)
CreateThread(function()
    while true do
        Wait(1500)
        local p=GetEntityCoords(PlayerPedId());local b=cfg.bounds
        if not teleporting and GetGameTimer()-lastRescue>10000 and p.z < -75.0 and p.x>b.minX and p.x<b.maxX and p.y>b.minY and p.y<b.maxY then
            lastRescue=GetGameTimer();diagnostic('resgate');ExecuteCommand('ilha')
        end
    end
end)
AddEventHandler('onClientResourceStop',function(name)
    if name~=resource then return end
    if teleporting then release(PlayerPedId()) end
    for _,b in ipairs(blips) do RemoveBlip(b) end
    for _,map in ipairs(cfg.maps) do RemoveIpl(map) end
end)
