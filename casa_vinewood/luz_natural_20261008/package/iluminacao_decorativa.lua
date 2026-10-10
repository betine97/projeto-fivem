-- Soft native fixture lighting and sparse indirect fill. Diagnostic commands only.
local config=json.decode(LoadResourceFile(GetCurrentResourceName(),'iluminacao_ambiente.json'))
local function weatherName(hash)
    for _,name in ipairs({'EXTRASUNNY','CLEAR','NEUTRAL','SMOG','FOGGY','OVERCAST','CLOUDS','CLEARING','RAIN','THUNDER','SNOW','BLIZZARD','SNOWLIGHT','XMAS','HALLOWEEN'}) do
        if GetHashKey(name)==hash then return name end
    end
    return tostring(hash)
end
local function status()
    print(('[Mansao luz] LUMINARIAS: %d spots brancos e %d fontes amarelas nos pendentes.'):format(config.native_ceiling_count,config.native_pendant_count))
    print(('[Mansao luz] Focos suaves ate o piso; %d preenchimentos indiretos nativos de baixa potencia, sem reflexos especulares.'):format(config.native_bounce_count))
    print(('[Mansao luz] Lentes brancas em quatro LODs; escada %d e TV %d fontes nativas amarelas.'):format(config.native_stair_count,config.native_tv_led_count))
    print('[Mansao luz] Fontes nativas constantes; nenhuma chamada Lua de iluminacao por quadro. O antigo reforco luzmansao nao adiciona fontes.')
    print(('[Mansao luz] Clima observado: %s -> %s; filtros principal %d, extra %d.'):format(
        weatherName(GetPrevWeatherTypeHashName()),weatherName(GetNextWeatherTypeHashName()),
        GetTimecycleModifierIndex(),GetExtraTimecycleModifierIndex()))
end
RegisterCommand('luzmansao',status,false)
RegisterCommand('mansaoluzes',status,false)
