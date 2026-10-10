local changing = false
local function notify(text)
    print('[Personagem] ' .. text)
    BeginTextCommandThefeedPost('STRING')
    AddTextComponentSubstringPlayerName(text)
    EndTextCommandThefeedPostTicker(false, false)
end

local function changeCharacter(model, silent)
    if changing then return false end
    local ped = PlayerPedId()
    if IsEntityDead(ped) or IsPedInAnyVehicle(ped, false) then
        notify('Fique de pe e fora do veiculo para trocar de personagem.')
        return false
    end
    if GetResourceState('fpv_drone_runtime') == 'started' and exports.fpv_drone_runtime:isPiloting() then
        notify('Use dronedesligar antes de trocar de personagem.')
        return false
    end
    changing = true
    local hash = type(model) == 'number' and model or joaat(model)
    if not IsModelInCdimage(hash) or not IsModelAPed(hash) then
        changing = false
        notify('Modelo ainda nao carregado: ' .. tostring(model) .. '. Reconecte apos a atualizacao da cidade.')
        return false
    end
    RequestModel(hash)
    local deadline = GetGameTimer() + 15000
    while not HasModelLoaded(hash) and GetGameTimer() < deadline do Wait(50) end
    if not HasModelLoaded(hash) then
        SetModelAsNoLongerNeeded(hash)
        changing = false
        notify('Nao foi possivel carregar o personagem. Tente novamente.')
        return false
    end
    TriggerEvent('cidade:stopProne')
    TriggerEvent('cidade:preparePilot')
    Wait(100)
    ped = PlayerPedId()
    if IsEntityDead(ped) or IsPedInAnyVehicle(ped, false) then
        SetModelAsNoLongerNeeded(hash)
        changing = false
        return false
    end
    local health, armour = GetEntityHealth(ped), GetPedArmour(ped)
    local maxHealth = GetEntityMaxHealth(ped)
    local heading, position = GetEntityHeading(ped), GetEntityCoords(ped)
    local selected = GetSelectedPedWeapon(ped)
    local weapons = {}
    for _, weapon in ipairs({selected, 'WEAPON_PISTOL', 'WEAPON_COMBATPISTOL', 'WEAPON_SMG', 'WEAPON_ASSAULTRIFLE', 'WEAPON_CARBINERIFLE', 'WEAPON_SPECIALCARBINE', 'WEAPON_COMBATMG', 'WEAPON_PUMPSHOTGUN', 'WEAPON_SNIPERRIFLE', 'WEAPON_RPG', 'WEAPON_KNIFE', 'WEAPON_GRENADE'}) do
        local weaponHash = type(weapon) == 'string' and joaat(weapon) or weapon
        if weaponHash and HasPedGotWeapon(ped, weaponHash, false) then
            weapons[#weapons + 1] = {hash = weaponHash, ammo = GetAmmoInPedWeapon(ped, weaponHash)}
        end
    end
    SetPlayerModel(PlayerId(), hash)
    ped = PlayerPedId()
    SetPedDefaultComponentVariation(ped)
    if model == 'cartelking' then
        for _, component in ipairs({0, 2, 3, 4, 11}) do
            SetPedComponentVariation(ped, component, 0, 0, 0)
        end
    end
    ClearAllPedProps(ped)
    SetEntityCoordsNoOffset(ped, position.x, position.y, position.z, false, false, false)
    SetEntityHeading(ped, heading)
    SetEntityMaxHealth(ped, maxHealth)
    SetEntityHealth(ped, health)
    SetPedArmour(ped, armour)
    for _, weapon in ipairs(weapons) do GiveWeaponToPed(ped, weapon.hash, weapon.ammo, false, false) end
    SetCurrentPedWeapon(ped, selected, true)
    SetModelAsNoLongerNeeded(hash)
    changing = false
    if not silent then
        notify(model == 'cartelking' and 'Cartel King ativo. personagemoriginal volta ao anterior.' or 'Personagem original restaurado.')
    end
    return true
end

exports('changeCharacter', changeCharacter)

RegisterCommand('cartelking', function() changeCharacter('cartelking') end, false)
RegisterCommand('personagemoriginal', function() changeCharacter('a_m_y_business_01') end, false)
