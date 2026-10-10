-- Fixture-only native lighting. No room fill, additive boost or draw thread.
local config=json.decode(LoadResourceFile(GetCurrentResourceName(),'iluminacao_ambiente.json'))
local function weatherName(hash)
    for _,name in ipairs({'EXTRASUNNY','CLEAR','NEUTRAL','SMOG','FOGGY','OVERCAST','CLOUDS','CLEARING','RAIN','THUNDER','SNOW','BLIZZARD','SNOWLIGHT','XMAS','HALLOWEEN'}) do
        if GetHashKey(name)==hash then return name end
    end
    return tostring(hash)
end
local function status()
    print(('[Mansao luz] APENAS LUMINARIAS: %d spots brancos e %d fontes amarelas nos pendentes.'):format(config.native_ceiling_count,config.native_pendant_count))
    print('[Mansao luz] Feixes fortes para baixo ate o piso: raio 1,10 m; linear 0,80 m. Preenchimentos, reforcos e LEDs decorativos: desligados.')
    print('[Mansao luz] Fontes nativas constantes; nenhuma chamada Lua de iluminacao por quadro. O antigo reforco luzmansao nao adiciona fontes.')
    print(('[Mansao luz] Clima observado: %s -> %s; filtros principal %d, extra %d.'):format(
        weatherName(GetPrevWeatherTypeHashName()),weatherName(GetNextWeatherTypeHashName()),
        GetTimecycleModifierIndex(),GetExtraTimecycleModifierIndex()))
end
RegisterCommand('luzmansao',status,false)
RegisterCommand('mansaoluzes',status,false)
