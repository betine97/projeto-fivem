local resource=GetCurrentResourceName()
local config=json.decode(LoadResourceFile(resource,'clima_interior.json'))
local M=CidadeClimaInterior
local origin=vector3(table.unpack(config.origin))
local probe=origin+vector3(table.unpack(config.probe))
local room=GetHashKey(config.room)
local interior,forcedPed,forcedViewport=0,nil,false
local pinnedInterior=0
local insidePed,insideCamera=false,false
local nextProbe,lastWarning=0,-30000
local running=true
local function coords(v) return {v.x,v.y,v.z} end
local function cameraPosition()
    local cam=GetRenderingCam()
    if cam~=0 and cam~=-1 and DoesCamExist(cam) then return GetCamCoord(cam) end
    return GetGameplayCamCoord()
end
local function release()
    if forcedPed and DoesEntityExist(forcedPed) then ClearRoomForEntity(forcedPed) end
    if forcedViewport then ClearRoomForGameViewport() end
    forcedPed,forcedViewport=nil,false
end
local function detect(now)
    if now<nextProbe then return end
    nextProbe=now+1000
    local found=GetInteriorAtCoordsWithType(probe.x,probe.y,probe.z,config.archetype)
    if found==0 or not IsValidInterior(found) then found=0 end
    if found~=interior then release() end
    if pinnedInterior~=found then
        if pinnedInterior~=0 and IsValidInterior(pinnedInterior) then UnpinInterior(pinnedInterior) end
        pinnedInterior=found
        if found~=0 then PinInteriorInMemory(found) end
    end
    interior=found
    if interior~=0 and not IsInteriorReady(interior) then RefreshInterior(interior) end
end
RegisterCommand('mansaoclima',function()
    local ped=PlayerPedId()
    print(('[Mansao clima] MLO=%d pronto=%s personagem=%s camera=%s interiorPed=%d salaPed=%s'):format(
        interior,tostring(interior~=0 and IsInteriorReady(interior)),tostring(insidePed),tostring(insideCamera),
        GetInteriorFromEntity(ped),tostring(GetRoomKeyFromEntity(ped))))
    print('[Mansao clima] Protecao local por sala MLO; clima externo e comandos clima/tempo preservados.')
end,false)
CreateThread(function()
    while running do
        local ped=PlayerPedId(); local p=GetEntityCoords(ped); local cam=cameraPosition()
        if #(p-origin)<65 or #(cam-origin)<65 then
            local now=GetGameTimer(); detect(now)
            insidePed=M.sheltered(config,coords(p),insidePed)
            insideCamera=M.sheltered(config,coords(cam),insideCamera)
            if interior~=0 and IsInteriorReady(interior) then
                if forcedPed and (forcedPed~=ped or not insidePed) then
                    if DoesEntityExist(forcedPed) then ClearRoomForEntity(forcedPed) end
                    forcedPed=nil
                end
                if insidePed then ForceRoomForEntity(ped,interior,room); forcedPed=ped end
                if insideCamera then ForceRoomForGameViewport(interior,room); forcedViewport=true
                elseif forcedViewport then ClearRoomForGameViewport(); forcedViewport=false end
            else
                release()
                if (insidePed or insideCamera) and now-lastWarning>30000 then
                    lastWarning=now
                    print('[Mansao clima] Interior MLO ainda nao carregou. Recarregue cidade_mansao no servidor e reconecte; F8 mansaoclima mostra o estado.')
                end
            end
            Wait(0)
        else
            release(); insidePed,insideCamera=false,false
            if pinnedInterior~=0 and IsValidInterior(pinnedInterior) then UnpinInterior(pinnedInterior) end
            pinnedInterior=0; interior=0; nextProbe=0
            Wait(250)
        end
    end
end)
AddEventHandler('onResourceStop',function(name)
    if name~=resource then return end
    running=false; release()
    if pinnedInterior~=0 and IsValidInterior(pinnedInterior) then UnpinInterior(pinnedInterior) end
    pinnedInterior=0
end)
