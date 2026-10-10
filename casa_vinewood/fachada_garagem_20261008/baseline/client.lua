local origin = vector3(-976.101013, 676.730896, 157.835037)
local entry = origin + vector3(5.80, -13.32, 0.40)
local function message(text)
    print('[Mansao] '..text)
    BeginTextCommandThefeedPost('STRING')
    AddTextComponentSubstringPlayerName(text)
    EndTextCommandThefeedPostTicker(false, false)
end

-- Streaming is requested before teleporting; normal entrance remains walkable.
RegisterCommand('mansao', function()
    -- Existing core hook restores ped collision and ends free flight.
    TriggerEvent('cidade:preparePilot')
    TriggerEvent('cidade:stopProne')
    local ped = PlayerPedId()
    if IsPedInAnyVehicle(ped, false) then
        message('Saia do veiculo para visitar a casa a pe.')
        return
    end
    RequestCollisionAtCoord(entry.x, entry.y, entry.z)
    NewLoadSceneStartSphere(entry.x, entry.y, entry.z, 65.0, 0)
    local deadline = GetGameTimer() + 5000
    while not IsNewLoadSceneLoaded() and GetGameTimer() < deadline do Wait(0) end
    SetEntityCoordsNoOffset(ped, entry.x, entry.y, entry.z, false, false, false)
    SetEntityHeading(ped, 270.0)
    deadline = GetGameTimer() + 3000
    FreezeEntityPosition(ped, true)
    while not HasCollisionLoadedAroundEntity(ped) and GetGameTimer() < deadline do
        RequestCollisionAtCoord(entry.x, entry.y, entry.z)
        Wait(0)
    end
    FreezeEntityPosition(ped, false)
    NewLoadSceneStop()
    message('Entrada a sua frente. Caminhe pela porta para explorar os dois andares.')
end, false)

-- Visible ceiling fixtures and stair LEDs: iluminacao_decorativa.lua.

-- The native exterior has no interior and can occlude the entire room when the
-- camera crosses its original visibility volumes. Disable those occluders only
-- around this house, including third-person cameras just outside the facade.
-- This native lasts one frame, so ordinary occlusion resumes when leaving.
local function inMansionView(q)
    local p = q-origin
    return p.x >= -12.5 and p.x <= 17.0
        and p.y >= -18.5 and p.y <= 12.0
        and p.z >= -2.0 and p.z <= 9.0
end
CreateThread(function()
    while true do
        if inMansionView(GetGameplayCamCoord()) or inMansionView(GetEntityCoords(PlayerPedId())) then
            DisableOcclusionThisFrame()
        end
        -- Check every frame to cover entry and free-camera movement without a
        -- delayed activation or a frame of flicker at an exterior doorway.
        Wait(0)
    end
end)
