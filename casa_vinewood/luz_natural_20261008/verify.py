"""Validate native models and scope. No claim of in-game exposure or FPS."""
import sys,json,math,ast as pyast,hashlib
from pathlib import Path
from dataclasses import fields,is_dataclass
from enum import Enum
from collections import Counter
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao';B=P/'backup';O=P/'package'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',str(R/'casa_vinewood/work/lua_syntax_deps')]
import numpy as np
from szio.gta5 import try_load_asset
from szio.gta5.bounds import AssetBoundComposite,AssetBoundBvh
from szio.gta5.drawables import LightType,LightFlashiness
from luaparser import ast
from lupa import LuaRuntime
import pymateria.gta5 as pm
tree=pyast.parse((R/'casa_vinewood/luminarias_cor_alcance_20261008/verify.py').read_text(encoding='utf-8'))
helpers=pyast.Module(body=[n for n in tree.body if isinstance(n,pyast.FunctionDef) and n.name in ['equal','collision']],type_ignores=[]);exec(compile(helpers,'comparison_helpers','exec'))
project=json.loads((P/'projeto.json').read_text());cfg=json.loads((O/'iluminacao_ambiente.json').read_text());report=[];native=[];pairs=[]
names=['mansao_teto','mansao_pendentes','mansao_spots_led','mansao_tv']
for name in names:
 before=try_load_asset(B/'stream'/(name+'.ydr'));after=try_load_asset(O/'stream'/(name+'.ydr'))
 assert before.name==after.name;assert equal(before.models,after.models),f'Geometry or materials changed: {name}'
 assert equal(before.skeleton,after.skeleton) and equal(before.lod_thresholds,after.lod_thresholds)
 collision(before.bounds,after.bounds)
 assert equal(before.shader_group.shaders,after.shader_group.shaders),f'Shader changed: {name}'
 assert before.shader_group.embedded_textures.keys()==after.shader_group.embedded_textures.keys()
 for key,tx in before.shader_group.embedded_textures.items():
  nt=after.shader_group.embedded_textures[key]
  assert tx.width==nt.width and tx.height==nt.height and tx.data.read_bytes()==nt.data.read_bytes(),f'Texture changed: {name}/{key}'
 if name in ['mansao_teto','mansao_pendentes']:
  count=88 if name=='mansao_teto' else 9
  assert len(before.lights)==count and len(after.lights)==count+(21 if name=='mansao_teto' else 0)
  for a,b in zip(before.lights,after.lights):
   for f in fields(a):
    if f.name not in ['intensity','falloff','falloff_exponent','cone_inner_angle','cone_outer_angle','color','volume_outer_color','user_metadata']:
     assert equal(getattr(a,f.name),getattr(b,f.name)),f'Unrequested source change {name}/{f.name}'
   assert b.light_type==LightType.SPOT and np.allclose(b.direction,[0,0,-1])
   assert b.intensity<a.intensity*.28 and b.cone_inner_angle==0 and b.cone_outer_angle>a.cone_outer_angle
   assert b.falloff_exponent==4 and b.light_fade_distance>=120
   if name=='mansao_teto':assert tuple(b.color)==(255,255,255)
   else:assert tuple(b.color)==(255,208,140)
   pairs.append((a,b))
 elif name=='mansao_spots_led':
  assert len(after.lights)==len(before.lights)==20
  for i,(a,b) in enumerate(zip(before.lights,after.lights)):
   assert equal(a.position,b.position) and a.light_hash==b.light_hash
   assert b.light_type==LightType.CAPSULE and np.allclose(b.direction,[1,0,0])
   assert np.allclose(b.extent,[project['stairs'][i]['length_m']]*3)
 elif name=='mansao_tv':
  assert len(after.lights)==1 and len(before.lights)==3
  li=after.lights[0];assert li.light_type==LightType.CAPSULE and np.allclose(li.direction,[0,1,0])
  assert np.allclose(li.extent,[2.193]*3) and np.allclose(li.position,np.mean([x.position for x in before.lights],axis=0))
  assert li.flags & pm.LightFlags.MOVING_LIGHT_SOURCE.value
 native+=after.lights
 report.append(dict(model=name,geometry_materials_textures_lods_collision_identical=True,before_lights=len(before.lights),after_lights=len(after.lights),before_bytes=(B/'stream'/(name+'.ydr')).stat().st_size,after_bytes=(O/'stream'/(name+'.ydr')).stat().st_size))
