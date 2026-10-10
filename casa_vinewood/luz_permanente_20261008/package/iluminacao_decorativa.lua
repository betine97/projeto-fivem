-- The normal lighting now lives in the streamed MLO drawable and stays on in
-- every room, all hours. No nearest-light list, storey preference or room switch.
-- This loop supplies only a user-requested additive boost; base lighting does
-- not depend on this loop, the character position or the camera position.
local config=json.decode(LoadResourceFile(GetCurrentResourceName(),'iluminacao_ambiente.json'))
local origin=vector3(table.unpack(config.origin))
local lights={}
for _,row in ipairs(config.lights) do
    lights[#lights+1]={world=origin+vector3(table.unpack(row.position)),row=row}
end
local gain,draws=1.0,0
local function cameraPosition()
    local cam=GetRenderingCam()
    if cam~=0 and cam~=-1 and DoesCamExist(cam) then return GetCamCoord(cam) end
    return GetGameplayCamCoord()
end
local function status()
    print(('[Mansao luz] %d luzes nativas permanentes, todos os comodos e horarios; reforco %.2f (%d/%d volumes adicionais).'):format(
        config.native_count,gain,draws,config.max_lights))
    print('[Mansao luz] luzmansao 1 = projeto padrao; luzmansao 1.5 a 3 = reforco opcional uniforme. A base permanece acesa ao sair do comodo.')
end
RegisterCommand('luzmansao',function(_,args)
    local value=tonumber(args[1])
    if value then gain=math.max(1.0,math.min(3.0,value)) end
    status()
end,false)
RegisterCommand('mansaoluzes',status,false)
CreateThread(function()
    while true do
        draws=0
        if gain>1.001 then
            local player,camera=GetEntityCoords(PlayerPedId()),cameraPosition()
            if #(player-origin)<config.activation_distance or #(camera-origin)<config.activation_distance then
                -- Every room receives the same fixed boost; do not rank by
                -- distance or drop a room when moving to another storey.
                for _,light in ipairs(lights) do
                    local p,row=light.world,light.row;local c=row.rgb
                    DrawLightWithRange(p.x,p.y,p.z,c[1],c[2],c[3],row.range,row.intensity*(gain-1.0))
                    draws=draws+1
                end
                Wait(0)
            else Wait(500) end
        else Wait(500) end
    end
end)
