-- A rectangular radius would also shelter the deck and the house's recesses.
-- Use the surveyed ground/upper footprints and actual floor/ceiling heights.
CidadeClimaInterior={}
local M=CidadeClimaInterior
function M.contains(p,polygon,margin)
    local inside=false; local minDistance=math.huge
    for i,a in ipairs(polygon) do
        local b=polygon[i%#polygon+1]
        if (a[2]>p[2])~=(b[2]>p[2]) and p[1]<(b[1]-a[1])*(p[2]-a[2])/(b[2]-a[2])+a[1] then inside=not inside end
        local dx,dy=b[1]-a[1],b[2]-a[2]; local length=dx*dx+dy*dy
        local t=length>0 and math.max(0,math.min(1,((p[1]-a[1])*dx+(p[2]-a[2])*dy)/length)) or 0
        minDistance=math.min(minDistance,math.sqrt((p[1]-a[1]-t*dx)^2+(p[2]-a[2]-t*dy)^2))
    end
    return inside or minDistance<=(margin or 0)
end
function M.sheltered(c,world,wasInside)
    local p={world[1]-c.origin[1],world[2]-c.origin[2],world[3]-c.origin[3]}
    local margin=wasInside and c.edge_hysteresis_m or 0
    if p[3]<c.floor_z-margin or p[3]>c.ceiling_z+margin then return false end
    return M.contains(p,p[3]>=c.upper_z and c.upper_polygon or c.ground_polygon,margin)
end
