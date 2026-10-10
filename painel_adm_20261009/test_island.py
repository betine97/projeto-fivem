"""Exercise server persistence, concurrency, authorization and client placement lifecycle."""
from pathlib import Path
import json,sys,math
R=Path(__file__).resolve().parent.parent;D=R/'server-data/resources/cidade_admin'
sys.path.insert(0,str(R/'casa_vinewood/work/lua_syntax_deps'))
from lupa import LuaRuntime
checks=[];catalog=json.loads((D/'ui/cayo.json').read_text(encoding='utf8'));model=catalog['objects'][0]['model']
assert len(set(x['model'] for x in catalog['objects']))==len(catalog['objects'])
assert all((D/'ui'/x['image']).is_file() for x in catalog['objects']);checks.append('Catalog models unique, thumbnails local')
def convert(lua,data):
    if isinstance(data,dict):return lua.table_from({k:convert(lua,v) for k,v in data.items()})
    if isinstance(data,list):return lua.table_from([convert(lua,v) for v in data])
    return data
def plain(data):
    if hasattr(data,'items'):
        items=dict(data.items())
        if all(isinstance(k,int) for k in items) and set(items)==set(range(1,len(items)+1)):return [plain(items[i]) for i in range(1,len(items)+1)]
        return {k:plain(v) for k,v in items.items()}
    return data
disk={};writes=[];fail=False
def server():
    lua=LuaRuntime(unpack_returned_tuples=True);g=lua.globals()
    g.pydecode=lambda t:convert(lua,json.loads(t));g.pyencode=lambda t:json.dumps(plain(t))
    g.pyload=lambda r,f:json.dumps(catalog) if f=='ui/cayo.json' else disk.get(f)
    def save(r,f,text,count):
        if fail:return False
        disk[f]=text;writes.append(f);return True
    g.pysave=save
    lua.execute('''
json={decode=pydecode,encode=pyencode};LoadResourceFile=pyload;SaveResourceFile=pysave
events={};handlers={};sent={};now=10000;source=10;allowed={[10]=true,[20]=true};records={[10]={id=1},[20]={id=2}};buckets={};states={};exports={cidade_acesso={}}
function exports.cidade_acesso:GetVerifiedRecord(id)return records[id]end
function GetCurrentResourceName()return 'cidade_admin'end
function GetResourceState(n)return states[n] or 'started'end
function IsPlayerAceAllowed(id)return allowed[id]==true end
function GetPlayerRoutingBucket(id)return buckets[id] or 0 end
function GetGameTimer()return now end
function RegisterNetEvent(n,f)events[n]=f end
function AddEventHandler(n,f)handlers[n]=f end
function TriggerClientEvent(n,id,...)sent[#sent+1]={name=n,id=id,args={...}}end
latentSent={}
function TriggerLatentClientEvent(n,id,bps,data,images)latentSent[#latentSent+1]={name=n,id=id,bps=bps,data=data,images=images}end
function CreateThread(fn)end
''')
    lua.execute((D/'captured_catalog.lua').read_text(encoding='utf8'))
    lua.execute((D/'island_server.lua').read_text(encoding='utf8'));return lua,g
lua,g=server();seq=0
def ask(action,player=10,advance=500,**args):
    global seq
    seq+=1;g.source=player;g.now+=advance;g.events['cidade_admin:islandRequest'](seq,convert(lua,dict(action=action,**args)))
    reply=g.sent[len(g.sent)];assert reply['name']=='cidade_admin:islandReply' and reply['id']==player
    return plain(reply['args'][2])
