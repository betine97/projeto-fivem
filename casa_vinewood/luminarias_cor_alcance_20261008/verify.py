"""Native roundtrip, floor/cone coverage, unrelated asset preservation, Lua execution.

Geometric coverage is not a measurement of GTA exposure or frame time. Those
remain explicitly pending in-game, rather than treating a radius test as visual QA.
"""
import sys,json,math,hashlib
from pathlib import Path
from dataclasses import fields,is_dataclass
from collections import Counter
from enum import Enum
from io import BytesIO
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao';O=P/'package';B=P/'backup'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',str(R/'casa_vinewood/work/pydeps'),str(R/'casa_vinewood/work/lua_syntax_deps')]
import numpy as np
from PIL import Image
from szio.gta5 import try_load_asset
from szio.gta5.bounds import AssetBoundComposite,AssetBoundBvh
from szio.gta5.drawables import LightType,LightFlashiness
from szio.gta5.entities import EntityMloInstance
from szio.gta5.archetypes import ArchetypeType
from shapely.geometry import Polygon,Point
from lupa import LuaRuntime
from luaparser import ast
def equal(a,b):
    if isinstance(a,np.ndarray):return np.array_equal(a,b)
    if is_dataclass(a):return type(a)==type(b) and all(equal(getattr(a,f.name),getattr(b,f.name)) for f in fields(a) if f.name!='user_metadata')
    if isinstance(a,dict):return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,(tuple,list)):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    if isinstance(a,Enum):return a==b
    if isinstance(a,(float,np.floating)):return math.isclose(a,b,rel_tol=1e-6,abs_tol=1e-7)
    try:return bool(a==b)
    except ValueError:return bool(np.array_equal(a,b))
def collision(a,b):
    assert type(a)==type(b)
    if a is None:return
    if isinstance(a,AssetBoundComposite):
        assert len(a.children)==len(b.children)
        for x,y in zip(a.children,b.children):collision(x,y)
    if isinstance(a,AssetBoundBvh):
        def surfaces(q):
            result=Counter()
            for t in q.geometry_primitives:
                p=tuple(tuple(round(float(x),4) for x in q.geometry_vertices[i].co) for i in t.vertices)
                p=min(p,p[1:]+p[:1],p[2:]+p[:2])
                result[(p,tuple(getattr(t.material,f.name) for f in fields(t.material)))]+=1
            return result
        assert surfaces(a)==surfaces(b),'Structural collision surfaces changed'
    for f in fields(a):
        if f.name not in ['user_metadata','children','geometry_vertices','geometry_primitives']:assert equal(getattr(a,f.name),getattr(b,f.name)),f.name

project=json.loads((P/'projeto.json').read_text(encoding='utf-8'));cfg=json.loads((O/'iluminacao_ambiente.json').read_text());actual=[];geometry=[]
for n in ['mansao_teto','mansao_pendentes','mansao_spot_embutido']:
    before=try_load_asset(B/'stream'/f'{n}.ydr');after=try_load_asset(O/'stream'/f'{n}.ydr')
    assert before.models.keys()==after.models.keys()
    for lod in before.models:
        assert len(before.models[lod])==len(after.models[lod])
        for a,b in zip(before.models[lod],after.models[lod]):
            assert len(a.geometries)==len(b.geometries)
            for x,y in zip(a.geometries,b.geometries):
                assert np.array_equal(x.vertex_buffer,y.vertex_buffer),'Vertices, UVs, normals or tangents changed'
                assert np.array_equal(x.index_buffer,y.index_buffer),'Triangles changed'
                assert y.shader_index==(2 if n=='mansao_spot_embutido' and x.shader_index==1 else x.shader_index)
    collision(before.bounds,after.bounds)
    assert equal(before.lod_thresholds,after.lod_thresholds)
    assert before.shader_group.embedded_textures.keys()==after.shader_group.embedded_textures.keys()
    for k,tx in before.shader_group.embedded_textures.items():
        if n=='mansao_spot_embutido' and k=='spot_lente':
            im=Image.open(BytesIO(after.shader_group.embedded_textures[k].data.read_bytes()));pixel=im.getpixel((0,0));assert pixel[0]==pixel[1]==pixel[2]
        else:assert tx.data.read_bytes()==after.shader_group.embedded_textures[k].data.read_bytes(),k
    assert len(before.shader_group.shaders)==len(after.shader_group.shaders)
    for i,(x,y) in enumerate(zip(before.shader_group.shaders,after.shader_group.shaders)):
        emission_changed=(n=='mansao_spot_embutido' and i==2) or (n=='mansao_pendentes' and i==1)
        assert x.preset_filename==y.preset_filename
        if emission_changed:assert y.name=='emissive' or y.name=='hash_8f245469'
        else:assert x.name==y.name,'Unrelated native shader hash changed'
        assert len(x.parameters)==len(y.parameters)
        for q,r in zip(x.parameters,y.parameters):
            if q.name=='emissivemultiplier' and ((n=='mansao_spot_embutido' and i==2) or (n=='mansao_pendentes' and i==1)):
                assert float(r.value[0])==(2.0 if n=='mansao_spot_embutido' else float(np.float32(1.8)))
            else:assert equal(q,r),q.name
    actual+=after.lights;geometry.append(dict(model=n,geometry_uv_normals_indices_identical=True,unrelated_shader_hashes_preserved=True,emissive_shader_key_corrected=n!='mansao_teto',collision_preserved=True,unrelated_texture_bytes_preserved=True))
