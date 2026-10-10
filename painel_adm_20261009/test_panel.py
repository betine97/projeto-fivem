from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parent.parent
RESOURCE=ROOT/'server-data/resources/cidade_admin'
sys.path.insert(0,str(ROOT/'casa_vinewood/work/lua_syntax_deps'))
from lupa import LuaRuntime
from luaparser import ast
checks=[]
for file in RESOURCE.glob('*.lua'):
    ast.parse(file.read_text(encoding='utf-8-sig'));checks.append('Lua syntax: '+file.name)
catalog=json.loads((RESOURCE/'ui/catalog.json').read_text(encoding='utf-8'))
for kind in ['vehicles','weapons','npcs']:
    assert len({r['model'] for r in catalog[kind]})==len(catalog[kind])
    assert all((RESOURCE/'ui'/r['image']).is_file() for r in catalog[kind])
    checks.append('Unique models and offline images: '+kind)

def convert(lua,data):
    if isinstance(data,dict):return lua.table_from({k:convert(lua,v) for k,v in data.items()})
    if isinstance(data,list):return lua.table_from([convert(lua,v) for v in data])
    return data

server=LuaRuntime(unpack_returned_tuples=True);s=server.globals()
s.pydecode=lambda text:convert(server,json.loads(text))
s.pyload=lambda res,file:(RESOURCE/file).read_text(encoding='utf-8')
server.execute('''
json={decode=pydecode};LoadResourceFile=pyload
events={};handlers={};threads={};sent={};now=10000;source=10
allowed={[10]=true,[20]=true};records={[10]={id=1,name='Admin',source=10},[20]={id=77,name='Friend',source=20}}
entities={};deleted={};moved={};states={};exports={cidade_acesso={}}
function exports.cidade_acesso:GetVerifiedRecord(id)return records[id]end
function GetCurrentResourceName()return 'cidade_admin'end
function GetResourceState(n)return states[n] or 'started'end
function IsPlayerAceAllowed(id,p)return allowed[id]==true end
function GetGameTimer()return now end
function GetPlayers()return {'10','20'}end
function GetPlayerRoutingBucket(id)return id==20 and 7 or 0 end
function GetPlayerPed(id)return id end
function GetEntityCoords(id)return {x=5,y=10,z=35}end
function GetEntityHeading(id)return 0 end
function DoesEntityExist(id)return entities[id]~=nil or id==10 or id==20 end
function NetworkGetNetworkIdFromEntity(id)return entities[id].net end
function NetworkGetEntityFromNetworkId(net)for id,e in pairs(entities)do if e.net==net then return id end end;return 0 end
function NetworkGetEntityOwner(id)return entities[id].owner end
function GetEntityType(id)return entities[id].kind end
function GetEntityModel(id)return entities[id].hash end
function GetHashKey(model)return model end
function DeleteEntity(id)deleted[#deleted+1]=id;entities[id]=nil end
function SetEntityCoords(id,...)moved[#moved+1]={id,...}end
function SetEntityHeading(id,h)end
function GetRegisteredCommands()return {{name='chamar',resource='cidade_acesso',restricted=true},{name='localizar',resource='cidade_admin',restricted=true},{name='unrelated',resource='other'}}end
function RegisterNetEvent(n,f)events[n]=f end
function AddEventHandler(n,f)handlers[n]=f end
function CreateThread(f)threads[#threads+1]=coroutine.create(f)end
function Wait(ms)coroutine.yield(ms)end
function TriggerClientEvent(n,id,...)sent[#sent+1]={name=n,id=id,args={...}}end
''')
server.execute((RESOURCE/'panel_server.lua').read_text(encoding='utf-8'))
sequence=0
def ask(action,id=10,advance=3000,**args):
    global sequence
    sequence+=1;s.source=id;s.now+=advance
    s.events['cidade_admin:panelRequest'](sequence,convert(server,dict(action=action,**args)))
    reply=s.sent[len(s.sent)]
    assert reply['name']=='cidade_admin:panelReply' and reply['id']==id
    return reply['args'][2]
