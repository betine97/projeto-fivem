"""Round-trip fixture/map validation, native plant collision and runtime behavior."""
import sys,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';OUT=W/'decor_fivem';DECOROUT=OUT
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/lua_syntax_deps'),str(W/'work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import try_load_asset
from lupa import LuaRuntime
from luaparser import ast
cfg=json.loads((W/'decoracao_iluminacao.json').read_text());origin=np.array(cfg['origin'])
fixture=try_load_asset(OUT/'mansao_spots_led.ydr');assert fixture is not None and fixture.bounds is None
geos=[g for lod in fixture.models.values() for m in lod for g in m.geometries]
triangles=0
for g in geos:
 vs=g.vertex_buffer;assert np.isfinite(vs['Position']).all() and np.isfinite(vs['Normal']).all()
 t=vs['Position'][g.index_buffer.reshape(-1,3)];area=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)*.5;assert min(area)>1e-10;triangles+=len(t)
assert any(s.preset_filename=='emissive.sps' for s in fixture.shader_group.shaders)
mp=try_load_asset(OUT/'mansao_decoracao.ymap');typ=try_load_asset(OUT/'mansao_decoracao.ytyp');assert len(typ.archetypes)==2 and len(mp.entities)==23
for row,entity in zip(cfg['plants'],mp.entities[1:]):
 assert str(entity.archetype_name)==row['model'];assert np.max(abs(np.array(entity.position)-origin-row['position']))<.0001
 assert abs(entity.scale_xy-row['scale'])<.00001
 assert .9<row['height_m']<2.1
assert len(cfg['spots'])==88 and len(cfg['stairs'])==20 and len(cfg['plants'])==17
assert len({q['name'] for q in cfg['stairs']})==20
assert sum(q['level']=='superior' for q in cfg['spots'])>30
rug=try_load_asset(OUT/'mansao_tapete_sala.ydr');assert rug.bounds is None
rg=[g for lod in rug.models.values() for m in lod for g in m.geometries]
rug_triangles=sum(len(g.index_buffer)//3 for g in rg);assert rug_triangles<=46000
for g in rg:
 assert np.isfinite(g.vertex_buffer['Position']).all() and np.isfinite(g.vertex_buffer['Normal']).all()
 assert np.isfinite(g.vertex_buffer['TexCoord0']).all()
 ps=g.vertex_buffer['Position'];assert ps[:,2].min()>-.8 and ps[:,2].max()<-.77
assert len(rug.shader_group.embedded_textures)==3
assert str(mp.entities[18].archetype_name)=='mansao_tapete_sala'
assert len(cfg['paintings'])==4 and len({p['model'] for p in cfg['paintings']})==4
for row,entity in zip(cfg['paintings'],mp.entities[19:]):
 assert str(entity.archetype_name)==row['model']
 assert np.max(abs(np.array(entity.position)-origin-row['position']))<.0001
 assert np.max(abs(np.array(entity.rotation)-row['quaternion']))<.0001
 assert row['floor_z']==-.8
 # Native art is a shallow wall prop, entirely above the walking capsule's lower body.
 assert row['bounds']['hi'][1]-row['bounds']['lo'][1]<.06
# Reuse the actual native architecture collision test, then add the new pots.
source=(W/'work/verify_fit.py').read_text()
exec(source.split('routes={}')[0])
for row in cfg['plants']:
 a=try_load_asset(W/'work/decor_native'/(row['model']+'.ydr'))
 tx=np.eye(4);tx[:3,:3]*=row['scale']
 visit(a.bounds,parent=tx,offset=np.array(row['position']),label='decor_plant_'+row['name'])
for row in cfg['paintings']:
 a=try_load_asset(W/'work/decor_art'/(row['model']+'.ydr'))
 angle=row['heading'];cs=np.cos(angle);sn=np.sin(angle);tx=np.eye(4)
 tx[:3,:3]=np.array([[cs,-sn,0],[sn,cs,0],[0,0,1]])*row['scale']
 visit(a.bounds,parent=tx,offset=np.array(row['position']),label='decor_art_'+row['name'])
# Update the collision acceleration arrays after adding plant primitives.
T=np.array(faces);low=T.min(1);high=T.max(1);norm=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0])
SL=np.array([ps.min(0)-pad for kind,ps,pad,label in smooth]);SH=np.array([ps.max(0)+pad for kind,ps,pad,label in smooth])
exec('routes={}\n'+source.split('routes={}')[1].split("fit=json.loads")[0])
route('Passagem entre sofa e jantar',[(-.5,-10.85,-.8),(.8,-10.85,-.8),(4.5,-10.85,-.8)])
route('Passagem cozinha',[(8.85,-11.05,-.8),(11.35,-11.05,-.8),(11.35,-6.95,-.8)])
route('Volta completa da mesa',[(.8,-10.85,-.8),(4.5,-10.85,-.8),(4.5,-5.8,-.8),(.8,-5.8,-.8),(.8,-10.85,-.8)])
route('Entre jantar e cozinha',[(4.5,-8.3,-.8),(8.85,-8.3,-.8)])
assert all(q['passed'] for q in routes.values()),{k:v for k,v in routes.items() if not v['passed']}
for row in cfg['plants']:assert support(np.array([*row['position'][:2],row['floor_z']])),row['name']
# Exercise the actual Lua loop: nearby, far, camera-only, capped shadow lights.
lua=LuaRuntime(unpack_returned_tuples=True);g=lua.globals()
def table(v):
 if isinstance(v,dict):return lua.table_from({k:table(x) for k,x in v.items()})
 if isinstance(v,list):return lua.table_from([table(x) for x in v])
 return v
