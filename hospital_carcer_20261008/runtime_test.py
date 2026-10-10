from pathlib import Path
import sys,json
r=Path.cwd();p=r/'hospital_carcer_20261008';sys.path.insert(0,str(r/'casa_vinewood/work/lua_syntax_deps'))
from lupa import LuaRuntime
l=LuaRuntime(unpack_returned_tuples=True);g=l.globals();checks=[]
def table(v):
 if isinstance(v,dict):return l.table_from({k:table(x) for k,x in v.items()})
 if isinstance(v,list):return l.table_from([table(x) for x in v])
 return v
s=json.loads((p/'spec.json').read_text());g.config=table({k:s[k] for k in ['origin','doors','rooms']})
l.execute('''events={};sent={};now=10000;source=10;allowed=true;positions={}
local vm={};vm.__index=vm;function vm.__add(a,b)return vector3(a.x+b.x,a.y+b.y,a.z+b.z)end;function vm.__sub(a,b)return vector3(a.x-b.x,a.y-b.y,a.z-b.z)end;function vm.__len(a)return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z)end
function vector3(x,y,z)return setmetatable({x=x,y=y,z=z},vm)end
json={decode=function()return config end}
function LoadResourceFile()return ''end
function GetCurrentResourceName()return 'cidade_hospital_carcer'end
function RegisterNetEvent(n,f)events[n]=f end
function TriggerClientEvent(n,id,...)sent[#sent+1]={n,id,...}end
function GetPlayers()return {'10','20'}end
function GetPlayerPed(id)return tonumber(id)end
function DoesEntityExist()return true end
function GetEntityCoords(id)return positions[id] or vector3(1000,1000,1000)end
function IsPlayerAceAllowed()return allowed end
function GetGameTimer()return now end
''')
l.execute((p/'package/server.lua').read_text());f=g.events['cidade_hospital:toggle']
d=s['doors'][0];v=s['origin'];cx=v[0]+d['pos'][0]+d['width']/2;cy=v[1]+d['pos'][1];cz=v[2]+d['pos'][2]+1
g.positions[10]=g.vector3(cx,cy-1,cz)
for invalid in [-1,0,37,1.5,'1',None]:
 old=len(g.sent);f(invalid);assert len(g.sent)==old;checks.append('Malformed door ID rejected '+str(invalid))
g.allowed=False;f(1);assert len(g.sent)==0;checks.append('Unauthorized door request rejected')
g.allowed=True;g.positions[10]=g.vector3(1000,1000,1000);f(1);assert len(g.sent)==0;checks.append('Distant door request rejected')
g.positions[10]=g.vector3(cx,cy-1,cz);f(1);assert g.sent[1][1]=='cidade_hospital:door' and g.sent[1][4] is True;checks.append('Opening broadcasts shared state')
f(1);assert len(g.sent)==1;checks.append('Transition cooldown prevents jitter')
g.now+=1000;g.positions[20]=g.vector3(cx,cy,cz);f(1);assert g.sent[2][1]=='cidade_acesso:notice';checks.append('Closing on player rejected')
g.positions[20]=g.vector3(1000,1000,1000);f(1);assert g.sent[3][4] is False;checks.append('Clear doorway closes')
g.events['cidade_hospital:states']();assert g.sent[4][1]=='cidade_hospital:snapshot';checks.append('Joining client receives shared snapshot')
(p/'runtime_validation.json').write_text(json.dumps({'passed':True,'checks':checks,'in_game_verified':False},indent=2));print('HOSPITAL_RUNTIME_PASSED',len(checks))
