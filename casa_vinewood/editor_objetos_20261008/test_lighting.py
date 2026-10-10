import sys,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao'
sys.path.insert(0,str(R/'casa_vinewood/work/lua_syntax_deps'))
from luaparser import ast
from lupa import LuaRuntime
c=json.loads((D/'iluminacao_ambiente.json').read_text()); source=(D/'iluminacao_decorativa.lua').read_text();ast.parse(source)
l=LuaRuntime(unpack_returned_tuples=True);g=l.globals()
g.py_decode=lambda _:l.table_from(c,recursive=True)
l.execute('''
    json={decode=py_decode};local mt={};mt.__index=mt
    function vector3(x,y,z) return setmetatable({x=x,y=y,z=z},mt) end
    mt.__add=function(a,b) return vector3(a.x+b.x,a.y+b.y,a.z+b.z) end
    mt.__sub=function(a,b) return vector3(a.x-b.x,a.y-b.y,a.z-b.z) end
    mt.__len=function(a) return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z) end
    function LoadResourceFile(...) return 'config' end; function GetCurrentResourceName() return 'cidade_mansao' end
    function RegisterCommand(name,fn,_) commands[name]=fn end
    commands={};now=0;hour=23;minutes=0;draws={}
    function GetClockHours() return hour end;function GetClockMinutes() return minutes end
    function GetGameTimer() return now end
    function PlayerPedId() return 1 end
    function GetEntityCoords(_) return player end;function GetGameplayCamCoord() return camera end
    function DrawLightWithRange(...) draws[#draws+1]={...} end
    function Wait(ms) coroutine.yield(ms) end
    function CreateThread(fn) thread=coroutine.create(fn) end
    function step() draws={};local ok,err=coroutine.resume(thread);assert(ok,err) end
''')
g.player=l.eval('vector3')(*c['origin']);g.camera=g.player;l.execute(source)
origin=c['origin'];cases=[]
for name,p in [('sala_tv',[-6,-11,-.8]),('jantar',[2,-8,-.8]),('cozinha',[12,-10,-.8]),('hall',[4,-2,-.8]),('superior',[3,-2,2.8])]:
    g.player=l.eval('vector3')(*[a+b for a,b in zip(origin,p)])
    g.camera=l.eval('vector3')(*[a+b for a,b in zip(origin,[p[0]-2,p[1],p[2]+1.5])])
    for _ in range(12):g.now+=100;g.step()
    rows=list(g.draws.values());assert 0<len(rows)<=24
    anchors=[]
    for row in c['lights']:
        if row.get('open_anchor'):
            pos=[a+b for a,b in zip(origin,row['position'])]
            if any(sum((d[i+1]-pos[i])**2 for i in range(3))<1e-6 for d in rows):anchors.append(row['id'])
    if name in ('sala_tv','jantar','cozinha'):assert len(anchors)==8,(name,anchors)
    cases.append({'place':name,'lights':len(rows),'open_room_anchors':len(anchors),'night':True})
g.hour=12;g.now+=100;g.step();day=sum(d[8] for d in g.draws.values())
g.hour=23;g.now+=100;g.step();night=sum(d[8] for d in g.draws.values());assert night>day*4
g.player=l.eval('vector3')(0,0,0);g.camera=g.player;g.now+=100;g.step();assert len(g.draws)==0
(P/'lighting_tests.json').write_text(json.dumps({'cases':cases,'night_to_day_power_ratio':night/day,'offsite_draws':0,'cap':24,'syntax':True,'in_game_verified':False},indent=2))
print('LIGHT_TESTS_PASS: all eight broad anchors stay active across sala/jantar/cozinha; cap24, offsite0')