def row(**kw):return dict(model=model,x=20,y=30,z=19,heading=90,scale=1,**kw)
assert not ask('begin',player=30,model=model)['ok'];g.allowed[10]=False;assert not ask('save',revision=0,rows=[row()])['ok'];g.allowed[10]=True
g.records[10]=None;assert not ask('list')['ok'];g.records[10]=convert(lua,{'id':1});checks.append('Verified account and ADM ACE required on every mutation')
g.buckets[10]=7;assert not ask('begin',model=model)['ok'];g.buckets[10]=0;checks.append('Editor limited to main routing bucket')
assert not ask('begin',model='adder')['ok'];assert not ask('execute',name='quit')['ok'];checks.append('Whitelist rejects unknown models and console actions')
assert ask('begin',model=model)['ok'];assert not ask('begin',model=model,advance=0)['ok'];checks.append('Request cooldown enforced')
for key,value in [('x',5000),('y',5000),('z',250),('heading',360),('scale',4),('x',float('nan')),('scale',float('inf'))]:
    bad=row();bad[key]=value;assert not ask('save',revision=0,rows=[bad])['ok']
for rows in [[],[row()]*33]:assert not ask('save',revision=0,rows=rows)['ok']
assert not disk;checks.append('Finite position, island boundaries, rotation, scale and batch size validated before disk writes')
a=row();a.update(id=999,author=99,batch='forged')
r=ask('save',revision=0,rows=[a,row()]);assert r['ok'] and r['data']['revision']==1
assert [v['id'] for v in r['data']['objects']]==[1,2] and all(v['author']==1 for v in r['data']['objects'])
assert g.sent[len(g.sent)-1]['name']=='cidade_admin:islandWorld' and g.sent[len(g.sent)-1]['id']==-1;checks.append('Server assigns IDs and author, persists and broadcasts all placements')
assert not ask('save',player=20,revision=0,rows=[row()])['ok'];assert len(ask('list')['data']['objects'])==2;checks.append('Stale revision cannot overwrite another ADM edit')
assert ask('save',player=20,revision=1,rows=[row()])['ok'];assert ask('undo',revision=2)['ok'];objects=ask('list')['data']['objects'];assert len(objects)==1 and objects[0]['author']==2
checks.append('Undo removes own latest batch and preserves other ADM applications')
id=objects[0]['id'];new=row();new['x']=100
assert ask('begin',model=model,id=id)['ok'];r=ask('save',revision=3,id=id,rows=[new]);assert r['ok'] and r['data']['objects'][0]['id']==id and r['data']['objects'][0]['x']==100;checks.append('Reposition preserves object ID and replaces persisted transform')
previous=disk['data/island_placements.json'];fail=True;assert not ask('delete',revision=4,id=id)['ok'];assert disk['data/island_placements.json']==previous and len(ask('list')['data']['objects'])==1;fail=False
checks.append('Disk failure cannot mutate or broadcast world')
lua,g=server();assert ask('list')['data']['objects'][0]['x']==100;assert ask('list')['data']['revision']==4;checks.append('Resource restart reloads saved objects and revision')
assert ask('delete',revision=4,id=id)['ok'];assert not ask('delete',revision=5,id=id)['ok'];assert ask('list')['data']['objects']==[]
assert 'data/island_placements.backup.json' in disk;checks.append('Delete persisted and previous save backed up')
validfile=disk['data/island_placements.json'];disk['data/island_placements.json']='broken'
try:server();raise AssertionError('Corrupted save silently overwritten')
except Exception as e:assert 'Arquivo de coloca' in str(e)
disk['data/island_placements.json']=validfile;checks.append('Corrupted file fails loudly without erasing placements')
lua,g=server();cayo_row=row();cayo_row.update(x=2600,y=300,z=45,pitch=20,roll=-10)
result=ask('save',revision=5,rows=[cayo_row]);assert result['ok'] and result['data']['objects'][0]['pitch']==20
checks.append('Cayo Perico accepts placements in its own bounds and preserves object tilt')
assert not ask('save',revision=6,rows=[dict(cayo_row,x=1500)])['ok'];checks.append('Ocean gap between editable islands is rejected')
captured_data=dict(type='capturedCatalog',revision=51,objects=[dict(model=model,hash=123,bbMin=[-1,-1,0],bbMax=[1,1,2],image='data:image/webp;base64,test')],marks=[])
captured_raw=json.dumps(captured_data);metadata_raw=json.dumps({**captured_data,'objects':[{k:v for k,v in item.items() if k!='image'} for item in captured_data['objects']]})
disk['data/catalogo_capturado.json']=captured_raw;disk['data/catalogo_capturado_indice.json']=metadata_raw;lua,g=server();g.events['cidade_admin:islandSync']()
assert g.latentSent[1]['data']==metadata_raw and g.latentSent[1]['images']==captured_raw and g.latentSent[1]['id']==10
assert g.CidadeCapturedCatalog.objects[1]['image'] is None
checks.append('Server decodes only model metadata and reuses encoded thumbnails for synchronization')

