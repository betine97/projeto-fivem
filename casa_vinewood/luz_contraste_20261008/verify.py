import sys,json,ast as pyast,math,hashlib
from pathlib import Path
from collections import Counter
from dataclasses import fields,is_dataclass
from enum import Enum
P=Path(__file__).resolve().parent;R=P.parents[1];B=P/'backup';O=P/'package'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(R/'casa_vinewood/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',str(R/'casa_vinewood/work/lua_syntax_deps')]
import numpy as np
from szio.gta5 import *
from szio.gta5.bounds import AssetBoundComposite,AssetBoundBvh
from szio.gta5.drawables import LightType,LightFlashiness
import pymateria.gta5 as pm
from shapely.geometry import Polygon,Point
from luaparser import ast
from lupa import LuaRuntime
tree=pyast.parse((R/'casa_vinewood/luminarias_cor_alcance_20261008/verify.py').read_text())
exec(compile(pyast.Module(body=[n for n in tree.body if isinstance(n,pyast.FunctionDef) and n.name in ['equal','collision']],type_ignores=[]),'helpers','exec'))
project=json.loads((P/'project.json').read_text());cfg=json.loads((O/'iluminacao_ambiente.json').read_text());old=json.loads((B/'iluminacao_ambiente.json').read_text())
assets=[];native=[]
allowed={'position','color','volume_outer_color','intensity','flags','specular_fade_distance','culling_plane_offset'}
for name in ['mansao_teto','mansao_pendentes','mansao_tv']:
 a=try_load_asset(B/'stream'/(name+'.ydr'));b=try_load_asset(O/'stream'/(name+'.ydr'))
 assert equal(a.models,b.models) and equal(a.skeleton,b.skeleton) and equal(a.lod_thresholds,b.lod_thresholds)
 collision(a.bounds,b.bounds)
 assert len(a.lights)==len(b.lights)
 for x,y in zip(a.lights,b.lights):
  for f in fields(x):
   if f.name not in allowed:assert equal(getattr(x,f.name),getattr(y,f.name)),(name,f.name)
  assert y.flags&pm.LightFlags.NO_SPECULAR.value
  assert y.intensity<x.intensity and y.volume_intensity==y.volume_outer_intensity==y.corona_intensity==y.corona_size==0
  assert y.time_flags==0xffffff and y.flashiness==LightFlashiness.CONSTANT
  if not equal(x.position,y.position):
   assert name=='mansao_teto' and x.light_type==LightType.POINT
   assert np.allclose(np.array(y.position)-np.array(x.position),[0,0,.85])
   assert math.isclose(y.culling_plane_offset-x.culling_plane_offset,.85,abs_tol=1e-5)
 for x,y in zip(a.shader_group.shaders,b.shader_group.shaders):
  assert x.name==y.name and x.preset_filename==y.preset_filename
  for u,v in zip(x.parameters,y.parameters):
   assert u.name==v.name
   if u.name!='emissivemultiplier':assert equal(u.value,v.value)
 for k,tx in a.shader_group.embedded_textures.items():
  nt=b.shader_group.embedded_textures[k];assert tx.data.read_bytes()==nt.data.read_bytes() and tx.width==nt.width and tx.height==nt.height
 native+=b.lights;assets.append(dict(model=name,native_lights=len(b.lights),meshes_collision_textures_preserved=True))
assert len(native)==129 and len({li.light_hash for li in native})==129
assert Counter(li.light_type.name for li in native)==Counter(SPOT=97,POINT=21,CAPSULE=11)
assert cfg['native_count']==149 and len(cfg['native_lights'])==125 and len(cfg['decorative_native_lights'])==24
assert cfg['max_lights']==0 and cfg['lights']==[]
rows={r['id']:r for r in cfg['native_lights']}
for r in old['native_lights']:
 n=rows[r['id']]
 if r['kind']!='bounce':assert n['position']==r['position']
 assert n['range']==r['range'] and n['inner_angle']==r['inner_angle'] and n['outer_angle']==r['outer_angle']
assert all(not any(s in n.lower() for s in ['fog','rain','weather','exposure']) for n in cfg['clean_postfx']['variables'])

tree=pyast.parse((R/'casa_vinewood/luz_referencia_quente_20261008/verify.py').read_text())
exec(compile(pyast.Module(body=[n for n in tree.body if isinstance(n,pyast.FunctionDef) and n.name=='evaluate'],type_ignores=[]),'distribution','exec'))
analysis=[]
regions=json.loads((R/'casa_vinewood/luz_permanente_20261008/projeto_luminotecnico.json').read_text())['regions']
for region in regions[:3]:
 poly=Polygon(region['polygon']).buffer(-.2);x0,y0,x1,y1=poly.bounds
 points=np.array([[x,y,-.79] for x in np.arange(x0,x1,.2) for y in np.arange(y0,y1,.2) if poly.contains(Point(x,y))]);normals=np.tile([0,0,1],(len(points),1))
 before=evaluate(old['native_lights'],points,normals,-.8)@np.array([.2126,.7152,.0722]);after=evaluate(cfg['native_lights'],points,normals,-.8)@np.array([.2126,.7152,.0722])
 ratio=float(np.median(after)/np.median(before));assert .2<ratio<.65 and after.min()>0
 analysis.append(dict(room=region['name'],samples=len(points),relative_diffuse_floor_median=ratio))

