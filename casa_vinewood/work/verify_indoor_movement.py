"""Exercise the Lua resource's entry/exit/noclip/ped-change lifecycle."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=R/'server-data/resources/cidade_mansao'
sys.path[:0]=[str(W/'work/lua_syntax_deps')]
from lupa import LuaRuntime
from luaparser import ast
for p in D.glob('*.lua'):ast.parse(p.read_text(encoding='utf-8'))
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute("""
events={}; handlers={}; ped=100; foot=true; disabled=false
local mt={__sub=function(a,b) return setmetatable({x=a.x-b.x,y=a.y-b.y,z=a.z-b.z},getmetatable(a)) end}
function vector3(x,y,z) return setmetatable({x=x,y=y,z=z},mt) end
coords=vector3(0,0,0)
function PlayerPedId() return ped end
function GetEntityCoords(_) return coords end
function GetEntityCollisionDisabled(_) return disabled end
function IsPedOnFoot(_) return foot end
function DoesEntityExist(_) return true end
function SetPedMaxMoveBlendRatio(p,r) table.insert(events,{kind='pace',ped=p,value=r}) end
function DisableControlAction(g,c,v) table.insert(events,{kind='control',control=c,disabled=v}) end
function Wait(_) coroutine.yield() end
function CreateThread(fn) thread=coroutine.create(fn) end
function AddEventHandler(name,fn) handlers[name]=fn end
function GetCurrentResourceName() return 'cidade_mansao' end
function frame(x,y,z)
 coords=vector3(-976.101013+x,676.730896+y,157.835037+z)
 events={};local ok,err=coroutine.resume(thread);assert(ok,err)
end
""")
lua.execute((D/'movimento_interior.lua').read_text(encoding='utf-8'));g=lua.globals();cases=[]
def step(name,point,expected,**state):
 for k,v in state.items():setattr(g,k,v)
 g.frame(*point);ev=[dict(g.events[i].items()) for i in range(1,len(g.events)+1)]
 actual=[(e['kind'],e.get('ped'),e.get('value'),e.get('control')) for e in ev]
 assert actual==expected,(name,actual,expected)
 cases.append(dict(name=name,events=ev,passed=True))
gentle=[('control',None,None,21),('pace',100,1.35,None)]
step('street remains unrestricted',(2.3,8.1,.2),[])
step('ground floor gentle pace',(7.7,-10,.2),gentle)
step('upstairs gentle pace',(9,-10,3.8),gentle)
step('walking down stairs retains limit',(1.8,4.5,2.1),gentle)
step('deck exit restores running',(-5.53,-14.1,.2),[('pace',100,3.0,None)])
step('interior reentry reapplies limit',(-6,-8,.2),gentle)
step('noclip is unrestricted',(-6,-8,.2),[('pace',100,3.0,None)],disabled=True)
step('noclip subsequent frames stay unrestricted',(-6,-8,.2),[])
step('walking after flight restores limit',(-6,-8,.2),gentle,disabled=False)
step('vehicle entry restores normal behavior',(-6,-8,.2),[('pace',100,3.0,None)],foot=False)
step('ped change reapplies limit',(-6,-8,.2),[('control',None,None,21),('pace',101,1.35,None)],foot=True,ped=101)
step('replacement ped releases old handle',(-6,-8,.2),[('pace',101,3.0,None),('control',None,None,21),('pace',102,1.35,None)],ped=102)
g.events=lua.table();g.handlers['onResourceStop']('unrelated');assert len(g.events)==0
g.handlers['onResourceStop']('cidade_mansao');assert len(g.events)==1 and g.events[1]['ped']==102 and g.events[1]['value']==3.0
cases.append(dict(name='resource stop restores ordinary pace',passed=True))
(W/'verificacao_movimento_lua.json').write_text(json.dumps({'passed':True,'cases':cases,'lua_files_parsed':len(list(D.glob('*.lua'))),'max_indoor_move_blend':1.35,'in_game_verified':False},indent=2))
print('INDOOR_MOVEMENT_LUA',len(cases),'behavior cases passed')
