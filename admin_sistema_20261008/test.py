from pathlib import Path
import sys,json
r=Path.cwd();sys.path.insert(0,str(r/'casa_vinewood/work/lua_syntax_deps'))
from lupa import LuaRuntime
from luaparser import ast
p=r/'admin_sistema_20261008';d=r/'server-data/resources/cidade_admin';tests=[]
for f in list(d.glob('*.lua'))+[r/'server-data/resources/cidade_acesso/server.lua',r/'server-data/resources/cidade_core/sandbox.lua',r/'server-data/resources/cidade_core/vehicles.lua']:ast.parse(f.read_text(encoding='utf-8-sig'));tests.append('syntax '+f.name)
l=LuaRuntime(unpack_returned_tuples=True);g=l.globals()
l.execute('''commands={};events={};handlers={};threads={};sent={};now=10000;source=10;allowed={[10]=true,[20]=true};records={[10]={source=10,id=1,name='Dono'},[20]={source=20,id=77,name='Amigo'}}
exports={cidade_acesso={}}
function exports.cidade_acesso:GetVerifiedRecord(id) return records[id] end
function exports.cidade_acesso:ResolvePermanentId(id) for _,r in pairs(records) do if r.id==id then return r end end end
function RegisterCommand(n,f,r) commands[n]={fn=f,restricted=r} end
function RegisterNetEvent(n,f) events[n]=f end
function AddEventHandler(n,f) handlers[n]=f end
function CreateThread(f) threads[#threads+1]=coroutine.create(f) end
function Wait(ms) coroutine.yield(ms) end
function GetCurrentResourceName() return 'cidade_admin' end
function GetResourceState() return 'started' end
function GetGameTimer() return now end
function GetPlayerPed(id) return id end
function DoesEntityExist(id) return true end
function GetEntityCoords(id) return {x=id,y=2,z=35} end
function GetEntityHeading(id) return 90 end
function GetPlayers() return {'10','20'} end
function GetPlayerRoutingBucket(id) return id==20 and 7 or 0 end
function IsPlayerAceAllowed(id,permission) return allowed[id]==true end
function TriggerClientEvent(n,id,...) sent[#sent+1]={name=n,id=id,args={...}} end
function GetRegisteredCommands() return {{name='encontrar',resource='cidade_acesso'},{name='chamar',resource='cidade_acesso'},{name='unrelated',resource='chat'}} end
''')
l.execute((d/'catalogo.lua').read_text());l.execute((d/'server.lua').read_text())
def last():return g.sent[len(g.sent)]
def command(n,id,args=[]):g.now+=3000;g.commands[n].fn(id,l.table_from(args))
command('jogadores',10);assert last()['name']=='cidade_admin:players';assert last()['args'][1][2]['id']==77;tests.append('Permanent ID player list')
command('jogadores',30);assert last()['name']=='cidade_acesso:notice';tests.append('Unapproved player rejected')
for bad in [['20'],['77','extra'],['-1'],['abc'],[]]:
 command('onde',10,bad);assert last()['name']=='cidade_acesso:notice';tests.append('Invalid/offline ID '+str(bad))
command('onde',10,['77']);assert last()['args'][1]['bucket']==7 and last()['args'][1]['x']==20;tests.append('Cross-instance coordinates')
command('rastrear',10,['77']);assert last()['args'][2] is True;l.execute('coroutine.resume(threads[1]);coroutine.resume(threads[1])');assert last()['name']=='cidade_admin:trackingTick';tests.append('Tracking updates')
command('onde',10,['77']);before=len(g.sent);l.execute('coroutine.resume(threads[1])');assert len(g.sent)==before;tests.append('One-off location cancels previous tracking')
command('rastrear',10,['77'])
g.allowed[10]=False;l.execute('coroutine.resume(threads[1])');assert last()['name']=='cidade_admin:clearTracking';tests.append('Revoked admin loses tracking')
g.allowed[10]=True
fn=g.events['cidade_admin:equipment']
def equip(action,name=None,ammo=None,id=10):g.now+=3000;g.source=id;fn(action,name,ammo)
equip('weapon','pistola',120);assert last()['args'][2]=='weapon_pistol';tests.append('Weapon alias normalized')
equip('weapon','WEAPON_CARBINERIFLE',120);assert last()['args'][2]=='weapon_carbinerifle';tests.append('Weapon native name normalized')
for bad in [-1,1.5,10000,float('nan')]:equip('weapon','pistola',bad);assert last()['name']=='cidade_acesso:notice';tests.append('Bad ammo rejected')
for bad in ['a b','a;restart','a'*65]:equip('vehicle',bad);assert last()['name']=='cidade_acesso:notice';tests.append('Bad model rejected')
equip('vehicle','ambulance');assert last()['name']=='cidade_admin:equipmentGranted';tests.append('Vehicle granted to caller only')
equip('vehicle','adder',id=30);assert last()['name']=='cidade_acesso:notice';tests.append('Unauthorized vehicle blocked')
equip('disarm');assert last()['args'][1]=='disarm';tests.append('Disarm authorized')
equip('deleteVehicle');assert last()['args'][1]=='deleteVehicle';tests.append('Vehicle delete authorized')
# Tracking account handles cannot transfer to another permanent ID.
command('rastrear',10,['77']);g.records[10]['id']=123;l.execute('coroutine.resume(threads[1])');assert last()['name']=='cidade_admin:clearTracking';tests.append('Reused session handle blocked')
for n in ['jogadores','onde','localizar','rastrear','comandosservidor']:assert g.commands[n]['restricted'] is True;tests.append('Server ACL '+n)
(p/'verification.json').write_text(json.dumps({'passed':True,'checks':tests,'in_game_verified':False},indent=2));print('ADMIN_TESTS_PASSED',len(tests))