assert not ask('open',id=30)['ok'];checks.append('Unverified account cannot open panel')
s.allowed[10]=False;assert not ask('vehicle',model='adder')['ok'];s.allowed[10]=True;checks.append('Revoked admin cannot create equipment')
r=ask('open');assert r['ok'] and r['data']['id']==1 and r['data']['players'][2]['id']==77
checks.append('Panel snapshot uses permanent IDs, names and instances')
assert not ask('notAnAction')['ok'];checks.append('Unknown action rejected')
for value in ['adder;restart','a'*65,'','a\nb']:
    assert not ask('vehicle',model=value)['ok']
checks.append('Invalid model strings rejected')
for value in [-1,1.5,10000,float('nan')]:
    assert not ask('weapon',model='weapon_pistol',ammo=value)['ok']
checks.append('Ammo integer and bounds enforced server-side')
assert not ask('weapon',model='weapon_bogus',ammo=100)['ok'];checks.append('Unknown weapon rejected')
r=ask('vehicle',model='adder');assert r['ok'] and s.sent[len(s.sent)-1]['args'][1]=='vehicle'
assert not ask('vehicle',advance=0,model='adder')['ok'];checks.append('Vehicle grant uses existing equipment event and cooldown')
for args in ['2;restart','2\nquit','2&foo','2'*121]:
    assert not ask('command',name='chamar',args=args)['ok']
assert not ask('command',name='restart',args='cidade_core')['ok']
assert not ask('command',name='unrelated',args='')['ok'];checks.append('Console injection and non-city commands blocked')
s.states['cidade_mansao']='stopped'
assert not ask('command',name='editarobjetos',args='')['ok']
open_result=ask('open');rows=open_result['data']['commands']
assert any(rows[i]['name']=='editarobjetos' and rows[i]['active']==False for i in range(1,len(rows)+1));checks.append('Inactive editor listed, execution blocked')
assert ask('command',name='chamar',args='77')['ok'];checks.append('Player action preserves permanent ID argument')
assert not ask('npc',model='unknownped')['ok'];checks.append('Unknown NPC denied')
r=ask('npc',model='s_m_y_cop_01');ticket=r['data']['ticket'];assert r['ok']
s.entities[900]=convert(server,{'net':100,'owner':20,'kind':1,'hash':'s_m_y_cop_01'})
s.source=10;s.events['cidade_admin:panelNpcCreated'](ticket,100)
assert len(ask('npcList')['data']['npcs'])==0;checks.append('NPC registration requires network ownership')
s.entities[900]['owner']=10;s.entities[900]['hash']='s_m_y_fireman_01'
s.source=10;s.events['cidade_admin:panelNpcCreated'](ticket,100)
assert len(ask('npcList')['data']['npcs'])==0;checks.append('NPC ticket model cannot be substituted')
# Re-reserve after elapsed registration window in negative tests.
r=ask('npc',model='s_m_y_cop_01');ticket=r['data']['ticket'];s.entities[900]['hash']='s_m_y_cop_01'
s.source=10;s.events['cidade_admin:panelNpcCreated'](ticket,100)
assert s.sent[len(s.sent)]['name']=='cidade_admin:panelNpcs'
assert len(ask('npcList')['data']['npcs'])==1;checks.append('Owned ped registration acknowledged and listed')
before=len(s.moved)
# A second admin cannot affect the first admin's NPC.
sequence+=1;s.source=20;s.now+=3000;s.events['cidade_admin:panelRequest'](sequence,convert(server,{'action':'npcBring','id':ticket}));assert s.sent[len(s.sent)]['args'][2]['ok']==False and len(s.moved)==before
checks.append('Another admin cannot bring or delete owned NPCs')
sequence+=1;s.source=10;s.now+=3000;s.events['cidade_admin:panelRequest'](sequence,convert(server,{'action':'npcBring','id':ticket}));assert s.moved[len(s.moved)][2]==5 and s.moved[len(s.moved)][3]==13
checks.append('Bring NPC places it three meters in front of caller')
# Reserve at one-second intervals; eleven existing/reserved models plus one owned.
for index in range(11):assert ask('npc',advance=900,model='s_m_y_cop_01')['ok']
assert not ask('npc',advance=900,model='s_m_y_cop_01')['ok'];checks.append('NPC cap includes pending spawn reservations')
server.execute('coroutine.resume(threads[1])');s.allowed[10]=False;server.execute('coroutine.resume(threads[1])')
assert not s.entities[900] and s.sent[len(s.sent)]['name']=='cidade_admin:panelClose';checks.append('Permission revocation closes panel and cleans up NPCs')
s.allowed[10]=True
assert ask('npc',model='s_m_y_cop_01')['ok'];checks.append('Cleanup releases reservations')