assert len(actual)==len(project['lights'])==116
assert len({l.light_hash for l in actual})==116
for row,light in zip(project['lights'],actual):
    assert np.allclose(row['position'],light.position,atol=1e-5)
    assert row['rgb']==list(light.color) and math.isclose(row['range'],light.falloff,rel_tol=1e-6)
    assert math.isclose(row['intensity'],light.intensity,rel_tol=1e-6)
    assert light.flashiness==LightFlashiness.CONSTANT and light.time_flags==0xffffff
    assert light.volume_intensity==light.volume_outer_intensity==light.corona_intensity==light.corona_size==0
    assert not light.flags & (1|2|512|32768|1073741824)
    assert light.flags & 16 and light.flags & 16384
    assert light.light_fade_distance>=100
    if row['kind']!='bounce':
        assert light.light_type==LightType.SPOT and np.allclose(light.direction,[0,0,-1])
        assert math.isclose(row['outer_angle'],light.cone_outer_angle) and light.cone_outer_angle>light.cone_inner_angle
        assert light.falloff>row['position'][2]-row['floor_z']+1.0
    else:assert light.light_type==LightType.POINT

def contains(r,p):
    delta=np.array(p)-r['position'];d=np.linalg.norm(delta)
    if d>=r['range']*.97:return False
    if r['kind']=='bounce':return True
    if delta[2]>=0:return False
    return math.degrees(math.acos(max(-1,min(1,-delta[2]/d))))<r['outer_angle']-2
coverage=[]
for region in project['regions']:
    poly=Polygon(region['polygon']);floor=-.8 if region['level']=='terreo' else 2.808
    lights=[r for r in project['lights'] if abs(r['floor_z']-floor)<.01];x0,y0,x1,y1=poly.bounds;n=0;direct=0
    for x in np.arange(x0+.12,x1,.7):
        for y in np.arange(y0+.12,y1,.7):
            if not poly.covers(Point(x,y)):continue
            for z in [floor+.05,floor+1.3]:
                p=[x,y,z];inside=[r for r in lights if contains(r,p)]
                assert inside,(region['name'],p,'No same-floor light coverage')
                direct+=any(r['kind']=='ceiling_white' for r in inside);n+=1
    coverage.append(dict(room=region['name'],level=region['level'],samples=n,ceiling_cone_samples=direct))

