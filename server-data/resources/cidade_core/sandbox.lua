-- Comandos da cidade; armas dependem da autorizacao ADM validada pelo servidor.
local function say(text)
    print('[Cidade] '..text)
    BeginTextCommandThefeedPost('STRING'); AddTextComponentSubstringPlayerName(text)
    EndTextCommandThefeedPostTicker(false,false)
end
local function integer(value,minimum,maximum)
    local n=tonumber(value)
    return n and n==n and n==math.floor(n) and n>=minimum and n<=maximum and n or nil
end
local function piloting()
    return GetResourceState('fpv_drone_runtime')=='started' and exports.fpv_drone_runtime:isPiloting()
end
local lying=false
local animationPending=false
local generation=0
local dict='amb@world_human_sunbathe@male@back@base'
local function stand()
    generation=generation+1
    animationPending=false
    if lying then ClearPedTasks(PlayerPedId()); lying=false end
end
RegisterCommand('levantar',function() stand(); TriggerEvent('cidade:stopProne') end,false)
RegisterCommand('deitar',function()
    if lying or animationPending then stand(); return end
    local ped=PlayerPedId()
    if piloting() or IsEntityDead(ped) or IsPedInAnyVehicle(ped,false) or IsEntityInAir(ped) then
        say('Para deitar, fique a pe no chao e encerre a pilotagem do drone.'); return
    end
    TriggerEvent('cidade:preparePilot')
    local token=generation
    animationPending=true
    RequestAnimDict(dict)
    local deadline=GetGameTimer()+5000
    while not HasAnimDictLoaded(dict) and GetGameTimer()<deadline and token==generation do Wait(20) end
    animationPending=false
    if token~=generation then return end
    if not HasAnimDictLoaded(dict) then say('Animacao nao carregou.'); return end
    if IsEntityDead(ped) or piloting() or IsPedInAnyVehicle(ped,false) then return end
    TaskPlayAnim(ped,dict,'base',4.0,-4.0,-1,1,0.0,false,false,false)
    lying=true
    RemoveAnimDict(dict)
    say('Deitado. Use levantar ou deitar novamente para levantar.')
end,false)
AddEventHandler('cidade:preparePilot',stand)

local aliases={pistola='PISTOL',carabina='CARBINERIFLE',fuzil='ASSAULTRIFLE',smg='SMG',escopeta='PUMPSHOTGUN',sniper='SNIPERRIFLE',faca='KNIFE',lanterna='FLASHLIGHT'}
local function giveAdminWeapon(name,ammo)
    local args={name,tostring(ammo)}
    local name=args[1]
    if not name then say('arma pistola 120 | carabina | fuzil | smg | escopeta | sniper | faca'); return end
    if piloting() or IsEntityDead(PlayerPedId()) then say('Encerre a pilotagem ou use reviver primeiro.'); return end
    name=aliases[name:lower()] or name:upper()
    if name:sub(1,7)~='WEAPON_' then name='WEAPON_'..name end
    local hash=joaat(name)
    local ammo=integer(args[2] or '120',0,9999)
    if not ammo then say('Municao: inteiro entre 0 e 9999.'); return end
    if not IsWeaponValid(hash) then say('Arma inexistente: '..name); return end
    GiveWeaponToPed(PlayerPedId(),hash,ammo,false,true)
    SetPedAmmo(PlayerPedId(),hash,ammo)
    SetCurrentPedWeapon(PlayerPedId(),hash,true)
    TriggerEvent('cidade:weaponChanged')
    say(name..' entregue com '..ammo..' municoes.')
