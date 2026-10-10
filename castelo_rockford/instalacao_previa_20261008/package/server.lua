RegisterCommand('castelo', function(source)
    if source <= 0 then
        print('[Castelo] Use castelo no F8 do jogador administrador.')
        return
    end
    if not IsPlayerAceAllowed(source, 'cidade.admin') then
        TriggerClientEvent('cidade_castelo:mensagem', source, 'Comando disponivel para administradores.')
        return
    end
    TriggerClientEvent('cidade_castelo:visitar', source)
end, false)
