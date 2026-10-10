-- The map copies exclude this palm. Also exclude cached/original placements
-- from the base game when another map layer streams back in.
local removals = {
    {x=-963.682251,y=692.875488,z=155.982544,model='prop_palm_sm_01d'},
    {x=-963.682251,y=692.875488,z=156.728180,model='ch2_props_combo0126_11_lod'},
    {x=-962.070984,y=692.630920,z=155.982544,model='prop_palm_sm_01d'},
    {x=-962.070984,y=692.630920,z=156.728180,model='ch2_props_combo0126_11_lod'}
}
local running=true
local function exclude()
    for _,r in ipairs(removals) do
        CreateModelHideExcludingScriptObjects(r.x,r.y,r.z,1.25,GetHashKey(r.model),true)
    end
end
CreateThread(function()
    exclude()
    while running do
        Wait(5000)
        if running then
            local p=GetEntityCoords(PlayerPedId())
            local dx,dy=p.x+962.070984,p.y-692.630920
            if dx*dx+dy*dy<250*250 then exclude() end
        end
    end
end)
AddEventHandler('onResourceStop',function(name)
    if name~=GetCurrentResourceName() then return end
    running=false
    for _,r in ipairs(removals) do
        RemoveModelHide(r.x,r.y,r.z,1.25,GetHashKey(r.model),false)
    end
end)