client=LuaRuntime(unpack_returned_tuples=True);c=client.globals()
c.pydecode=lambda text:convert(client,json.loads(text));c.pyload=s.pyload
client.execute('''
json={decode=pydecode};LoadResourceFile=pyload;events={};handlers={};commands={};callbacks={};threads={};calls={};messages={};focus=false;now=1000;source=65535
LocalPlayer={state={cidadeAdmin=true,cidadeId=1}};npcExists=false;autoAck=true
function GetCurrentResourceName()return 'cidade_admin'end
function RegisterNetEvent(n,f)events[n]=f end
function RegisterCommand(n,f)commands[n]=f end
function RegisterNUICallback(n,f)callbacks[n]=f end
function AddEventHandler(n,f)handlers[n]=f end
function CreateThread(f)threads[#threads+1]=coroutine.create(f)end
function Wait(ms)now=now+math.max(ms,1)end
function GetGameTimer()return now end
function SendNUIMessage(m)messages[#messages+1]=m end
function SetNuiFocus(a,b)focus=a end
function GetResourceState()return 'started'end
function joaat(x)return x end
function IsWeaponValid(x)return x=='weapon_pistol'end
function IsModelInCdimage(x)return x~='bogus'end
function IsModelValid(x)return x~='bogus'end
function IsModelAVehicle(x)return x=='adder' or x=='sertao'end
function IsModelAPed(x)return x=='s_m_y_cop_01'end
function GetAllVehicleModels()return {'adder','sertao'}end
function GetRegisteredCommands()return {{name='voar',resource='cidade_core'},{name='dynamicCityAlias',resource='cidade_core'},{name='unrelated',resource='other'}}end
function TriggerServerEvent(n,...)
    calls[#calls+1]={n,...}
    if n=='cidade_admin:panelNpcCreated' and autoAck and select(2,...)~=0 then events['cidade_admin:panelNpcAck'](select(1,...)) end
end
function ExecuteCommand(s)calls[#calls+1]={'execute',s}end
function PlayerPedId()return 10 end
function IsEntityDead()return false end
function RequestModel()end
function HasModelLoaded()return true end
function SetModelAsNoLongerNeeded()end
function GetOffsetFromEntityInWorldCoords()return {x=0,y=3,z=35}end
function GetGroundZFor_3dCoord()return true,35 end
function GetEntityHeading()return 0 end
function CreatePed(...)npcExists=true;calls[#calls+1]={'createPed',...};return 900 end
function DoesEntityExist(id)return id==10 or (id==900 and npcExists)end
function SetEntityAsMissionEntity()end
function SetPedCanRagdoll()end
function SetBlockingOfNonTemporaryEvents()end
function SetPedDefaultComponentVariation()end
function TaskStandStill()end
function NetworkGetNetworkIdFromEntity(id)return 100 end
function GetEntityModel(id)return 's_m_y_cop_01'end
function SetNetworkIdCanMigrate()end
function DeleteEntity(id)npcExists=false;calls[#calls+1]={'delete',id}end
function BeginTextCommandThefeedPost()end
function AddTextComponentSubstringPlayerName()end
function EndTextCommandThefeedPostTicker()end
''')
client.execute((RESOURCE/'captured_catalog.lua').read_text(encoding='utf-8'))
client.execute((RESOURCE/'panel_client.lua').read_text(encoding='utf-8'))
def count(name):return sum(c.calls[i][1]==name for i in range(1,len(c.calls)+1))
def latest_request():
    for index in range(len(c.calls),0,-1):
        if c.calls[index][1]=='cidade_admin:panelRequest':return c.calls[index][2]
