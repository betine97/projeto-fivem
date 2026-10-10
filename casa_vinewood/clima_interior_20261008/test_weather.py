"""Exercise real client code with Lua and check the surveyed shelter boundary."""
import json,sys,random,xml.etree.ElementTree as ET
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(R/'casa_vinewood/work/lua_syntax_deps'),str(R/'casa_vinewood/work/pydeps')]
from lupa import LuaRuntime
from luaparser import ast
from shapely.geometry import Polygon,Point
c=json.loads((P/'package/clima_interior.json').read_text())
shared=(D/'clima_shared.lua').read_text();client=(D/'clima_client.lua').read_text()
ast.parse(shared);ast.parse(client)
l=LuaRuntime(unpack_returned_tuples=True);g=l.globals()
g.py_decode=lambda _:l.table_from(c,recursive=True)
l.execute('''
json={decode=py_decode};commands={};events={};calls={};now=0;ped=1;found=17;ready=true;camHandle=-1
local mt={};mt.__index=mt
function vector3(x,y,z) return setmetatable({x=x,y=y,z=z},mt) end
mt.__add=function(a,b) return vector3(a.x+b.x,a.y+b.y,a.z+b.z) end
mt.__sub=function(a,b) return vector3(a.x-b.x,a.y-b.y,a.z-b.z) end
mt.__len=function(a) return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z) end
local function record(name,...) calls[#calls+1]={name,...} end
function GetCurrentResourceName() return 'cidade_mansao' end
function LoadResourceFile(...) return 'config' end
function GetHashKey(_) return 1234 end
function PlayerPedId() return ped end
function GetEntityCoords(_) return player end
function DoesEntityExist(_) return true end
function GetRenderingCam() return camHandle end
function DoesCamExist(_) return true end
function GetCamCoord(_) return scriptedCamera end
function GetGameplayCamCoord() return camera end
function GetGameTimer() return now end
function GetInteriorAtCoordsWithType(...) return found end
function IsValidInterior(i) return i~=0 end
function IsInteriorReady(_) return ready end
function PinInteriorInMemory(i) record('pin',i) end
function UnpinInterior(i) record('unpin',i) end
function RefreshInterior(i) record('refresh',i) end
function ForceRoomForEntity(...) record('ped',...) end
function ForceRoomForGameViewport(...) record('view',...) end
function ClearRoomForEntity(...) record('clearPed',...) end
function ClearRoomForGameViewport(...) record('clearView',...) end
function GetInteriorFromEntity(_) return found end
function GetRoomKeyFromEntity(_) return 1234 end
function RegisterCommand(name,fn,_) commands[name]=fn end
function AddEventHandler(name,fn) events[name]=fn end
function Wait(ms) coroutine.yield(ms) end
function CreateThread(fn) thread=coroutine.create(fn) end
function print(...) record('log',...) end
function step(ms) now=now+(ms or 100);calls={};local ok,err=coroutine.resume(thread);assert(ok,err) end
''')
l.execute(shared);conf=l.table_from(c,recursive=True)
def world(x,y,z):return [c['origin'][0]+x,c['origin'][1]+y,c['origin'][2]+z]
def shelter(p,was=False):return bool(g.CidadeClimaInterior.sheltered(conf,l.table_from(world(*p)),was))
checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)
for name,p in [('sala',(-6,-8,1)),('jantar',(2,-7,1)),('cozinha',(12,-10,1)),('hall',(4,-2,1)),('mezanino',(3,-2,4)),('pe_direito',(-6,-8,5)),('extensao_superior',(12,-15,4))]:
    check('interior_'+name,shelter(p))
for name,p in [('deck',(2,9,1)),('recuo',(3,-13,1)),('lado',(-10,-4,1)),('telhado',(3,-2,6.6)),('subsolo',(3,-2,-1)),('extensao_terreo',(12,-15,1))]:
    check('exterior_'+name,not shelter(p))
