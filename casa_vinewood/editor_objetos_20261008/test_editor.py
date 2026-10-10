import sys,json,math
from pathlib import Path
P=Path(__file__).resolve().parent; R=P.parents[1]; D=R/'server-data/resources/cidade_mansao'
sys.path.insert(0,str(R/'casa_vinewood/work/lua_syntax_deps'))
from lupa import LuaRuntime
from luaparser import ast
files=['objetos_shared.lua','objetos_server.lua','objetos_client.lua','fxmanifest.lua']
for name in files: ast.parse((D/name).read_text(encoding='utf-8'))
checks=[]
def plain(v):
    if hasattr(v,'items'):
        items=list(v.items())
        if items and all(isinstance(k,(int,float)) for k,_ in items): return [plain(v[i]) for i in range(1,len(items)+1)]
        return {str(k):plain(x) for k,x in items}
    return v
def runtime(storage=None):
    l=LuaRuntime(unpack_returned_tuples=True); g=l.globals(); storage=storage if storage is not None else {}
    g.py_decode=lambda s:l.table_from(json.loads(s),recursive=True)
    g.py_encode=lambda v:json.dumps(plain(v),ensure_ascii=False)
    g.py_load=lambda name:storage.get(name) or ((D/name).read_text(encoding='utf-8-sig') if (D/name).exists() else None)
    g.py_save=lambda name,data:storage.update({name:data}) or True
    l.execute('''
        json={decode=py_decode,encode=py_encode}; events={}; commands={}; threads={}; sent={}; now=0; source=1; ace=true; failSave=false
        function GetCurrentResourceName() return 'cidade_mansao' end
        function LoadResourceFile(_,name) return py_load(name) end
        function SaveResourceFile(_,name,data,_) if failSave then return false end return py_save(name,data) end
        function GetHashKey(s) local n=0; for i=1,#s do n=(n*31+s:byte(i))%2147483647 end return n end
        function RegisterNetEvent(name,fn) events[name]=fn end
        function AddEventHandler(name,fn) events[name]=fn end
        function RegisterCommand(name,fn,_) commands[name]=fn end
        function RegisterKeyMapping(...) end
        function CreateThread(fn) threads[#threads+1]=coroutine.create(fn) end
        function Wait(ms) coroutine.yield(ms) end
        function GetGameTimer() return now end
        function IsPlayerAceAllowed(_,_) return ace end
        function GetPlayerPed(_) return 1 end
        player={x=-979,y=667,z=157.05}; health=200; bucket=0
        function GetPlayerRoutingBucket(_) return bucket end
        function GetEntityCoords(_) return player end
        function GetEntityHealth(_) return health end
        function TriggerClientEvent(name,target,...) sent[#sent+1]={name=name,target=target,args={...}} end
        function emit(src,name,...) source=src; return events['cidade:objetos:'..name](...) end
        function step(i) local ok,msg=coroutine.resume(threads[i]); assert(ok,msg); return msg end
    ''')
    l.execute((D/'objetos_shared.lua').read_text()); return l,storage
l,storage=runtime(); g=l.globals(); M=g.CidadeObjetos
catalog=json.loads((D/'objetos_catalogo.json').read_text()) if (D/'objetos_catalogo.json').exists() else json.loads((P/'package/objetos_catalogo.json').read_text())
g.py_load=lambda name: json.dumps(catalog) if name=='objetos_catalogo.json' else storage.get(name)
l.execute((D/'objetos_server.lua').read_text())
d=next(x for x in catalog['objects'] if x['model']=='mansao_jantar'); dl=l.table_from(d,recursive=True)
c=M.center(dl,dl); turned=M.turn(dl,dl,90); c2=M.center(dl,turned)
assert M.distance(c,c2)<1e-8; checks.append('rotation preserves off-centre mesh centre')
assert abs(M.surfaceDistance(dl,dl,l.table_from(plain(c))))<1e-6
assert not M.pose(l.table_from({'p':[float('nan'),0,0],'h':0},recursive=True)); checks.append('NaN rejected')
g.player=l.table_from(dict(zip(['x','y','z'],plain(c))))
def ev(name,*args,src=1):
    g.now+=400; return g.emit(src,name,*[l.table_from(a,recursive=True) if isinstance(a,(dict,list)) else a for a in args])
def last(name):
    return next(x for x in reversed(list(g.sent.values())) if x['name']=='cidade:objetos:'+name)
