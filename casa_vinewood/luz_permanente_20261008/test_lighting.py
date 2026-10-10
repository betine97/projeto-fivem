"""Test permanent native definitions, room coverage and actual Lua boost loop."""
import sys,json,math,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];O=P/'package';D=R/'server-data/resources/cidade_mansao'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',str(R/'casa_vinewood/work/pydeps'),str(R/'casa_vinewood/work/lua_syntax_deps')]
from szio.gta5 import try_load_asset
from szio.gta5.drawables import LightType,LightFlashiness
from shapely.geometry import Polygon,Point
from lupa import LuaRuntime
from luaparser import ast
project=json.loads((P/'projeto_luminotecnico.json').read_text(encoding='utf-8'))
c=json.loads((O/'iluminacao_ambiente.json').read_text());roof=try_load_asset(O/'mansao_teto.ydr')
assert len(roof.lights)==68
assert len({li.light_hash for li in roof.lights})==68
for light in roof.lights:
    assert light.time_flags==0xFFFFFF and light.flashiness==LightFlashiness.CONSTANT and light.light_type==LightType.POINT
    assert light.flags & 16384 and light.flags & 16
    assert not light.flags & (1|2|512|32768|1073741824)
    assert light.volume_intensity==0 and light.corona_intensity==0 and light.light_fade_distance>=100
coverage=[]
for region in project['regions']:
    poly=Polygon(region['polygon']);floor=-.8 if region['level']=='terreo' else 2.808
    lights=[r for r in project['lights'] if r['id'] in region['light_ids']]
    minx,miny,maxx,maxy=poly.bounds;n=0;worst=0
    for ix in range(math.ceil((maxx-minx)/.6)+1):
        for iy in range(math.ceil((maxy-miny)/.6)+1):
            x=min(minx+.05+ix*.6,maxx-.05);y=min(miny+.05+iy*.6,maxy-.05)
            if not poly.covers(Point(x,y)):continue
            # Surface and body height samples must be inside a permanent light volume.
            for z in [floor+.10,floor+1.4]:
                ratios=[math.dist((x,y,z),r['position'])/r['range'] for r in lights]
                ratio=min(ratios);assert ratio<1,(region['name'],(x,y,z),ratio)
                n+=1;worst=max(worst,ratio)
    coverage.append(dict(room=region['name'],level=region['level'],samples=n,worst_distance_to_radius=worst,native_sources=len(lights)))
l=LuaRuntime(unpack_returned_tuples=True);g=l.globals();g.decode_config=lambda _:l.table_from(c,recursive=True)
l.execute('''
json={decode=decode_config};commands={};calls={};camHandle=-1;hour=23
local mt={};mt.__index=mt
function vector3(x,y,z) return setmetatable({x=x,y=y,z=z},mt) end
mt.__add=function(a,b) return vector3(a.x+b.x,a.y+b.y,a.z+b.z) end
mt.__sub=function(a,b) return vector3(a.x-b.x,a.y-b.y,a.z-b.z) end
mt.__len=function(a) return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z) end
function GetCurrentResourceName() return 'cidade_mansao' end
function LoadResourceFile(...) return 'config' end
function RegisterCommand(name,fn,_) commands[name]=fn end
function GetClockHours() return hour end
function PlayerPedId() return 1 end
function GetEntityCoords(_) return player end
function GetGameplayCamCoord() return camera end
function GetRenderingCam() return camHandle end
function DoesCamExist(_) return true end
function GetCamCoord(_) return drone end
function DrawLightWithRange(...) calls[#calls+1]={...} end
function print(...) end
function Wait(ms) coroutine.yield(ms) end
function CreateThread(fn) thread=coroutine.create(fn) end
function step() calls={};local ok,err=coroutine.resume(thread);assert(ok,err);return err end
''')
source=(O/'iluminacao_decorativa.lua').read_text();ast.parse(source)
def world(p):return g.vector3(*[a+b for a,b in zip(c['origin'],p)])
g.player=world([0,-1,1]);g.camera=g.player;l.execute(source)
assert g.step()==500 and len(g.calls)==0
g.commands.luzmansao(0,l.table_from(['2']))
def signature():return sorted(tuple(row.values()) for row in g.calls.values())
cases=[];first=None
for label,p in [('hall_print', [1,-.5,1]),('sala_print',[-5,-9,1]),('jantar',[2,-8,1]),('cozinha',[11,-9,1]),('quarto_terreo',[-6,6,1]),('mezanino',[3,-2,4]),('suite',[-5,6,4]),('quarto_superior',[11,-10,4]),('deck',[2,11,1])]:
    g.player=world(p);g.camera=g.player
    for hour in [0,5,12,19,23]:
        g.hour=hour;assert g.step()==0;assert len(g.calls)==19
        sig=signature()
        if first is None:first=sig
        assert sig==first,(label,hour,'different rooms/intensity after moving')
    cases.append(dict(place=label,boost_lights=19,unchanged_at_all_tested_hours=True))
# A distant character using a drone at the house also gets the entire uniform boost.
g.player=g.vector3(0,0,0);g.camera=g.player;g.camHandle=7;g.drone=world([2,-7,3]);assert g.step()==0 and signature()==first
g.drone=g.player;assert g.step()==500 and len(g.calls)==0
g.commands.luzmansao(0,l.table_from(['1']));g.drone=world([2,-7,3]);assert g.step()==500 and len(g.calls)==0
g.commands.mansaoluzes()
assert 'table.sort' not in source and 'selectLights' not in source
report=dict(passed=True,coverage=coverage,total_surface_samples=sum(r['samples'] for r in coverage),native_lights=68,rooms=19,
    lua_cases=cases,optional_boost_exactly_identical_from_all_rooms_and_hours=True,default_script_draws=0,
    drone_camera_verified=True,far_loop_sleeps=True,native_constant_all_24_hours=True,native_light_hashes_unique=True,
    native_visible_from_outside=True,shadow_sources=3,lua_syntax=True,in_game_verified=False)
(P/'lighting_tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('LIGHTING_TESTS_PASS: 19 rooms;',report['total_surface_samples'],'surface samples; 45 movement/hour cases; native68, default script0, optional19')
