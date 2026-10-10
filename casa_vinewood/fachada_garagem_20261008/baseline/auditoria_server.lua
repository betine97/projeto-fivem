RegisterNetEvent('cidade_mansao:collisionAudit', function(report)
    if type(report) ~= 'table' or report.revision ~= 'jantar-cozinha-2026-10-07' then return end
    local data = json.encode(report)
    if #data > 100000 then return end
    report.player = source
    report.timestamp = os.time()
    SaveResourceFile(GetCurrentResourceName(),'diagnostico_colisoes_runtime.json',json.encode(report),-1)
    print(('[Mansao audit] GTA reportou %d bloqueios; aprovado=%s.'):format(
        tonumber(report.blockers) or -1,tostring(report.passed)))
end)