g.ace=False; ev('toggle',True); assert last('mode')['args'][1]==False; checks.append('non-admin activation denied')
g.ace=True; ev('toggle',True); ev('lock',d['id'],None)
lock=last('locked'); token=lock['args'][2]
ev('toggle',True,src=2); ev('lock',d['id'],None,src=2); assert 'Outro administrador' in last('notice')['args'][1]; checks.append('concurrent ownership protected')
pose={'p':d['p'].copy(),'h':d['h']}; pose['p'][0]+=1
ev('update',d['id'],'wrong',1,pose); ev('snapshotRequest',src=3)
assert last('snapshot')['args'][2][d['id']]['p'][1]==d['p'][0]; checks.append('forged token rejected')
ev('update',d['id'],token,2,pose); old={'p':d['p'].copy(),'h':d['h']}; ev('update',d['id'],token,1,old)
ev('snapshotRequest',src=4); assert last('snapshot')['args'][2][d['id']]['p'][1]==pose['p'][0]; checks.append('stale move rejected; snapshot shares move')
ev('finish',d['id'],token,pose,False); ev('snapshotRequest',src=5)
assert last('snapshot')['args'][2][d['id']]['p'][1]==d['p'][0]; checks.append('cancel restores committed pose')
ev('lock',d['id'],None); token=last('locked')['args'][2]; ev('finish',d['id'],token,pose,True)
assert json.loads(storage['objetos_posicoes.json'])['positions'][d['id']]['p'][0]==pose['p'][0]; checks.append('commit persisted')
ev('lock',d['id'],None); token=last('locked')['args'][2]; g.failSave=True; pose2=plain(M.turn(dl,l.table_from(pose,recursive=True),90)); pose2['p'][0]+=1
ev('finish',d['id'],token,pose2,True); assert 'Falha ao salvar' in last('notice')['args'][1]
ev('snapshotRequest',src=6); assert last('snapshot')['args'][2][d['id']]['h']==pose['h']; checks.append('disk failure rolls back')
g.failSave=False; ev('lock',d['id'],None); token=last('locked')['args'][2]; ev('update',d['id'],token,1,pose2)
g.source=1; g.events['playerDropped'](); ev('snapshotRequest',src=7)
assert last('snapshot')['args'][2][d['id']]['h']==pose['h']; checks.append('disconnect rolls back')
ev('toggle',True); ev('lock',d['id'],None); token=last('locked')['args'][2]; ev('update',d['id'],token,1,pose2)
g.step(1); g.now+=7000; g.step(1); ev('snapshotRequest',src=8)
assert last('snapshot')['args'][3][d['id']] is None; checks.append('stalled lock expires')
ev('lock',d['id'],None); g.ace=False; g.now+=1001; g.step(1)
assert last('mode')['args'][1]==False; checks.append('permission revocation disables editor')
g.ace=True; ev('toggle',True); far={'p':[5000,5000,1000],'h':0}; ev('lock',d['id'],None); token=last('locked')['args'][2]; ev('finish',d['id'],token,far,True)
assert 'Posicao invalida' in last('notice')['args'][1]; checks.append('far-away teleport rejected')
l2,_=runtime(storage); l2.globals().py_load=lambda name:json.dumps(catalog) if name=='objetos_catalogo.json' else storage.get(name)
l2.execute((D/'objetos_server.lua').read_text()); l2.globals().emit(3,'snapshotRequest')
assert l2.globals().sent[1]['args'][2][d['id']]['p'][1]==pose['p'][0]; checks.append('restart reloads saved layout')
generic={'model':123,'p':plain(c),'h':0,'lo':[-.5,-.5,0],'hi':[.5,.5,1],'s':[1,1,1],'basis':[[0,1,0],[1,0,0],[0,0,1]]}
assert M.generic(l.table_from(generic,recursive=True),l.table()); gid=M.genericId(l.table_from(generic,recursive=True))
ev('lock',gid,generic); token=last('locked')['args'][2]; ev('finish',gid,token,generic,True)
assert gid in json.loads(storage['objetos_posicoes.json'])['generic']; checks.append('ordinary map prop descriptor persisted')
assert 'objetos_posicoes.backup.json' in storage; checks.append('previous disk revision backed up')
# Client controls, spawn transform and cancellation, with vector/native stubs.
cl,_=runtime(); cg=cl.globals(); cg.py_load=lambda name:json.dumps(catalog) if name=='objetos_catalogo.json' else None
cl.execute('''
    local mt={}; mt.__index=mt
    function vector3(x,y,z) return setmetatable({x=x,y=y,z=z},mt) end
    mt.__add=function(a,b) return vector3(a.x+b.x,a.y+b.y,a.z+b.z) end
    mt.__sub=function(a,b) return vector3(a.x-b.x,a.y-b.y,a.z-b.z) end
    mt.__mul=function(a,b) return vector3(a.x*b,a.y*b,a.z*b) end
    mt.__len=function(a) return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z) end
    function GetEntityCoords(_) return vector3(player.x,player.y,player.z) end
    function PlayerPedId() return 1 end; function PlayerId() return 0 end; function GetPlayerServerId(_) return 1 end
    function TriggerServerEvent(name,...) sent[#sent+1]={name=name,args={...}} end
    function BeginTextCommandThefeedPost(...) end; function AddTextComponentSubstringPlayerName(...) end; function EndTextCommandThefeedPostTicker(...) end
    function BeginTextCommandDisplayHelp(...) end; function EndTextCommandDisplayHelp(...) end
    modelHash=123; matrix=nil; collide=true; deleted=false
    function RequestModel(_) end; function HasModelLoaded(_) return true end
    function CreateObjectNoOffset(...) return 101 end; function SetEntityAsMissionEntity(...) end
    function FreezeEntityPosition(...) end; function SetEntityLodDist(...) end; function SetModelAsNoLongerNeeded(...) end
    function SetEntityCoordsNoOffset(...) end; function SetEntityMatrix(...) matrix={...} end
    function SetEntityCollision(_,on,_) collide=on end; function DoesEntityExist(_) return true end
    function SetEntityDrawOutline(...) end; function SetEntityDrawOutlineColor(...) end
    function DeleteEntity(_) deleted=true end
    function GetGameplayCamCoord() return vector3(player.x,player.y-2,player.z+1) end
    function GetGameplayCamRot(_) return vector3(0,0,0) end
    function StartExpensiveSynchronousShapeTestLosProbe(...) return 1 end
    function GetShapeTestResult(_) return 2,true,vector3(0,0,0),vector3(0,0,1),101 end
    function GetGamePool(_) return {101} end
    function GetPedBoneCoords(...) return vector3(player.x,player.y,player.z+1) end
    function IsEntityOnScreen(_) return true end; function IsEntityDead(_) return false end; function IsPedInAnyVehicle(...) return false end
    function DisableControlAction(...) end; function GetFrameTime() return .016 end
    function CreateModelHideExcludingScriptObjects(...) end; function RemoveModelHide(...) end
''')
cl.execute((D/'objetos_client.lua').read_text()); cd=dict(d); cd['s']=[.8,.8,.8]; ct={'p':d['p'].copy(),'h':d['h']}
cg.player=cl.table_from(dict(zip(['x','y','z'],plain(c))))
cg.emit(65535,'snapshot',{d['id']:cd},{d['id']:ct},{}) if False else None
cg.emit(65535,'snapshot',cl.table_from({d['id']:cd},recursive=True),cl.table_from({d['id']:ct},recursive=True),cl.table())
cg.step(1); assert abs(math.sqrt(sum(cg.matrix[i]**2 for i in range(2,5)))-.8)<1e-6; checks.append('client preserves original YMAP scale')
cg.emit(65535,'mode',True); cg.commands['+cidade_objeto_caps'](); assert cg.sent[len(cg.sent)]['name']=='cidade:objetos:lock'; checks.append('CAPS requests selection')
cg.emit(65535,'state',d['id'],cl.table_from(ct,recursive=True),1); cg.emit(65535,'locked',d['id'],'t',cl.table_from(ct,recursive=True))
assert cg.collide==False; cg.player['x']+=.5; cg.now=500; cg.step(2)
assert abs(cg.matrix[11]-ct['p'][0]-.5)<1e-6; checks.append('walking moves prop by ped displacement without pivot jump')
cg.commands['+cidade_objeto_caps'](); assert cg.sent[len(cg.sent)]['args'][4]==True; checks.append('second CAPS commits')
cg.emit(65535,'state',d['id'],cl.table_from(ct,recursive=True),False); assert cg.collide==True; checks.append('commit restores collision')
cg.emit(65535,'locked',d['id'],'t2',cl.table_from(ct,recursive=True)); cg.commands['+cidade_objeto_cancel']()
assert cg.sent[len(cg.sent)]['args'][4]==False; checks.append('BACKSPACE cancels')
cg.events['onResourceStop']('cidade_mansao'); assert cg.deleted; checks.append('resource stop removes clones')
for damaged,expected in [({'objetos_posicoes.json':'{broken'},False),({'objetos_posicoes.json':'{broken','objetos_posicoes.backup.json':storage['objetos_posicoes.json']},True)]:
    recovery,_=runtime(damaged);rg=recovery.globals()
    rg.py_load=lambda name:json.dumps(catalog) if name=='objetos_catalogo.json' else damaged.get(name)
    recovery.execute((D/'objetos_server.lua').read_text());rg.emit(1,'toggle',True)
    mode=next(e for e in rg.sent.values() if e['name']=='cidade:objetos:mode')
    assert mode['args'][1]==expected
checks.append('invalid save recovers backup or refuses overwrite')
(P/'tests.json').write_text(json.dumps({'passed':len(checks),'checks':checks,'lua_syntax':files,'in_game_verified':False},indent=2))
print('PASS',len(checks),'checks; Lua syntax valid')
