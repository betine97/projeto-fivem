local enabled=false
local context=nil
local function droneActive()
    return GetResourceState('fpv_drone_runtime')=='started' and exports.fpv_drone_runtime:isPiloting()
end
local function disable()
    enabled=false; context=nil
    SetNightvision(false)
    SendNUIMessage({type='nightvision',active=false})
end
RegisterCommand('nightvision',function()
    if enabled then disable(); return end
    if IsEntityDead(PlayerPedId()) then return end
    if droneActive() then
        if not exports.fpv_drone_runtime:setFirstPerson() then return end
        context='drone'
    else
        SetFollowPedCamViewMode(4)
        SetFollowVehicleCamViewMode(4)
        context=IsPedInAnyVehicle(PlayerPedId(),false) and 'vehicle' or 'ped'
    end
    enabled=true
    SetNightvision(true)
    print('[Visao noturna] Ativada. Mude de camera ou digite nightvision novamente para desligar.')
end,false)
CreateThread(function()
    while true do
        if not enabled then Wait(100) else
            Wait(0)
            local ped=PlayerPedId()
            local firstPerson=false
            if context=='drone' then
                firstPerson=droneActive() and exports.fpv_drone_runtime:isFirstPerson()
            elseif not droneActive() and IsGameplayCamRendering() then
                local vehicle=IsPedInAnyVehicle(ped,false)
                firstPerson=(context=='vehicle' and vehicle and GetFollowVehicleCamViewMode()==4)
                    or (context=='ped' and not vehicle and GetFollowPedCamViewMode()==4)
            end
            if IsEntityDead(ped) or not firstPerson then disable()
            else
                local rotation=GetFinalRenderedCamRot(2)
                SendNUIMessage({type='nightvision',active=true,visible=not IsPauseMenuActive(),
                    heading=(-rotation.z)%360,pitch=rotation.x,roll=rotation.y})
                Wait(16)
            end
        end
    end
end)
AddEventHandler('onResourceStop',function(name)
    if name==GetCurrentResourceName() then disable() end
end)
