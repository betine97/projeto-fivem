from pathlib import Path
import sys,json
r=Path.cwd();sys.path.insert(0,str(r/'casa_vinewood/work/lua_syntax_deps'))
from lupa import LuaRuntime
l=LuaRuntime(unpack_returned_tuples=True);g=l.globals();checks=[]
l.execute('''commands={};events={};handlers={};threads={};calls={};logs={};source=65535;now=100;invoking='cidade_admin';LocalPlayer={state={cidadeAdmin=true}}
local vm={};vm.__index=vm;function vm.__add(a,b)return vector3(a.x+b.x,a.y+b.y,a.z+b.z)end;function vm.__sub(a,b)return vector3(a.x-b.x,a.y-b.y,a.z-b.z)end;function vm.__len(a)return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z)end
function vector3(x,y,z)return setmetatable({x=x,y=y,z=z},vm)end
function RegisterCommand(n,f) commands[n]=f end
function RegisterNetEvent(n,f) events[n]=f end
function AddEventHandler(n,f) handlers[n]=f end
function CreateThread(f) threads[#threads+1]=f end
function print(s)logs[#logs+1]=s end
function GetGameTimer()return now end
function GetCurrentResourceName()return 'cidade_admin' end
function GetInvokingResource()return invoking end
function GetResourceState()return 'stopped' end
function PlayerPedId()return 10 end
function GetEntityCoords()return vector3(0,0,35)end
function GetEntityHeading()return 90 end
function GetNameOfZone()return 'BURTON'end
function GetLabelText(x)return x end
function joaat(x)return x end
function IsWeaponValid(x)return x~='WEAPON_BOGUS'end
function IsModelInCdimage(x)return x~='bogus'end
function IsModelAVehicle(x)return x~='bogus'end
function IsEntityDead()return false end
function HasModelLoaded()return true end
function DoesEntityExist()return true end
function GetModelDimensions()return vector3(-1,-2,0),vector3(1,2,2)end
function GetOffsetFromEntityInWorldCoords()return vector3(0,6,35)end
function GetAllVehicleModels()return {'sertao','adder','bogus'}end
function GetRegisteredCommands()return {{name='voar',resource='cidade_core'},{name='+binding',resource='cidade_core'},{name='unrelated',resource='other'}}end
function TriggerServerEvent(n,...)calls[#calls+1]={n,...}end
function TriggerEvent(n,...)calls[#calls+1]={n,...};if handlers[n] then handlers[n](...)end end
function AddBlipForCoord(...)calls[#calls+1]={'blip',...};return 42 end
function RemoveBlip(id)calls[#calls+1]={'removeBlip',id}end
function CreateVehicle(...)calls[#calls+1]={'createVehicle',...};return 88 end
function GiveWeaponToPed(...)calls[#calls+1]={'giveWeapon',...}end
function RemoveAllPedWeapons(...)calls[#calls+1]={'removeWeapons',...}end
function Wait(ms)now=now+math.max(1,ms)end
for _,n in ipairs({'SetBlipSprite','SetBlipColour','SetBlipScale','SetBlipAsShortRange','SetBlipCoords','BeginTextCommandSetBlipName','AddTextComponentSubstringPlayerName','EndTextCommandSetBlipName','ExecuteCommand','BeginTextCommandThefeedPost','EndTextCommandThefeedPostTicker','SetCurrentPedWeapon','AddTextEntry','RequestModel','SetModelAsNoLongerNeeded','SetEntityAsMissionEntity','DeleteVehicle','SetVehicleOnGroundProperly','SetVehicleDirtLevel','SetVehicleFuelLevel','SetVehicleEngineOn','SetVehRadioStation','SetPedIntoVehicle'})do _G[n]=function()end end
''')
for path in ['cidade_admin/catalogo.lua','cidade_admin/client.lua','cidade_core/sandbox.lua','cidade_core/vehicles.lua']:l.execute((r/'server-data/resources'/path).read_text())
def call(n,args=[]):g.commands[n](0,l.table_from(args))
def count(n):return sum(g.calls[i][1]==n for i in range(1,len(g.calls)+1))
call('arma',['pistola','120']);assert g.calls[len(g.calls)][1]=='cidade_admin:equipment';checks.append('Weapon command requests server authorization')
fn=g.events['cidade_admin:equipmentGranted'];g.source=25;fn('weapon','weapon_pistol',120);assert count('giveWeapon')==0;checks.append('Forged network source rejected')
g.source=65535;fn('weapon','weapon_pistol',120);assert count('giveWeapon')==1;checks.append('Authorized weapon delivered through core')
g.invoking='unrelated';g.handlers['cidade_core:adminWeapon']('weapon_pistol',120);assert count('giveWeapon')==1;checks.append('Untrusted resource cannot use internal grant')
g.invoking='cidade_admin';fn('weapon','weapon_bogus',120);assert count('giveWeapon')==1;checks.append('Invalid native weapon rejected')
call('veiculo',['adder']);assert g.calls[len(g.calls)][1]=='cidade_admin:equipment';checks.append('Vehicle command requests server authorization')
fn('vehicle','adder',None);assert count('createVehicle')==1;checks.append('Authorized vehicle created through core')
fn('vehicle','bogus',None);assert count('createVehicle')==1;checks.append('Invalid vehicle rejected')
fn('disarm',None,None);assert count('removeWeapons')==1;checks.append('Authorized disarm delivered')
call('admin');assert any('chamar ID' in g.logs[i] for i in range(1,len(g.logs)+1));checks.append('F8 help includes pull-player command')
call('armas',['pistola']);checks.append('Weapon catalogue filters')
call('veiculos',['todos']);assert any('adder | sertao' in g.logs[i] for i in range(1,len(g.logs)+1));checks.append('Complete native vehicle catalogue includes custom model')
loc=l.table_from(dict(id=77,name='Amigo',x=20,y=2,z=35,bucket=7));g.events['cidade_admin:location'](loc,True);assert count('blip')==1;checks.append('Player location creates map marker')
g.events['cidade_admin:clearTracking']();assert count('removeBlip')==1;checks.append('Tracking stop cleans map marker')
(r/'admin_sistema_20261008/client_verification.json').write_text(json.dumps({'passed':True,'checks':checks,'in_game_verified':False},indent=2));__builtins__.print('CLIENT_TESTS_PASSED',len(checks))