l=LuaRuntime(unpack_returned_tuples=True);g=l.globals();g.decode_config=lambda _:l.table_from(cfg,recursive=True)
l.execute('''
json={decode=decode_config};commands={};calls={};camHandle=-1;hour=23;printed={}
local mt={};mt.__index=mt
function vector3(x,y,z) return setmetatable({x=x,y=y,z=z},mt) end
mt.__add=function(a,b) return vector3(a.x+b.x,a.y+b.y,a.z+b.z) end
mt.__sub=function(a,b) return vector3(a.x-b.x,a.y-b.y,a.z-b.z) end
mt.__len=function(a) return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z) end
function GetCurrentResourceName() return 'cidade_mansao' end
function LoadResourceFile(...) return 'config' end
function RegisterCommand(name,fn,_) commands[name]=fn end
function PlayerPedId() return 1 end
function GetEntityCoords(_) return player end
function GetGameplayCamCoord() return camera end
function GetRenderingCam() return camHandle end
function DoesCamExist(_) return true end
function GetCamCoord(_) return drone end
function DrawLightWithRange(...) calls[#calls+1]={...} end
function GetHashKey(s) local a=0;for i=1,#s do a=a+s:byte(i)*i end;return a end
function GetPrevWeatherTypeHashName() return GetHashKey('FOGGY') end
function GetNextWeatherTypeHashName() return GetHashKey('CLEAR') end
function GetTimecycleModifierIndex() return -1 end
function GetExtraTimecycleModifierIndex() return -1 end
function print(s) printed[#printed+1]=s end
function Wait(ms) coroutine.yield(ms) end
function CreateThread(fn) thread=coroutine.create(fn) end
function step() calls={};local ok,err=coroutine.resume(thread);assert(ok,err);return err end
''')
source=(O/'iluminacao_decorativa.lua').read_text(encoding='utf-8');ast.parse(source);ast.parse((O/'luzes_pendentes.lua').read_text())
def world(p):return g.vector3(*[a+b for a,b in zip(cfg['origin'],p)])
g.player=world([0,-1,1]);g.camera=g.player;l.execute(source);assert g.step()==500 and len(g.calls)==0
g.commands.luzmansao(0,l.table_from(['1.5']))
sig=lambda:sorted(tuple(row.values()) for row in g.calls.values())
first=None;cases=0
for p in [[1,-.5,1],[-5,-9,1],[2,-8,1],[11,-9,1],[-6,6,1],[3,-2,4],[-5,6,4],[11,-10,4],[2,11,1]]:
    g.player=world(p);g.camera=g.player
    for hour in [0,5,12,19,23]:
        g.hour=hour;assert g.step()==0 and len(g.calls)==19
        if first is None:first=sig()
        assert sig()==first;cases+=1
g.player=g.vector3(0,0,0);g.camera=g.player;g.camHandle=7;g.drone=world([2,-7,3]);assert g.step()==0 and sig()==first
g.drone=g.player;assert g.step()==500 and len(g.calls)==0
g.commands.luzmansao(0,l.table_from(['99']));g.drone=world([0,0,0]);assert g.step()==0
assert math.isclose(float(g.calls[1][8]),cfg['lights'][0]['intensity'])
g.commands.luzmansao(0,l.table_from(['1']));assert g.step()==500 and len(g.calls)==0
g.commands.mansaoluzes();assert any('FOGGY -> CLEAR' in s for s in g.printed.values())
for forbidden in ['SetWeather','SetTimecycle','SetExtraTimecycle','SetRain','SetArtificialLights','table.sort']:assert forbidden not in source
assert not any(isinstance(e,EntityMloInstance) for e in try_load_asset(D/'stream/cidade_mansao.ymap').entities)
assert all(a.type==ArchetypeType.BASE for a in try_load_asset(D/'stream/cidade_mansao.ytyp').archetypes)
assert not (D/'clima_client.lua').exists()
report=dict(passed=True,native_sources=116,white_ceiling_sources=88,yellow_pendants=9,neutral_low_bounce=19,
    every_fixture_geometrically_reaches_actual_floor=True,coverage=coverage,surface_samples=sum(q['samples'] for q in coverage),
    native_constant_all_hours=True,volumetric_and_corona_sources=0,shadow_sources=sum(q['shadow'] for q in project['lights']),
    geometry_checks=geometry,lua_syntax=True,lua_movement_time_cases=cases,all_room_boost_unchanged=True,drone_verified=True,
    default_light_draws_per_frame=0,weather_diagnostic_only=True,climate_protection_still_removed=True,
    in_game_visual_verified=False,in_game_fps_measured=False)
(P/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('VERIFIED',report['surface_samples'],'floor/body samples;',cases,'Lua movement/time cases; colours, native data, geometry and BASE collision',flush=True)