client=LuaRuntime(unpack_returned_tuples=True);c=client.globals()
c.pydecode=lambda t:convert(client,json.loads(t));c.pyload=lambda r,f:json.dumps(catalog) if f=='ui/cayo.json' else 'null'
client.execute('''
json={decode=pydecode};LoadResourceFile=pyload;events={};handlers={};callbacks={};commands={};threads={};now=0;source=65535;objects={};nextObj=100;deleted={};matrices={};messages={};controls={};focus=true;opened=true;ground=true;hit=true;modelAvailable=true;revision=0;saveRequest=nil
LocalPlayer={state={cidadeAdmin=true}};CidadeAdminPanel={}
function CidadeAdminPanel.message(t)messages[#messages+1]=t end
function CidadeAdminPanel.close()opened=false;focus=false end
function CidadeAdminPanel.isOpen()return opened end
function GetCurrentResourceName()return 'cidade_admin'end
function RegisterNetEvent(n,f)events[n]=f end
function RegisterNUICallback(n,f)callbacks[n]=f end
function RegisterCommand(n,f)commands[n]=f end
function RegisterKeyMapping(...)end
function AddEventHandler(n,f)handlers[n]=f end
function CreateThread(f)threads[#threads+1]=coroutine.create(f)end
function Wait(ms)now=now+math.max(1,ms);coroutine.yield(ms)end
function GetGameTimer()return now end
function SendNUIMessage()end
function SendNuiMessage(raw)lastRawNui=raw end
function TriggerServerEvent(n,seq,request)
 if n=='cidade_admin:islandRequest' then
  if request.action=='save' then saveRequest=request end
  events['cidade_admin:islandReply'](seq,{ok=true,message='saved',data={revision=revision}})
 end
end
local V={};V.__index=V
function vector3(x,y,z)return setmetatable({x=x,y=y,z=z},V)end
V.__add=function(a,b)return vector3(a.x+b.x,a.y+b.y,a.z+b.z)end
V.__sub=function(a,b)return vector3(a.x-b.x,a.y-b.y,a.z-b.z)end
V.__mul=function(a,b)return vector3(a.x*b,a.y*b,a.z*b)end
V.__len=function(a)return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z)end
cam=vector3(0,0,40);ped=vector3(0,0,20)
function GetEntityCoords()return ped end
function GetFrameTime()return 1/60 end
function IsPauseMenuActive()return false end
function IsNuiFocused()return focus end
function PlayerId()return 1 end
function DisablePlayerFiring()end
function GetGameplayCamCoord()return cam end
function GetGameplayCamRot()return vector3(-30,0,0)end
function GetOffsetFromEntityInWorldCoords()return vector3(0,5,20)end
function PlayerPedId()return 1 end
function GetEntityHeading()return 0 end
function joaat(n)return n end
function IsModelInCdimage()return modelAvailable end
function IsModelValid()return modelAvailable end
function RequestModel()end
function HasModelLoaded()return true end
function SetModelAsNoLongerNeeded()end
function CreateObjectNoOffset()nextObj=nextObj+1;objects[nextObj]=true;return nextObj end
function SetEntityAsMissionEntity()end
function FreezeEntityPosition()end
function SetEntityLodDist()end
function SetEntityMatrix(id,...)
 local args={...};for _,v in ipairs(args)do assert(math.type(v)=='float','Native float argument received an integer: '..tostring(v))end
 matrices[id]=args
end
function SetEntityCollision()end
function SetEntityAlpha()end
function SetEntityVisible()end
function DeleteEntity(id)objects[id]=nil;deleted[#deleted+1]=id end
function SetNewWaypoint()end
function IsEntityDead()return false end
function DisableControlAction()end
function IsDisabledControlJustPressed(_,n)return controls[n]==true end
function IsDisabledControlPressed(_,n)return controls[n]==true end
function IsControlPressed()return false end
function StartExpensiveSynchronousShapeTestLosProbe()return 1 end
function GetShapeTestResult()return 2,hit,vector3(20,30,18)end
function RequestCollisionAtCoord()end
function GetGroundZFor_3dCoord()return ground,18 end
function SetTextFont()end;function SetTextScale()end;function SetTextColour()end;function SetTextOutline()end;function BeginTextCommandDisplayText()end;function AddTextComponentSubstringPlayerName()end;function EndTextCommandDisplayText()end
function step(i)local ok,err=coroutine.resume(threads[i]);assert(ok,err)end
''')
client.execute((D/'captured_catalog.lua').read_text(encoding='utf8'))
client.execute((D/'island_client.lua').read_text(encoding='utf8'))
def begin(**args):
    c.opened=True;c.callbacks['islandAction'](convert(client,dict(action='begin',model=model,count=1,radius=0,**args)),lambda r:None);client.execute('step(#threads)')
