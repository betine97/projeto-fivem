local resource = GetCurrentResourceName()
local config = json.decode(LoadResourceFile(resource, 'portas_madeira.json'))
local doorsById, states, headings, lastToggle, doorBusy = {}, {}, {}, {}, {}
for _, d in ipairs(config.doors) do doorsById[d.id]=d; states[d.id]=false; headings[d.id]=d.open_heading end
local origin = config.origin
local function localPos(p)
    return p.x-origin[1],p.y-origin[2],p.z-origin[3]
end
local function awayHeading(d,x,y)
    -- Use the actual leaf direction; the main entrance extends +X while
    -- the other models extend -X in hinge space.
    local h,c=d.hinge,d.opening_center
    local vx,vy=c[1]-h[1],c[2]-h[2]
    local side=-vy*(x-c[1])+vx*(y-c[2])
    local swing=d.swing_degrees or math.abs(d.open_heading-d.closed_heading)
    if math.abs(side)<.025 then return d.open_heading end
    return d.closed_heading+(side>0 and -swing or swing)
end
local function swept(d,x,y,from,to)
    local h,c=d.hinge,d.opening_center
    local vx,vy=c[1]-h[1],c[2]-h[2];local length=math.sqrt(vx*vx+vy*vy)
    vx,vy=vx/length,vy/length
    -- Sample the full arc with a pedestrian margin; spacing is under 5 cm.
    for i=0,40 do
        local r=math.rad(from+(to-from)*i/40-d.closed_heading)
        local ex=(vx*math.cos(r)-vy*math.sin(r))*d.width_m
        local ey=(vx*math.sin(r)+vy*math.cos(r))*d.width_m
        local px,py=x-h[1],y-h[2]
        local t=math.max(0,math.min(1,(px*ex+py*ey)/(ex*ex+ey*ey)))
        local dx,dy=px-t*ex,py-t*ey
        if dx*dx+dy*dy<.30*.30 then return true end
    end
    return false
end
RegisterNetEvent('cidade_mansao:requestDoorStates',function()
    TriggerClientEvent('cidade_mansao:doorStates',source,states,headings)
end)
RegisterNetEvent('cidade_mansao:toggleDoor',function(id)
    local player=source
    if type(id)~='number' or id%1~=0 or not doorsById[id] then return end
    local now=GetGameTimer()
    if (lastToggle[player] and now-lastToggle[player]<650) or (doorBusy[id] and now-doorBusy[id]<650) then return end
    local d,ped=doorsById[id],GetPlayerPed(player)
    if ped==0 then return end
    local x,y,z=localPos(GetEntityCoords(ped));local c=d.opening_center
    if (x-c[1])^2+(y-c[2])^2+(z-c[3])^2>2.7^2 then return end
    local opened=not states[id]
    local target=opened and awayHeading(d,x,y) or d.closed_heading
    local from=states[id] and headings[id] or d.closed_heading
    for _,other in ipairs(GetPlayers()) do
        local q=GetPlayerPed(other)
        if q~=0 then
            local ox,oy,oz=localPos(GetEntityCoords(q))
            if oz>d.hinge[3] and oz<d.hinge[3]+d.height_m+1 then
                local b=d.opening_bounds
                local inOpening=not opened and ox>b[1]-.30 and ox<b[2]+.30 and oy>b[3]-.35 and oy<b[4]+.35
                if inOpening or swept(d,ox,oy,from,target) then
                    TriggerClientEvent('cidade_mansao:doorOccupied',player)
                    return
                end
            end
        end
    end
    lastToggle[player]=now;doorBusy[id]=now
    states[id]=opened
    if opened then headings[id]=target end
    TriggerClientEvent('cidade_mansao:doorState',-1,id,opened,headings[id])
end)
AddEventHandler('playerDropped',function() lastToggle[source]=nil end)
