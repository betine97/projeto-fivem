local cfg=json.decode(LoadResourceFile(GetCurrentResourceName(),'hospital.json'))
local origin=vector3(table.unpack(cfg.origin));local leaves,states,motions={},{},{};local running=true
local function apply(id,opened,instant)
    states[id]=opened;local e=leaves[id];local d=cfg.doors[id];if not e or not d then return end
    local p=origin+vector3(table.unpack(d.pos));local target=p+vector3(opened and d.travel*(d.direction or 1) or 0,0,0)
    if instant then SetEntityCoordsNoOffset(e,target.x,target.y,target.z,false,false,false);motions[id]=nil;SetEntityCollision(e,true,true)
    else motions[id]={from=GetEntityCoords(e),target=target,started=GetGameTimer()};SetEntityCollision(e,false,false) end
end
RegisterNetEvent('cidade_hospital:snapshot',function(snapshot)
    if source~=65535 or type(snapshot)~='table' then return end
    for _,d in ipairs(cfg.doors) do if not motions[d.id] then apply(d.id,snapshot[d.id]==true or snapshot[tostring(d.id)]==true,true) end end
end)
RegisterNetEvent('cidade_hospital:door',function(id,opened)if source==65535 and cfg.doors[id] and type(opened)=='boolean' then apply(id,opened,false) end end)
local function cleanup()
    for id,e in pairs(leaves) do if DoesEntityExist(e) then DeleteEntity(e) end;leaves[id]=nil;motions[id]=nil end
end
CreateThread(function()
    while running do
        if #(GetEntityCoords(PlayerPedId())-origin)<170 then
            for _,d in ipairs(cfg.doors) do
                if not leaves[d.id] then
                    local hash=joaat(d.model);RequestModel(hash);local deadline=GetGameTimer()+10000
                    while running and not HasModelLoaded(hash) and GetGameTimer()<deadline do Wait(20) end
                    if running and HasModelLoaded(hash) then
                        local p=origin+vector3(table.unpack(d.pos));local e=CreateObjectNoOffset(hash,p.x,p.y,p.z,false,false,false)
                        if e~=0 then SetEntityAsMissionEntity(e,true,true);FreezeEntityPosition(e,true);SetEntityHeading(e,d.heading);SetEntityLodDist(e,220);leaves[d.id]=e;apply(d.id,states[d.id]==true,true) end
                    end
                    SetModelAsNoLongerNeeded(hash)
                end
            end
            TriggerServerEvent('cidade_hospital:states')
        else cleanup() end
        Wait(3000)
    end
end)
CreateThread(function()
    while running do
        local near= #(GetEntityCoords(PlayerPedId())-origin)<110
        if near then
            for id,t in pairs(motions) do
                if leaves[id] then
                    local s=math.min(1,(GetGameTimer()-t.started)/650);s=s*s*(3-2*s);local p=t.from+(t.target-t.from)*s;SetEntityCoordsNoOffset(leaves[id],p.x,p.y,p.z,false,false,false)
                    if s>=1 then motions[id]=nil;SetEntityCollision(leaves[id],true,true) end
                end
            end
            local p=GetEntityCoords(PlayerPedId());local best,dist=nil,2.5
            for _,d in ipairs(cfg.doors) do
                local center=origin+vector3(d.pos[1]+d.width/2,d.pos[2],d.pos[3]+1);local dd=#(p-center)
                if dd<dist then best=d.id;dist=dd end
            end
            if best then BeginTextCommandDisplayHelp('STRING');AddTextComponentSubstringPlayerName('~INPUT_CONTEXT~ abrir/fechar porta do hospital');EndTextCommandDisplayHelp(0,false,true,-1);if IsControlJustPressed(0,38) then TriggerServerEvent('cidade_hospital:toggle',best) end end
        end
        Wait(near and 0 or 500)
    end
end)
local teleporting=false
RegisterCommand('hospital',function()
    if not LocalPlayer.state.cidadeAdmin then print('[Hospital] Aguarde sua autorizacao ADM.');return end
    if teleporting then return end
    teleporting=true
    CreateThread(function()
        TriggerEvent('cidade:preparePilot');TriggerEvent('cidade:stopProne')
        local ped=PlayerPedId();local previous=GetEntityCoords(ped);local p=origin+vector3(0,-25,1)
        if IsPedInAnyVehicle(ped,false) then print('[Hospital] Saia do veiculo primeiro.');teleporting=false;return end
        DoScreenFadeOut(150);FreezeEntityPosition(ped,true)
        local ok,err=pcall(function()
            RequestCollisionAtCoord(p.x,p.y,p.z);NewLoadSceneStartSphere(p.x,p.y,p.z,130,0);local deadline=GetGameTimer()+8000
            while not IsNewLoadSceneLoaded() and GetGameTimer()<deadline do Wait(0) end
            SetEntityCoordsNoOffset(ped,p.x,p.y,p.z,false,false,false);SetEntityHeading(ped,0)
            deadline=GetGameTimer()+5000
            while not HasCollisionLoadedAroundEntity(ped) and GetGameTimer()<deadline do RequestCollisionAtCoord(p.x,p.y,p.z);Wait(0) end
            if not HasCollisionLoadedAroundEntity(ped) then SetEntityCoordsNoOffset(ped,previous.x,previous.y,previous.z,false,false,false);error('Colisao ainda nao carregou. Tente novamente.') end
            SetEntityVelocity(ped,0,0,0)
        end)
        NewLoadSceneStop();FreezeEntityPosition(ped,false);DoScreenFadeIn(200);teleporting=false
        print(ok and '[Hospital] Carcer Way. E abre/fecha as portas; escada na extremidade direita do lobby.' or '[Hospital] '..tostring(err))
    end)
end,false)
local blip
CreateThread(function()
    blip=AddBlipForCoord(origin.x,origin.y-24,origin.z);SetBlipSprite(blip,61);SetBlipColour(blip,2);SetBlipScale(blip,.9);SetBlipAsShortRange(blip,true);BeginTextCommandSetBlipName('STRING');AddTextComponentSubstringPlayerName('Pillbox Medical Center - Carcer Way');EndTextCommandSetBlipName(blip)
end)
AddEventHandler('onResourceStop',function(name)
    if name~=GetCurrentResourceName() then return end
    running=false;cleanup();if blip then RemoveBlip(blip) end
    if teleporting then NewLoadSceneStop();FreezeEntityPosition(PlayerPedId(),false);DoScreenFadeIn(200) end
end)
