-- Warm light follows the supplied pendant geometry. These draw calls last one frame.
local config = json.decode(LoadResourceFile(GetCurrentResourceName(), 'luzes_pendentes.json'))
local origin = vector3(config.origin[1], config.origin[2], config.origin[3])
local lights = {}
for _,lamp in ipairs(config.lights) do
    lights[#lights+1] = {
        position = origin + vector3(lamp.position[1], lamp.position[2], lamp.position[3]),
        rgb = lamp.rgb, range = lamp.range, intensity = lamp.intensity
    }
end
CreateThread(function()
    while true do
        local player = GetEntityCoords(PlayerPedId())
        local camera = GetGameplayCamCoord()
        if #(player-origin) < 55.0 or #(camera-origin) < 55.0 then
            for _,lamp in ipairs(lights) do
                local p, rgb = lamp.position, lamp.rgb
                DrawLightWithRange(p.x, p.y, p.z, rgb[1], rgb[2], rgb[3], lamp.range, lamp.intensity)
            end
            Wait(0)
        else
            Wait(1000)
        end
    end
end)
