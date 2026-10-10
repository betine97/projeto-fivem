-- Cover seeking has been removed. Consume old saved key bindings without
-- searching for walls, changing postures, walking the ped or starting tasks.
CidadeCover={active=false,phase='disabled'}
RegisterCommand('cidade_cobertura',function() end,false)
RegisterCommand('cobertura',function() end,false)
RegisterCommand('coberturainfo',function() print('[Combate] Busca de cobertura removida.') end,false)
-- Also prevent the original GTA cover control on foot. Flight/drone controls
-- retain their Q bindings; this resource never registers a new cover key.
CreateThread(function()
    while true do
        Wait(0)
        local p=PlayerPedId()
        local drone=GetResourceState('fpv_drone_runtime')=='started' and exports.fpv_drone_runtime:isPiloting()
        if DoesEntityExist(p) and not IsEntityDead(p) and not IsPedInAnyVehicle(p,false) and
            not GetEntityCollisionDisabled(p) and not drone and not (CidadeTurret and CidadeTurret.active) then
            for group=0,2 do DisableControlAction(group,44,true) end
        end
    end
end)
