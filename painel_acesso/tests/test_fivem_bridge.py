"""Exercise real Lua admission callbacks and revocation with FiveM native mocks."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'casa_vinewood/work/lua_syntax_deps'))
from lupa import LuaRuntime
lua=LuaRuntime(unpack_returned_tuples=True);g=lua.globals()
lua.execute('''
handlers={};timeouts={};threads={};messages={};drops={};states={};commands={};admins={};source=7;httpCode=200;reply={id=3,name='Amigo',status='pending'};deferCount=0;identifiers={'license:abc123'}
exported={}
function exports(name,callback) exported[name]=callback end
function AddEventHandler(name,callback) handlers[name]=callback end
function RegisterCommand(name,callback,restricted) assert(restricted); end
function CreateThread(fn) table.insert(threads,coroutine.create(fn)) end
function GetConvar(name,default) if name=='cidade_acesso_key' then return 'private-test-key' else return default end end
json={encode=function(body) lastBody=body; return 'encoded' end,decode=function(_) return reply end}
function Wait(ms) local _,main=coroutine.running(); if not main and ms==5000 then coroutine.yield() end end
function SetTimeout(_,fn) table.insert(timeouts,fn) end
function GetPlayerIdentifiers(_) return identifiers end
function GetPlayers() return {'7'} end
function GetPlayerName(_) return 'Amigo' end
function PerformHttpRequest(url,callback,method,body,headers) assert(headers['X-Cidade-Key']=='private-test-key');lastURL=url;if holdHttp then pendingCallback=callback else callback(httpCode,'encoded') end end
function GetCurrentResourceName() return 'cidade_acesso' end
function ExecuteCommand(command)
 table.insert(commands,command)
 local op,id=command:match('^(%w+_principal) player%.(%d+) group%.admin$')
 assert(op and id,'Unexpected permission command: '..command)
 admins[tonumber(id)]=op=='add_principal'
end
function IsPlayerAceAllowed(id,object) assert(object=='cidade.admin');return admins[id]==true end
function DropPlayer(id,reason) table.insert(drops,{id=id,reason=reason}) end
function Player(id) return {state={set=function(_,key,value,replicated) assert(replicated);states[key]=value end}} end
-- FiveM distinguishes no arguments (accept) from an explicit nil argument (reject).
deferrals={defer=function() deferCount=deferCount+1 end,update=function(t) lastUpdate=t end,done=function(...) local argc=select('#',...); local reason=...;table.insert(messages,{reason=reason,allowed=argc==0}) end}
function connect() handlers['playerConnecting']('Amigo',nil,deferrals) end
function heartbeat() local ok,err=coroutine.resume(threads[1]);assert(ok,err) end
''')
lua.execute((R/'server-data/resources/cidade_acesso/server.lua').read_text(encoding='utf-8'))
g.connect();assert g.messages[1]['allowed'] is False and '3' in g.messages[1]['reason']
g.reply['status']='approved';g.connect();assert g.messages[2]['allowed'] is True
g.reply['status']='blocked';g.connect();assert g.messages[3]['allowed'] is False
g.httpCode=503;g.connect();assert g.messages[4]['allowed'] is False and 'indisponível' in g.messages[4]['reason']
for _,fn in g.timeouts.items():fn()
assert len(g.messages)==4,'Late timeout cannot finish an already completed admission twice'
def table(v):
 if isinstance(v,dict):return lua.table_from({k:table(x) for k,x in v.items()})
 if isinstance(v,list):return lua.table_from([table(x) for x in v])
 return v
g.httpCode=200;g.reply=table({'players':[{'source':7,'id':3,'name':'Amigo','status':'approved'}]})
g.heartbeat();assert g.states['cidadeId']==3 and g.states['cidadeNome']=='Amigo'
assert g.admins[7] is True and g.states['cidadeAdmin'] is True
g.reply=table({'players':[{'source':7,'id':3,'name':'Amigo','status':'blocked'}]});g.heartbeat();assert len(g.drops)==1 and g.drops[1]['id']==7
assert g.admins[7] is False and g.states['cidadeAdmin'] is False
g.httpCode=503;g.heartbeat();assert len(g.drops)==1,'Transient API outage must not drop already connected approved players'
# Permissions use the final joining handle, never the temporary connecting handle.
g.httpCode=200;g.reply=table({'id':3,'name':'Amigo','status':'approved'})
g.handlers['playerJoining']();assert g.admins[7] is True
g.httpCode=503;g.heartbeat();assert g.admins[7] is True,'Transient outages preserve existing admin sessions'
g.handlers['onResourceStop']('another_resource');assert g.admins[7] is True
g.handlers['playerDropped']();assert g.admins[7] is False
g.httpCode=200;g.reply=table({'id':3,'name':'Amigo','status':'pending'})
g.handlers['playerJoining']();assert g.admins[7] is False and len(g.drops)==2
g.reply['status']='approved';g.handlers['playerJoining']();assert g.admins[7] is True
g.handlers['onResourceStop']('cidade_acesso');assert g.admins[7] is False
# A delayed approval for an old account must not promote a new account on that ID.
g.holdHttp=True;g.handlers['playerJoining']()
g.identifiers=table(['license:differentAccount']);g.pendingCallback(200,'encoded')
assert g.admins[7] is False and len(g.drops)==2
g.identifiers=table(['license:abc123']);g.holdHttp=False
g.reply['status']='blocked';g.handlers['playerJoining']();assert g.admins[7] is False and len(g.drops)==3
assert 'exec server-ilha.cfg' in (R/'server-data/server.cfg').read_text()
config=(R/'server-data/server-ilha.cfg').read_text();assert config.index('ensure cidade_acesso')<config.index('ensure cidade_core') and 'sv_maxclients 16' in config
assert config.index('exec permissoes-amigos.cfg')<config.index('ensure cidade_acesso')
permissions=(R/'server-data/permissoes-amigos.cfg').read_text()
assert 'add_ace group.admin command allow' in permissions
assert 'add_ace resource.cidade_acesso command.add_principal allow' in permissions
assert 'add_ace resource.cidade_acesso command.remove_principal allow' in permissions
assert "model = 'a_m_y_business_01'" in (R/'server-data/resources/cidade_core/client.lua').read_text()
print('FIVEM_BRIDGE_OK: admission, default ped, persistent ID, automatic ADM, block/drop/stop revocation, outage preservation, recycled handle isolation')