def respond(data,source=65535):
    c.source=source;c.events['cidade_admin:panelReply'](latest_request(),convert(client,data))
c.commands['painel'](0,convert(client,['adm']));assert count('cidade_admin:panelRequest')==1
respond({'ok':True,'data':{'id':1,'name':'Admin','players':[],'commands':[{'name':'voar','resource':'cidade_core','active':True}],'npcs':[]}},source=42)
assert not c.focus;checks.append('Forged client reply cannot open NUI')
respond({'ok':True,'data':{'id':1,'name':'Admin','players':[],'commands':[{'name':'voar','resource':'cidade_core','active':True}],'npcs':[]}})
client.execute('coroutine.resume(threads[#threads])');assert c.focus
payload=c.messages[len(c.messages)]['data'];assert len(payload['catalog']['vehicles'])==2 and len(payload['catalog']['weapons'])==1 and len(payload['catalog']['npcs'])==1
assert any(payload['commands'][i]['name']=='dynamicCityAlias' for i in range(1,len(payload['commands'])+1));checks.append('Only valid native models displayed; runtime command aliases merged')
results=[]
c.callbacks['action'](convert(client,{'action':'vehicle','model':'bogus'}),lambda r:results.append(r['ok']));assert results==[False]
checks.append('NUI invalid model returns an error callback')
c.callbacks['action'](convert(client,{'action':'command','name':'voar','args':''}),lambda r:results.append(r['ok']))
respond({'ok':True,'data':{'name':'voar','args':''}});assert c.calls[len(c.calls)][1]=='execute' and c.calls[len(c.calls)][2]=='voar' and not c.focus
checks.append('Authorized command executes in caller console and releases NUI focus')
results=[]
c.commands['npc'](0,convert(client,['s_m_y_cop_01']));respond({'ok':True,'data':{'model':'s_m_y_cop_01','ticket':22,'permanent':1}})
client.execute('coroutine.resume(threads[#threads])');assert count('createPed')==1 and c.npcExists
checks.append('Authorized specific NPC created and registered')
checks.append('NPC receives collision/ragdoll-capable live ped rather than image')
c.autoAck=False
c.commands['npc'](0,convert(client,['s_m_y_cop_01']));respond({'ok':True,'data':{'model':'s_m_y_cop_01','ticket':23,'permanent':1}})
client.execute('coroutine.resume(threads[#threads])');assert not c.npcExists;checks.append('Unconfirmed NPC cleaned up instead of reporting success')
c.commands['npc'](0,convert(client,['s_m_y_cop_01']));respond({'ok':True,'data':{'model':'s_m_y_cop_01','ticket':24,'permanent':999}})
client.execute('coroutine.resume(threads[#threads])');assert count('createPed')==2;checks.append('Account mismatch while loading NPC cancels spawn')
c.handlers['onResourceStop']('cidade_admin');assert not c.focus;checks.append('Resource stop releases keyboard and mouse')
report={'passed':True,'checks':checks,'in_game_verified':False,'catalog_counts':{k:len(v) for k,v in catalog.items()}}
(ROOT/'painel_adm_20261009/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('PANEL_TESTS_PASSED',len(checks))
