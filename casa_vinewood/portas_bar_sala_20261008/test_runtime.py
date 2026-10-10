import sys,json,math
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao'
sys.path[:0]=[str(R/'casa_vinewood/work/lua_syntax_deps')]
from lupa import LuaRuntime
cfg=json.loads((D/'portas_madeira.json').read_text(encoding='utf-8'))
lua=LuaRuntime(unpack_returned_tuples=True);g=lua.globals();g.decode=lambda _:lua.table_from(cfg,recursive=True)
lua.execute('''
json={decode=decode};handlers={};emitted={};players={'1','2'};pedpos={};now=1000;source=1
function GetCurrentResourceName() return 'cidade_mansao' end
function LoadResourceFile(...) return 'doors' end
function RegisterNetEvent(name,fn) handlers[name]=fn end
function AddEventHandler(name,fn) handlers[name]=fn end
function GetGameTimer() return now end
function GetPlayerPed(p) return tonumber(p) end
function GetEntityCoords(p) return pedpos[p] end
function GetPlayers() return players end
function TriggerClientEvent(name,target,...) emitted[#emitted+1]={name,target,...} end
''')
lua.execute((D/'portas_server.lua').read_text())
def at(p):return lua.table_from(dict(zip(['x','y','z'],[a+b for a,b in zip(cfg['origin'],p)])))
tests=0
for d in cfg['doors'][7:]:
    c=d['opening_center'];p=c[:];p[0]+=.85;g.pedpos[1]=at(p);g.pedpos[2]=at([0,0,0]);g.now+=1000
    fn=g.handlers['cidade_mansao:toggleDoor'];fn(d['id']);event=g.emitted[len(g.emitted)]
    assert event[1]=='cidade_mansao:doorState' and event[2]==-1 and event[3]==d['id'] and event[4] is True;tests+=1
    g.now+=1000;g.pedpos[2]=at([c[0],c[1],-.8+.85]);fn(d['id']);event=g.emitted[len(g.emitted)]
    assert event[1]=='cidade_mansao:doorOccupied';tests+=1
    g.now+=1000;g.pedpos[2]=at([0,0,0]);fn(d['id']);event=g.emitted[len(g.emitted)]
    assert event[1]=='cidade_mansao:doorState' and event[4] is False;tests+=1
    count=len(g.emitted);g.now+=1000;g.pedpos[1]=at([0,0,10]);fn(d['id']);assert len(g.emitted)==count;tests+=1
    # Full open leaf segment is far enough from the opening's center for a ped.
    angle=math.radians(d['open_heading']);h=d['hinge'];end=[h[0]-d['width_m']*math.cos(angle),h[1]-d['width_m']*math.sin(angle)]
    a,b=h[:2],end;v=[b[0]-a[0],b[1]-a[1]];t=max(0,min(1,sum((c[i]-a[i])*v[i] for i in range(2))/sum(x*x for x in v)))
    distance=math.hypot(*(c[i]-a[i]-t*v[i] for i in range(2)));assert distance>.45,(d['name'],distance);tests+=1
report=dict(passed=True,tests=tests,door_ids=[8,9],server_broadcast_to_every_player=True,occupied_opening_blocks_closing=True,distant_requests_rejected=True,open_leaf_clearance_over_45cm=True)
(P/'runtime_tests.json').write_text(json.dumps(report,indent=2));print('DOOR_RUNTIME_PASS',tests,'shared state, occupancy, access distance and open clearance cases')