end
RegisterCommand('arma',function(_,args)
    if not args[1] or #args>2 then say('Use arma NOME [municao]. Use armas para o catalogo.');return end
    local ammo=integer(args[2] or '120',0,9999)
    if not ammo then say('Municao: inteiro entre 0 e 9999.');return end
    TriggerServerEvent('cidade_admin:equipment','weapon',args[1],ammo)
end,false)
AddEventHandler('cidade_core:adminWeapon',function(name,ammo)
    if GetInvokingResource()=='cidade_admin' then giveAdminWeapon(name,ammo) end
end)
RegisterCommand('desarmar',function()
    TriggerServerEvent('cidade_admin:equipment','disarm')
end,false)
AddEventHandler('cidade_core:adminDisarm',function()
    if GetInvokingResource()~='cidade_admin' then return end
    RemoveAllPedWeapons(PlayerPedId(),true)
    TriggerEvent('cidade:weaponChanged')
    say('Armas removidas.')
end)

local hour,minute=12,0
local locked=false
local managed=false
local function applyTime(h,m)
    hour,minute=h,m; managed=true; locked=true
    NetworkOverrideClockTime(h,m,0)
    say(('Horario: %02d:%02d (fixo). Use tempolivre para retomar o ciclo.'):format(h,m))
end
RegisterCommand('dia',function() applyTime(12,0) end,false)
RegisterCommand('tarde',function() applyTime(17,0) end,false)
RegisterCommand('noite',function() applyTime(23,0) end,false)
RegisterCommand('hora',function(_,args)
    local h,m=integer(args[1],0,23),integer(args[2] or '0',0,59)
    if not h or not m then say('Use hora HH MM, por exemplo hora 18 30.'); return end
    applyTime(h,m)
end,false)
RegisterCommand('tempolivre',function()
    managed=false; locked=false; NetworkClearClockTimeOverride(); PauseClock(false)
    say('Ciclo natural de horario retomado.')
end,false)
local darkNight,darkNightApplied=false,false
RegisterCommand('noiteescura',function()
    darkNight=not darkNight
    say(darkNight and 'Noites mais escuras ativadas. O efeito acompanha o horario.' or 'Noites mais escuras desativadas.')
end,false)
CreateThread(function()
    while true do
        local h=GetClockHours()
        local shouldApply=darkNight and (h>=21 or h<5)
        if shouldApply and not darkNightApplied then
            SetExtraTimecycleModifier('MP_deathfail_night')
            SetExtraTimecycleModifierStrength(0.38)
            darkNightApplied=true
        elseif not shouldApply and darkNightApplied then
            ClearExtraTimecycleModifier()
            darkNightApplied=false
        end
        Wait(1000)
    end
end)
local weatherAliases={sol='EXTRASUNNY',limpo='CLEAR',nublado='CLOUDS',encoberto='OVERCAST',chuva='RAIN',tempestade='THUNDER',neblina='FOGGY',neve='XMAS'}
local validWeather={EXTRASUNNY=true,CLEAR=true,CLOUDS=true,OVERCAST=true,RAIN=true,THUNDER=true,FOGGY=true,SMOG=true,CLEARING=true,SNOW=true,SNOWLIGHT=true,BLIZZARD=true,XMAS=true}
local selectedWeather
local function weather(_,args)
    local name=args[1] or ''
    if name:lower()=='automatico' then
        selectedWeather=nil; ClearOverrideWeather(); ClearWeatherTypePersist()
        say('Clima automatico.'); return
    end
    name=weatherAliases[name:lower()] or name:upper()
    if not validWeather[name] then say('clima sol | nublado | chuva | tempestade | neblina | neve | automatico'); return end
    selectedWeather=name
    ClearOverrideWeather(); SetWeatherTypeNowPersist(name)
    say('Clima: '..name)
end
RegisterCommand('clima',weather,false)
RegisterCommand('tempo',weather,false)
CreateThread(function()
    while true do
        if managed and locked then NetworkOverrideClockTime(hour,minute,0) end
        if selectedWeather then SetWeatherTypeNowPersist(selectedWeather) end
        Wait(1000)
    end
end)
AddEventHandler('onResourceStop',function(name)
    if name~=GetCurrentResourceName() then return end
    stand()
    if managed then NetworkClearClockTimeOverride() end
    if selectedWeather then ClearOverrideWeather(); ClearWeatherTypePersist() end
    if darkNightApplied then ClearExtraTimecycleModifier();darkNightApplied=false end
end)
