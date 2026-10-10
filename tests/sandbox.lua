local commands,events={},{}
local clockCalls,weatherCalls,weaponCalls=0,0,0
local animation,cleared=false,false
function RegisterCommand(n,f) commands[n]=f end
function AddEventHandler(n,f) events[n]=f end
function TriggerEvent(n) if events[n] then events[n]() end end
function CreateThread() end
function PlayerPedId() return 1 end
function GetResourceState() return 'stopped' end
function IsEntityDead() return false end
function IsEntityInAir() return false end
function IsPedInAnyVehicle() return false end
function joaat(n) return n end
function IsWeaponValid(n) return n=='WEAPON_PISTOL' end
function GiveWeaponToPed(_,hash,ammo) weaponCalls=weaponCalls+1; assert(hash=='WEAPON_PISTOL' and ammo==120) end
function NetworkOverrideClockTime(h,m) clockCalls=clockCalls+1; assert(h>=0 and h<=23 and m>=0 and m<=59) end
function SetWeatherTypeNowPersist(n) weatherCalls=weatherCalls+1; assert(n=='RAIN') end
function GetGameTimer() return 1000 end
function HasAnimDictLoaded() return true end
function TaskPlayAnim() animation=true end
function ClearPedTasks() cleared=true end
for _,n in ipairs({'BeginTextCommandThefeedPost','AddTextComponentSubstringPlayerName','EndTextCommandThefeedPostTicker','RequestAnimDict','RemoveAnimDict','SetCurrentPedWeapon','RemoveAllPedWeapons','NetworkClearClockTimeOverride','PauseClock','ClearOverrideWeather','ClearWeatherTypePersist'}) do _G[n]=function() end end
dofile('server-data/resources/cidade_core/sandbox.lua')
commands.arma(0,{'pistola','120'}); assert(weaponCalls==1)
commands.arma(0,{'pistola','nan'}); commands.arma(0,{'pistola','-1'}); commands.arma(0,{'fake','120'}); assert(weaponCalls==1)
commands.hora(0,{'24','0'}); commands.hora(0,{'12','60'}); assert(clockCalls==0)
commands.hora(0,{'18','30'}); commands.dia(); commands.tarde(); commands.noite(); assert(clockCalls==4)
commands.clima(0,{'invalido'}); assert(weatherCalls==0)
commands.clima(0,{'chuva'}); assert(weatherCalls==1)
commands.deitar(); assert(animation)
commands.levantar(); assert(cleared)
print('OK: weapons, invalid inputs, time bounds, weather aliases, lie down/stand up')
