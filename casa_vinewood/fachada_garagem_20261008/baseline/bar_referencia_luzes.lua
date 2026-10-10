-- Four local fill lights for the actual recessed bar/painting LED strips.
-- This supplements the room controller without changing its settings/budget.
local origin=vector3(-976.1010131835938,676.7308959960938,157.8350372314453)
local lights={
    {position=vector3(7.71,-13.855,2.245),range=2.05,intensity=1.35},
    {position=vector3(7.71,-13.855,1.395),range=1.80,intensity=1.10},
    {position=vector3(7.71,-13.855,.765),range=1.80,intensity=1.10},
    {position=vector3(10.82,-14.03,2.21),range=1.95,intensity=.95},
}
CreateThread(function()
    local fade=0.0
    while true do
        local p=GetEntityCoords(PlayerPedId())-origin
        local near=#(p-vector3(9.35,-13.8,.6))<16.0 and p.z<2.6
        if near or fade>0 then
            fade=math.max(0.0,math.min(1.0,fade+(near and 1 or -1)*GetFrameTime()*3.0))
            for _,l in ipairs(lights) do
                local q=origin+l.position
                DrawLightWithRange(q.x,q.y,q.z,255,211,154,l.range,l.intensity*fade)
            end
            Wait(0)
        else Wait(750) end
    end
end)
