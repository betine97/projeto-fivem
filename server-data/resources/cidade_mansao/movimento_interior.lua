-- Keep the ordinary GTA locomotion and follow camera, with a gentle indoor pace.
local origin = vector3(-976.101013, 676.730896, 157.835037)
local ground = {
    {-9.271000, -12.000000},
    {-8.270000, -12.000000},
    {-8.270000, -13.199000},
    {1.546000, -13.199000},
    {1.546000, -11.518000},
    {4.722000, -11.518000},
    {4.722000, -11.666000},
    {6.254000, -11.666000},
    {6.254000, -14.456000},
    {14.401000, -14.456000},
    {14.401000, 6.341000},
    {13.400000, 6.341000},
    {13.400000, 7.540000},
    {3.584000, 7.540000},
    {3.584000, 5.859000},
    {1.065000, 5.859000},
    {1.065000, 6.007000},
    {-1.123000, 6.007000},
    {-1.123000, 9.817000},
    {-9.271000, 9.817000}
}
local upper = {
    {-9.271000, -12.000000},
    {-8.270000, -12.000000},
    {-8.270000, -13.199000},
    {1.546000, -13.199000},
    {1.546000, -11.518000},
    {4.722000, -11.518000},
    {4.722000, -11.666000},
    {6.254000, -11.666000},
    {6.254000, -15.978000},
    {14.401000, -15.978000},
    {14.401000, 6.341000},
    {13.400000, 6.341000},
    {13.400000, 7.540000},
    {3.584000, 7.540000},
    {3.584000, 5.859000},
    {1.065000, 5.859000},
    {1.065000, 6.007000},
    {-1.123000, 6.007000},
    {-1.123000, 9.727000},
    {-9.271000, 9.727000}
}
local controlledPed = nil
local function contains(poly, x, y)
    local inside, j = false, #poly
    for i=1,#poly do
        local a,b = poly[i],poly[j]
        if (a[2]>y) ~= (b[2]>y) and x < (b[1]-a[1])*(y-a[2])/(b[2]-a[2])+a[1] then
            inside = not inside
        end
        j = i
    end
    return inside
end
local function restorePace()
    if controlledPed and DoesEntityExist(controlledPed) then
        SetPedMaxMoveBlendRatio(controlledPed, 3.0)
    end
    controlledPed = nil
end
CreateThread(function()
    while true do
        local ped = PlayerPedId()
        local p = GetEntityCoords(ped)-origin
        local disabled = GetEntityCollisionDisabled(ped)
        local foot = IsPedOnFoot(ped)
        local onFoot = (foot == true or foot == 1) and not (disabled == true or disabled == 1)
        local inside = onFoot and p.z >= -1.2 and p.z <= 6.7
            and contains(p.z < 2.5 and ground or upper,p.x,p.y)
        if controlledPed and (controlledPed ~= ped or not inside) then restorePace() end
        if inside then
            controlledPed = ped
            DisableControlAction(0, 21, true) -- sprint
            SetPedMaxMoveBlendRatio(ped, 1.35) -- walking through a gentle jog
        end
        Wait(0)
    end
end)
AddEventHandler('onResourceStop', function(name)
    if name == GetCurrentResourceName() then restorePace() end
end)
