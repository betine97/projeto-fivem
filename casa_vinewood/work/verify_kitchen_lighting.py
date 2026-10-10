import sys,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';SERVER=R/'server-data/resources/cidade_mansao'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/lua_syntax_deps')]
from lupa import LuaRuntime
from luaparser import ast
cfg=json.loads((W/'cozinha_fivem/iluminacao_ambiente.json').read_text());script=(SERVER/'iluminacao_decorativa.lua').read_text();ast.parse(script)
lua=LuaRuntime(unpack_returned_tuples=True);g=lua.globals()
def table(v):
 if isinstance(v,dict):return lua.table_from({k:table(x) for k,x in v.items()})
 if isinstance(v,list):return lua.table_from([table(x) for x in v])
 return v
g.cfg=table(cfg)
lua.execute('''
local mt={__add=function(a,b) return vector3(a.x+b.x,a.y+b.y,a.z+b.z) end,__sub=function(a,b) return vector3(a.x-b.x,a.y-b.y,a.z-b.z) end,__len=function(a) return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z) end}
function vector3(x,y,z) return setmetatable({x=x,y=y,z=z},mt) end
timer=0;hour=23;minute=0;calls={};commands={};threads={};peak=0;frames_count=0
coords=vector3(cfg.origin[1]+12.4,cfg.origin[2]-9.2,cfg.origin[3]+.2);camera=coords
function GetClockHours() return hour end
function GetClockMinutes() return minute end
json={decode=function(_) return cfg end}
function GetCurrentResourceName() return 'cidade_mansao' end
function LoadResourceFile(...) return '' end
function CreateThread(f) threads[#threads+1]=coroutine.create(f) end
function Wait(t) delay=t;coroutine.yield() end
function PlayerPedId() return 1 end
function GetGameTimer() return timer end
function GetEntityCoords(_) return coords end
function GetGameplayCamCoord() return camera end
function RegisterCommand(n,f,_) commands[n]=f end
function DrawLightWithRange(...) calls[#calls+1]={...} end
function frame(t) timer=timer+t;calls={};for _,thread in ipairs(threads) do local ok,e=coroutine.resume(thread);assert(ok,e) end;peak=math.max(peak,#calls);frames_count=frames_count+1 end
''');lua.execute(script)
def position(x,y,z):return g.vector3(*(cfg['origin'][k]+p for k,p in enumerate((x,y,z))))
def frames(n=60):
 for _ in range(n):g.frame(16);assert len(g.calls)<=cfg['max_lights']
 return [[g.calls[i][j] for j in range(1,9)] for i in range(1,len(g.calls)+1)]
night=frames();strip=[q for q in night if abs(q[0]-cfg['origin'][0]-13.934)<.01 and abs(q[2]-cfg['origin'][2]-.75)<.01]
assert len(strip)>=3,len(strip);assert all(q[3:6]==[255,211,153] for q in strip);seen={round(q[1]-cfg['origin'][1],2) for q in strip}
nightpower=sum(q[7] for q in night);g.hour=12;day=frames();assert abs(nightpower/sum(q[7] for q in day)-cfg['night_multiplier']/cfg['day_multiplier'])<.001
g.hour=23
for x,y,z in [(12.4,-7,.2),(12.4,-12,.2),(10,-9,.2),(-5,-8,.2),(10,5,3.8)]:
 g.coords=position(x,y,z);g.camera=g.coords;rows=frames();assert len(rows)>5
 seen.update(round(q[1]-cfg['origin'][1],2) for q in rows if abs(q[0]-cfg['origin'][0]-13.934)<.01 and abs(q[2]-cfg['origin'][2]-.75)<.01)
assert len(seen)==5,seen
g.coords=position(500,500,0);g.camera=g.coords;g.frame(1000);assert len(g.calls)==0 and g.delay==1000
g.camera=position(12.4,-9.2,.2);assert len(frames())>5 and g.delay==0
report={'passed':True,'runtime_frames':g.frames_count,'budget':cfg['max_lights'],'peak_calls':g.peak,'all_five_worktop_sections_covered':True,'nearest_kitchen_leds_active':len(strip),'night_day_factor':cfg['night_multiplier']/cfg['day_multiplier'],'far_sleep':True,'camera_only':True,'script_sha256':hashlib.sha256(script.encode()).hexdigest()}
(W/'verificacao_luz_cozinha.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('KITCHEN_LIGHTING_VERIFIED',report,flush=True)
