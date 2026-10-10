local last={}
RegisterNetEvent('porto_esperanca:diagnostic',function(report)
    local player=source
    if type(report)~='table' or type(report.models)~='table' or #report.models>40 or type(report.ground)~='table' or #report.ground>20 then return end
    local now=GetGameTimer();if last[player] and now-last[player]<5000 then return end;last[player]=now
    report.player_id=player;report.client_report=true
    local encoded=json.encode(report)
    if #encoded<16000 then SaveResourceFile(GetCurrentResourceName(),'data/diagnostico_cliente.json',encoded,-1);print('[Porto Esperanca] Diagnostico do jogador '..player..' recebido.') end
end)
AddEventHandler('playerDropped',function()last[source]=nil end)
local lastSpawn={}
RegisterNetEvent('porto_esperanca:spawnDiagnostic',function(report)
    local player=source
    if type(report)~='table' or (report.stage~='antes' and report.stage~='depois') then return end
    local encoded=json.encode(report)
    if #encoded>4000 then return end
    local now=GetGameTimer()
    if lastSpawn[player] and now-lastSpawn[player]<1000 then return end
    lastSpawn[player]=now
    SaveResourceFile(GetCurrentResourceName(),'data/entrada_'..player..'_'..report.stage..'.json',encoded,-1)
    print('[Entrada Ilha] jogador='..player..' '..encoded)
end)
AddEventHandler('playerDropped',function()lastSpawn[source]=nil end)