assert len(native)==139 and len(set(l.light_hash for l in native))==139
assert Counter(l.light_type.name for l in native)==Counter(SPOT=97,POINT=21,CAPSULE=21)
for li in native:
 assert li.time_flags==0xffffff and li.flashiness==LightFlashiness.CONSTANT
 assert li.volume_intensity==li.volume_outer_intensity==li.corona_intensity==li.corona_size==0
 assert not li.flags & (pm.LightFlags.DRAW_VOLUME.value|pm.LightFlags.CALC_FROM_SUN.value|pm.LightFlags.CORONA_ONLY.value)
 assert li.light_fade_distance>=100
 if li.light_type!=LightType.SPOT:
  assert li.flags & pm.LightFlags.NO_SPECULAR.value and not li.flags & pm.LightFlags.CAST_SHADOWS.value
assert sum(bool(li.flags & pm.LightFlags.CAST_SHADOWS.value) for li in native)==sum(bool(a.flags & pm.LightFlags.CAST_SHADOWS.value) for a,b in pairs)==1
mapping={r['id']:r for r in cfg['native_lights']}
for row,li in zip([r for r in cfg['native_lights'] if r['kind']=='ceiling_white']+project['bounce'],native[:109]):
 assert np.allclose(row['position'],li.position,atol=1e-5) and row['rgb']==list(li.color)
 assert math.isclose(row['intensity'],li.intensity,rel_tol=1e-6) and math.isclose(row['range'],li.falloff,rel_tol=1e-6)
 if row['kind']=='bounce':
  assert li.light_type==LightType.POINT and li.flags & pm.LightFlags.USE_CULL_PLANE.value
  assert np.allclose(li.culling_plane_normal,[0,0,1])
  floor=row['floor_z']
  # CodeWalker plane convention: positive signed result rejects the sample.
  value=lambda z:li.position[2]-z-li.culling_plane_offset
  assert value(floor)<0 and value(floor-.1)>0
 else:
  h=row['position'][2]-row['floor_z'];radius=h*math.tan(math.radians(li.cone_outer_angle))
  assert math.isclose(radius,row['floor_radius_m'],rel_tol=1e-6) and li.falloff>math.hypot(h,radius)
assert cfg['native_count']==139 and cfg['native_bounce_count']==21 and cfg['max_lights']==0 and cfg['lights']==[]
full_count=0;unrelated_sources=0
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();baseline=json.loads((P/'baseline.json').read_text())
for file in (D/'stream').glob('*.ydr'):
 replacement=O/'stream'/file.name;a=try_load_asset(replacement if replacement.exists() else file);full_count+=len(a.lights)
 if file.stem not in names:
  assert sha(file)==baseline[file.relative_to(D).as_posix()],'Unrelated live model changed'
  unrelated_sources+=len(a.lights)
assert full_count==139+unrelated_sources
l=LuaRuntime(unpack_returned_tuples=True);g=l.globals();g.cfg=lambda _:l.table_from(cfg,recursive=True)
l.execute('''json={decode=cfg};commands={};outputs={}
function LoadResourceFile(...) return 'config' end
function GetCurrentResourceName() return 'cidade_mansao' end
function RegisterCommand(n,f,_) commands[n]=f end
function CreateThread(...) error('Unexpected draw thread') end
function DrawLightWithRange(...) error('Unexpected Lua light') end
function GetHashKey(s) return s end
function GetPrevWeatherTypeHashName() return 'CLEAR' end
function GetNextWeatherTypeHashName() return 'RAIN' end
function GetTimecycleModifierIndex() return -1 end
function GetExtraTimecycleModifierIndex() return -1 end
function print(s) outputs[#outputs+1]=s end''')
s=(O/'iluminacao_decorativa.lua').read_text(encoding='utf-8');ast.parse(s);l.execute(s);g.commands.luzmansao();g.commands.mansaoluzes()
assert any('21 preenchimentos' in o for o in g.outputs.values()) and any('escada 20 e TV 1' in o for o in g.outputs.values())
assert any('CLEAR -> RAIN' in o for o in g.outputs.values())
assert all(sha(D/t)==baseline[t] for t in project['targets']),'Concurrent lighting target edit'
result=dict(passed=True,native_sources_in_changed_models=139,resource_native_sources=full_count,unrelated_native_sources_preserved=unrelated_sources,types=dict(Counter(l.light_type.name for l in native)),checks=report,all_fixture_positions_preserved=True,only_one_existing_shadow_source_in_changed_models=True,no_volumes_coronas_weather_filters_or_script_draw_threads=True,in_game_visual_verified=False)
(P/'verification.json').write_text(json.dumps(result,indent=2));print('VERIFIED: exact geometry/material/texture preservation; native soft focus, clipped indirect fill, linear LEDs; Lua diagnostics.',flush=True)
