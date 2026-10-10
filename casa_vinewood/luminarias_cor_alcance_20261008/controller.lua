-- Native BASE drawables hold constant white ceiling lights and yellow pendants.
-- Lua supplies only an optional LOW room bounce, never high ceiling hot spots.
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
local function weatherName(hash)
    for _,name in ipairs({'EXTRASUNNY','CLEAR','NEUTRAL','SMOG','FOGGY','OVERCAST','CLOUDS','CLEARING','RAIN','THUNDER','SNOW','BLIZZARD','SNOWLIGHT','XMAS','HALLOWEEN'}) do
        if GetHashKey(name)==hash then return name end
    end
    return tostring(hash)
end
local function status()
    print(('[Mansao luz] %d fontes nativas constantes: %d spots brancos, %d pendentes amarelos, %d preenchimentos baixos.'):format(
        config.native_count,config.native_ceiling_count,config.native_pendant_count,config.native_bounce_count))
    print(('[Mansao luz] Reforco %.2f; %d/%d chamadas Lua adicionais. Padrao: luzmansao 1; reforco: luzmansao 1.5 a 2.'):format(gain,draws,config.max_lights))
    print(('[Mansao luz] Clima observado: %s -> %s. Volumes luminosos de nevoa: 0; o recurso nao altera o clima.'):format(
        weatherName(GetPrevWeatherTypeHashName()),weatherName(GetNextWeatherTypeHashName())))
    print(('[Mansao luz] Filtro atmosferico observado: principal %d, extra %d (-1 = nenhum).'):format(
        GetTimecycleModifierIndex(),GetExtraTimecycleModifierIndex()))
end
RegisterCommand('luzmansao',function(_,args)
    local value=tonumber(args[1])
    if value then gain=math.max(1.0,math.min(2.0,value)) end
    status()
end,false)
RegisterCommand('mansaoluzes',status,false)
CreateThread(function()
    while true do
        draws=0
        if gain>1.001 then
            local player,camera=GetEntityCoords(PlayerPedId()),cameraPosition()
            if #(player-origin)<config.activation_distance or #(camera-origin)<config.activation_distance then
                -- The entire house receives the SAME fixed optional bounce.
                -- Do not sort by nearest room, prefer a floor or switch on entry.
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