g.test_config=table(cfg)
lua.execute('''
local mt={__add=function(a,b) return vector3(a.x+b.x,a.y+b.y,a.z+b.z) end,__sub=function(a,b) return vector3(a.x-b.x,a.y-b.y,a.z-b.z) end,__len=function(a) return math.sqrt(a.x*a.x+a.y*a.y+a.z*a.z) end}
function vector3(x,y,z) return setmetatable({x=x,y=y,z=z},mt) end
coords=vector3(test_config.origin[1],test_config.origin[2],test_config.origin[3]);camera=coords;calls={};timer=0
clockhour=12;clockminute=0
function GetClockHours() return clockhour end
function GetClockMinutes() return clockminute end
json={decode=function(_) return test_config end}
function GetCurrentResourceName() return 'cidade_mansao' end
function LoadResourceFile(_,_) return '' end
function CreateThread(f) thread=coroutine.create(f) end
function Wait(t) delay=t;coroutine.yield() end
function PlayerPedId() return 1 end
function GetGameTimer() return timer end
function GetEntityCoords(_) return coords end
function GetGameplayCamCoord() return camera end
function DrawLightWithRange(...) table.insert(calls,{kind='stair',args={...}}) end
function DrawSpotLight(...) table.insert(calls,{kind='spot',args={...}}) end
function DrawSpotLightWithShadow(...) table.insert(calls,{kind='shadow',args={...}}) end
function frame() local ok,err=coroutine.resume(thread);assert(ok,err) end
''')
script=(W/'work/iluminacao_decorativa.lua').read_text();ast.parse(script);lua.execute(script);g.frame()
rows=[g.calls[i] for i in range(1,len(g.calls)+1)];assert sum(r['kind']=='shadow' for r in rows)==6;assert sum(r['kind'] in ('spot','shadow') for r in rows)<=18
assert g.delay==0 and any(r['kind']=='stair' for r in rows)
for r in rows:
 if r['kind'] in ('spot','shadow'):assert r['args'][6]==-1 and r['args'][3]>origin[2]+2
day=[r['args'][11] for r in rows if r['kind'] in ('spot','shadow')]
for hour,minute,multiplier in [(22,0,4),(19,0,2.5),(6,30,2.5),(8,0,1),(5,0,4),(18,0,1)]:
 g.clockhour=hour;g.clockminute=minute;g.calls=lua.table();g.frame()
 values=[g.calls[i]['args'][11] for i in range(1,len(g.calls)+1) if g.calls[i]['kind'] in ('spot','shadow')]
 assert np.allclose(values,np.array(day)*multiplier),(hour,minute,values,day)
g.coords=g.vector3(-500,676,157);g.camera=g.coords;g.calls=lua.table();g.timer=1000;g.frame();assert len(g.calls)==0 and g.delay==1000
g.camera=g.vector3(*origin);g.timer=2000;g.frame();assert len(g.calls)>0 and g.delay==0
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in DECOROUT.iterdir() if p.suffix in ('.ydr','.ymap','.ytyp')}
report=dict(passed=True,revision=cfg['revision'],spots=len(cfg['spots']),stair_led_strips=len(cfg['stairs']),native_plants=len(cfg['plants']),native_paintings=4,rug_triangles=rug_triangles,rug_uv_finite=True,rug_no_collision=True,night_multiplier=4,fixture_triangles=triangles,fixture_no_collision=True,walking_routes=routes,native_map_roundtrip=True,runtime_cases=9,max_spotlights=18,max_shadow_lights=6,files=hashes,in_game_verified=False)
(W/'verificacao_decoracao_iluminacao.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('DECOR_VERIFIED',len(routes),'walking routes;',triangles,'fixture triangles; runtime lights capped; native roundtrip OK',flush=True)