client.execute('step(2)')
begin();assert not c.focus and not c.opened and len(list(c.objects.items()))==1;checks.append('Preview releases NUI focus and creates only temporary local object')
client.execute('step(2)');client.execute('step(2)');matrix=plain(c.matrices[c.nextObj]);assert matrix[10]>=4,matrix
assert math.isclose(matrix[11],18-catalog['objects'][0]['bbMin'][2])
initial_x=matrix[9];y=matrix[10];c.ped=client.eval('vector3(7,-9,300)');client.execute('step(2)');matrix=plain(c.matrices[c.nextObj]);assert math.isclose(matrix[9],initial_x+7) and math.isclose(matrix[10],y-9) and math.isclose(matrix[11],18-catalog['objects'][0]['bbMin'][2])
checks.append('Preview follows player translation while flying and remains grounded')
c.controls[172]=True;client.execute('step(2)');raised=c.matrices[c.nextObj][12];assert raised>matrix[11];c.controls[172]=False;c.controls[173]=True;client.execute('step(2)');c.controls[173]=False;assert math.isclose(c.matrices[c.nextObj][12],matrix[11]);checks.append('Up/down arrows adjust height symmetrically')
c.controls[96]=True;client.execute('step(2)');c.controls[96]=False;client.execute('step(2)');matrix=plain(c.matrices[c.nextObj]);assert math.isclose(matrix[8],1.05);client.execute('step(2)');assert math.isclose(c.matrices[c.nextObj][9],1.05);checks.append('Repeated transform keeps stable scale without compounding')
c.ground=0;c.controls[201]=True;client.execute('step(2)');assert not c.saveRequest;c.ground=1;client.execute('step(2)');assert c.saveRequest and len(list(c.objects.items()))==0
checks.append('Missing ground blocks commit; Enter submits validated transform and clears preview')
c.controls[201]=False;begin();old_preview=c.nextObj;begin(scale=.5);assert old_preview not in dict(c.objects.items()) and len(list(c.objects.items()))==1;assert math.isclose(c.matrices[c.nextObj][9],.5);checks.append('Selecting another object abandons the unsaved preview and applies requested scale');c.commands['cancelarilha']();assert len(list(c.objects.items()))==0;checks.append('Cancel deletes preview without saving')
begin();c.LocalPlayer.state.cidadeAdmin=False;client.execute('step(2);step(2)');assert len(list(c.objects.items()))==0;checks.append('Permission revocation clears active preview')
c.LocalPlayer.state.cidadeAdmin=True;begin();c.handlers['onResourceStop']('cidade_admin');assert len(list(c.objects.items()))==0;checks.append('Resource stop cleans temporary objects')
# Reload a saved placement through the actual streamer, then select it with Caps.
c.ped=client.eval('vector3(20,29,20)');c.cam=client.eval('vector3(20,29,22)');c.opened=False;c.focus=False
saved=dict(id=77,model=model,x=20,y=30,z=19,heading=35,scale=1)
c.events['cidade_admin:islandWorld'](convert(client,dict(revision=12,objects=[saved])))
client.execute('step(1);step(1)');assert len(list(c.objects.items()))==1
c.revision=12;c.commands['editarilhaperto']();client.execute('step(#threads)')
matrix=plain(c.matrices[c.nextObj]);assert matrix[9:12]==[20,30,19],matrix
checks.append('Caps selects nearby saved object and preserves its original transform')
c.ped=client.eval('vector3(23,25,90)');client.execute('step(2);step(2)');matrix=plain(c.matrices[c.nextObj]);assert matrix[9:12]==[23,26,19],matrix
c.controls[201]=True;client.execute('step(2)');c.controls[201]=False
assert c.saveRequest['id']==77 and c.saveRequest['revision']==12
checks.append('Resumed object follows movement and saves under the same ID')
c.commands['cancelarilha']();c.LocalPlayer.state.cidadeAdmin=False
before=len(c.threads);c.commands['editarilhaperto']();assert len(c.threads)==before
checks.append('Caps cannot start editing without administrator permission')
# Cancellation while the frame loop is suspended must not kill the editor.
c.LocalPlayer.state.cidadeAdmin=True;begin();client.execute('step(2)');c.commands['cancelarilha']();client.execute('step(2)')
assert client.eval('coroutine.status(threads[2])')!='dead'
begin();client.execute('step(2);step(2)');assert len(list(c.objects.items()))>=1
checks.append('Frame loop survives cancellation during Wait and can place another preview')
c.commands['cancelarilha']()
checks.append('All entity matrix axes and coordinates passed as native floats, including scale 1')
c.events['cidade_admin:capturedCatalog'](json.dumps(dict(revision=99,objects=[dict(model=model,hash=123,defaultPitch=90,defaultRoll=0,bbMin=[-1,-2,-3],bbMax=[1,2,3])],marks=[])))
c.events['cidade_admin:capturedCatalog']('invalid-json');assert c.CidadeCapturedCatalog.revision==99
checks.append('Client accepts encoded catalogue and preserves its last version after malformed updates')
c.events['cidade_admin:capturedCatalog'](json.dumps(dict(revision=99,objects=[],marks=[])),captured_raw)
assert c.lastRawNui==captured_raw
checks.append('Thumbnail JSON reaches the browser unchanged, including repeated panel opens')
begin();matrix=plain(c.matrices[c.nextObj]);axes=[matrix[:3],matrix[3:6],matrix[6:9]]
assert all(math.isclose(sum(v*v for v in axis),1,abs_tol=1e-9) for axis in axes)
assert all(math.isclose(sum(a*b for a,b in zip(axes[i],axes[j])),0,abs_tol=1e-9) for i,j in ((0,1),(0,2),(1,2)))
assert math.isclose(matrix[11],20,abs_tol=1e-9);checks.append('Captured tilt preserves three full-size orthogonal axes and grounds rotated bounds')
c.commands['cancelarilha']()
report=dict(passed=True,checks=checks,in_game_visual_verified=False)
(R/'painel_adm_20261009/island-verification.json').write_text(json.dumps(report,indent=2));print('ISLAND_TESTS_PASSED',len(checks))