check('histerese_sem_proteger_deck',not shelter((-9.24,0,1)) and shelter((-9.24,0,1),True) and not shelter((-9.30,0,1),True))
rng=random.Random(1010)
for _ in range(3000):
    p=(rng.uniform(-12,18),rng.uniform(-19,13),rng.uniform(-2,9))
    poly=Polygon(c['upper_polygon'] if p[2]>=c['upper_z'] else c['ground_polygon'])
    expected=c['floor_z']<=p[2]<=c['ceiling_z'] and poly.covers(Point(p[:2]))
    assert shelter(p)==expected,p
check('3000_pontos_comparados_ao_poligono_real',True)
def v(p):return g.vector3(*world(*p))
def rows():return [list(row.values()) for row in g.calls.values()]
def has(name,*args):return any(row[0]==name and (not args or row[1:]==list(args)) for row in rows())
g.player=v((2,-7,1));g.camera=v((2,-7,2));l.execute(client);g.step(1000)
check('interior_forca_sala_personagem_e_camera',has('ped',1,17,1234) and has('view',17,1234) and has('pin',17))
g.step(1100);check('pin_nao_repete',not has('pin'))
g.camera=v((2,10,2));g.step()
check('camera_exterior_personagem_interior',has('ped',1,17,1234) and has('clearView') and not has('view'))
g.player=v((2,10,1));g.camera=v((2,-7,2));g.step()
check('personagem_exterior_camera_interior',has('clearPed',1) and has('view',17,1234) and not has('ped'))
g.camera=v((2,10,2));g.step();check('saida_restaura_exterior',has('clearView') and not has('view') and not has('ped'))
g.player=v((2,-7,1));g.camera=v((2,-7,2));g.step()
g.ped=2;g.step();check('troca_personagem_libera_anterior',has('clearPed',1) and has('ped',2,17,1234))
g.camHandle=7;g.scriptedCamera=v((2,10,2));g.step();check('camera_drone_exterior',has('clearView') and not has('view'))
g.scriptedCamera=v((2,-7,2));g.step();check('camera_drone_interior',has('view',17,1234))
g.ready=False;g.step(1100)
check('mlo_nao_pronto_libera_e_avisa',has('clearPed',2) and has('clearView') and has('refresh',17) and has('log') and not has('ped') and not has('view'))
g.ready=True;g.step()
g.found=18;g.step(1100)
check('novo_interior_libera_pin_anterior',has('unpin',17) and has('pin',18) and has('clearPed',2) and has('clearView') and has('ped',2,18,1234))
g.found=0;g.step(1100);check('mlo_descarregado_libera',has('unpin',18) and has('clearPed',2) and has('clearView') and not has('ped'))
g.found=17;g.step(1100)
g.player=g.vector3(0,0,0);g.camera=g.player;g.scriptedCamera=g.player;g.step()
check('longe_sem_forcar_salas',has('unpin',17) and has('clearPed',2) and has('clearView') and not has('view') and not has('ped'))
g.player=v((2,-7,1));g.camera=v((2,-7,2));g.camHandle=-1;g.step(1100)
g.calls=l.table();g.events.onResourceStop('outro');check('parada_outro_recurso_ignorada',len(g.calls)==0)
g.events.onResourceStop('cidade_mansao');check('parada_limpa_todos_overrides',has('unpin',17) and has('clearPed',2) and has('clearView'))
check('clima_global_nao_alterado',all(native not in client for native in ['SetRain','SetWeather','SetTimecycleModifier','SetExtraTimecycleModifier','SetFog']))
xml=ET.parse(D/'clima_interior.xml').getroot();mod=xml.find('modifier')
check('timecycle_preserva_luzes_exposicao_e_nevoa_distante',mod.attrib['name']=='mansao_ar_seco' and len(mod)==1 and mod.find('fog_start').text.strip()=='50.000 50.000')
report={'checks_passed':checks,'geometry_random_samples':3000,'lua_syntax':True,'in_game_verified':False}
(P/'weather_tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('WEATHER_TESTS_PASS',len(checks),'checks + 3000 geometry samples')
