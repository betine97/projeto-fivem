import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=R/'server-data/resources/cidade_mansao'
spec=json.loads((W/'encaixe_fachada.json').read_text())
def literal(poly):return '{\n'+',\n'.join('    {%.6f, %.6f}'%tuple(p) for p in poly)+'\n}'
source="""-- Keep the ordinary GTA locomotion and follow camera, with a gentle indoor pace.
local origin = vector3(-976.101013, 676.730896, 157.835037)
local ground = GROUND
local upper = UPPER
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
""".replace('GROUND',literal(spec['ground_polygon'])).replace('UPPER',literal(spec['upper_polygon']))
(D/'movimento_interior.lua').write_text(source,encoding='utf-8')
f=D/'fxmanifest.lua';s=f.read_text()
if "client_script 'movimento_interior.lua'" not in s:s+="\nclient_script 'movimento_interior.lua'\n"
f.write_text(s,encoding='utf-8')
for name in ('auditoria_client.lua','auditoria_server.lua'):
 f=D/name;s=f.read_text().replace('juntas-oclusao-2026-10-07','acabamentos-camera-2026-10-07');f.write_text(s,encoding='utf-8')
print('INDOOR_MOVEMENT_INSTALLED')
