local last={}
RegisterNetEvent('cayo_vizinha:diagnostic',function(report)
    local player=source
    if type(report)~='table' or type(report.position)~='table' or type(report.missing_models)~='table' or #report.missing_models>20 then return end
    local now=GetGameTimer();if last[player] and now-last[player]<5000 then return end;last[player]=now
    report.player_id=player;report.client_report=true
    local encoded=json.encode(report)
    if #encoded>12000 then return end
    SaveResourceFile(GetCurrentResourceName(),'data/diagnostico_cliente.json',encoded,-1)
    print('[Cayo Vizinha] '..encoded)
end)
AddEventHandler('playerDropped',function() last[source]=nil end)
CreateThread(function()
    local cfg=json.decode(LoadResourceFile(GetCurrentResourceName(),'data/config.json'))
    print(('[Cayo Vizinha] %s | mapas=%s | Cayo a leste da ilha autoral | F8: cayo'):format(cfg.revision,#cfg.maps))
end)