code=(O/'iluminacao_decorativa.lua').read_text();ast.parse(code)
cases=[]
def runtime(fail=False,no_vars=False):
 l=LuaRuntime(unpack_returned_tuples=True);g=l.globals();g.cfg=lambda _:l.table_from(cfg,recursive=True)
 l.execute('''json={decode=cfg}; commands={};events={};calls={};outputs={}; extra=-1;primary=14;created=71
 cam={x=-981.1010131835938,y=671.7308959960938,z=159.3350372314453}
 vars={'postfx_intensity_bloom','postfx_noise','screen_blur_intensity','dof_blur_mid','dof_blur_far'}
 function LoadResourceFile(...) return 'cfg' end
 function GetCurrentResourceName() return 'cidade_mansao' end
 function RegisterCommand(n,f,_) commands[n]=f end
 function AddEventHandler(n,f) events[n]=f end
 function CreateThread(f) thread=coroutine.create(f) end
 function Wait(ms) assert(ms==250);coroutine.yield() end
 function step() local ok,e=coroutine.resume(thread);assert(ok,e) end
 function GetGameplayCamCoord() return cam end
 function GetTimecycleVarCount() return #vars end
 function GetTimecycleVarNameByIndex(i) return vars[i+1] end
 function GetTimecycleModifierIndexByName(n) return -1 end
 function CreateTimecycleModifier(n) calls.create=n;return created end
 function SetTimecycleModifierVar(n,k,a,b) assert(a==b);calls[k]=a end
 function RemoveTimecycleModifier(n) calls.remove=n end
 function SetExtraTimecycleModifier(n) extra=71;calls.set=(calls.set or 0)+1 end
 function GetExtraTimecycleModifierIndex() return extra end
 function ClearExtraTimecycleModifier() extra=-1;calls.clear=(calls.clear or 0)+1 end
 function GetTimecycleModifierIndex() return primary end
 function GetTimecycleModifierNameByIndex(i) return 'filter_'..i end
 function GetHashKey(s) return s end
 function GetPrevWeatherTypeHashName() return 'CLEAR' end
 function GetNextWeatherTypeHashName() return 'RAIN' end
 function print(s) outputs[#outputs+1]=s end
 function DrawLightWithRange(...) error('Unexpected drawn light') end
 function DrawSpotLight(...) error('Unexpected drawn light') end
 function SetWeatherTypeNow(...) error('Weather changed') end
 function SetTimecycleModifier(...) error('Primary filter changed') end''')
 if fail:g.created=-1
 if no_vars:l.execute('vars={}')
 l.execute(code);g.step();return l,g
l,g=runtime();assert g.extra==71 and g.primary==14
assert g.calls.postfx_intensity_bloom==.08 and g.calls.dof_blur_far==0;cases.append('Only five supported optical variables; inside camera applies profile')
g.cam.x=-1020;g.step();assert g.extra==-1;cases.append('Leaving house clears only owned profile')
g.cam.x=-981.1010131835938;g.extra=90;g.step();assert g.extra==90 and g.calls.set==1;cases.append('Foreign extra filter preserved')
g.extra=-1;g.step();assert g.extra==71
g.commands.luzmansao(0,l.table_from(['original']));assert g.extra==-1
g.commands.luzmansao(0,l.table_from(['limpo']));assert g.extra==71;cases.append('F8 comparison commands work')
g.events.onResourceStop('other');assert g.extra==71
g.events.onResourceStop('cidade_mansao');assert g.extra==-1 and g.calls.remove==cfg['clean_postfx']['modifier'];cases.append('Resource stop removes own modifier')
l,g=runtime();g.extra=90;g.events.onResourceStop('cidade_mansao');assert g.extra==90;cases.append('Cleanup cannot clear replacement filter')
l,g=runtime(fail=True);assert g.extra==-1 and g.calls.set is None;cases.append('Unavailable API profile fails without changing game filters')
l,g=runtime(no_vars=True);assert g.extra==-1 and g.calls.remove is not None;cases.append('Missing variables remove unused profile')
report=dict(passed=True,assets=assets,light_count_unchanged=True,geometry_collision_textures_preserved=True,no_weather_fog_or_primary_filter_changes=True,relative_floor_distribution=analysis,lua_lifecycle_cases=cases,visual_match_verified=False,sha256={r:hashlib.sha256((O/r).read_bytes()).hexdigest() for r in project['targets']})
(P/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(passed=True,distribution=analysis,lua_cases=len(cases)),indent=2))
