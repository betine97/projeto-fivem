local resource=GetCurrentResourceName()
local cfg=json.decode(LoadResourceFile(resource,'data/config.json'))
RegisterNetEvent('natureza_integrada:diagnostic',function(report)
    if type(report)~='table' then return end
    local text=json.encode(report)
    if #text>3000 then return end
    print(('[Natureza Ilha] jogador=%s %s'):format(source,text))
end)
CreateThread(function()
    print(('[Natureza Ilha] %s | mapas=%d | arvores=%d | rasteira=%d | identidade=100%%'):format(cfg.revision,#cfg.maps,cfg.counts.tree,cfg.grass_instances))
end)
