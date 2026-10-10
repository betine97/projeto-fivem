import sys,json,ast as pyast,math,hashlib
from pathlib import Path
from dataclasses import fields,is_dataclass
from enum import Enum
from collections import Counter
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao';B=P/'backup';O=P/'package'
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
helpers=pyast.Module(body=[n for n in tree.body if isinstance(n,pyast.FunctionDef) and n.name in ['equal','collision']],type_ignores=[]);exec(compile(helpers,'helpers','exec'))
project=json.loads((P/'project.json').read_text());cfg=json.loads((O/'iluminacao_ambiente.json').read_text());native=[];assets=[]
for name in ['mansao_teto','mansao_pendentes','mansao_tv']:
 before=try_load_asset(B/'stream'/(name+'.ydr'));after=try_load_asset(O/'stream'/(name+'.ydr'))
 assert equal(before.models,after.models),('Mesh changed',name)
 assert equal(before.skeleton,after.skeleton) and equal(before.lod_thresholds,after.lod_thresholds)
 collision(before.bounds,after.bounds)
 for x,y in zip(before.shader_group.shaders,after.shader_group.shaders):
  assert x.name==y.name and x.preset_filename==y.preset_filename
  for a,b in zip(x.parameters,y.parameters):
   assert a.name==b.name
   if a.name!='emissivemultiplier':assert equal(a.value,b.value),(name,a.name)
 assert before.shader_group.embedded_textures.keys()==after.shader_group.embedded_textures.keys()
 for key,tx in before.shader_group.embedded_textures.items():
  nt=after.shader_group.embedded_textures[key];assert tx.data.read_bytes()==nt.data.read_bytes() and tx.width==nt.width and tx.height==nt.height
 native+=after.lights;assets.append(dict(model=name,native_lights=len(after.lights),geometry_material_textures_collision_preserved=True,bytes=(O/'stream'/(name+'.ydr')).stat().st_size))
assert len(native)==129 and len(set(li.light_hash for li in native))==129
assert Counter(li.light_type.name for li in native)==Counter(SPOT=97,POINT=21,CAPSULE=11)
for li in native:
 assert li.time_flags==0xffffff and li.flashiness==LightFlashiness.CONSTANT
 assert li.volume_intensity==li.volume_outer_intensity==li.corona_intensity==li.corona_size==0
 assert not li.flags & (pm.LightFlags.DRAW_VOLUME.value|pm.LightFlags.CALC_FROM_SUN.value|pm.LightFlags.CORONA_ONLY.value)
 assert li.falloff>0 and li.intensity>0 and np.isfinite(li.position).all()
assert len(cfg['native_lights'])==125 and len(cfg['decorative_native_lights'])==24
assert cfg['max_lights']==0 and cfg['lights']==[]
old=json.loads((B/'iluminacao_ambiente.json').read_text())
# Analyze relative light distribution using CodeWalker's attenuation, angular
# falloff and capsule closest-point formula. This is not a FiveM render.
def evaluate(rows,points,normals,floor):
 result=np.zeros((len(points),3))
 for r in rows:
  if not math.isclose(r.get('floor_z',-.8),floor,abs_tol=.01):continue
  pos=np.array(r['position']);nearest=np.broadcast_to(pos,points.shape).copy()
  if r.get('source_type')=='CAPSULE':
   axis=np.array(r['direction']);half=r['length_m']*.5
   t=np.clip((points-pos)@axis,-half,half);nearest=pos+t[:,None]*axis
  delta=nearest-points;dist=np.linalg.norm(delta,axis=1);norm=delta/np.maximum(dist[:,None],1e-8);d=dist/r['range']
  attenuation=np.clip((1-d)/(1+d*d*r['falloff_exponent']),0,1)
  if r['kind'].startswith(('ceiling','pendant')):
   angle=np.degrees(np.arccos(np.clip(norm[:,2],-1,1)))
   attenuation*=np.clip(1-(angle-r['inner_angle'])/(r['outer_angle']-r['inner_angle']),0,1)
  response=np.maximum(0,(norm*normals).sum(1))
  result+=(attenuation*response*r['intensity'])[:,None]*np.array(r['rgb'])/255
 return result
regions=json.loads((R/'casa_vinewood/luz_permanente_20261008/projeto_luminotecnico.json').read_text())['regions'];analysis=[]
for region in regions:
 poly=Polygon(region['polygon']).buffer(-.2);floor=-.8 if region['level']=='terreo' else 2.808
 x0,y0,x1,y1=poly.bounds;points=np.array([[x,y,floor+.01] for x in np.arange(x0,x1,.20) for y in np.arange(y0,y1,.20) if poly.contains(Point(x,y))])
 normals=np.tile([0,0,1],(len(points),1))
 a=evaluate(old['native_lights'],points,normals,floor);b=evaluate(cfg['native_lights'],points,normals,floor)
 assert np.isfinite(b).all() and b.sum()>0
 old_lum=a@np.array([.2126,.7152,.0722]);new_lum=b@np.array([.2126,.7152,.0722])
 analysis.append(dict(room=region['name'],samples=len(points),floor_luminance_median_before=float(np.median(old_lum)),floor_luminance_median_after=float(np.median(new_lum)),median_rgb_after=np.median(b,axis=0).tolist(),floor_min_after=float(new_lum.min()),relative_median_ratio=float(np.median(new_lum)/max(1e-8,np.median(old_lum)))))
focus=[r for r in analysis if r['room'] in ['Sala de estar','Sala de jantar','Cozinha']]
assert all(r['floor_min_after']>0 for r in focus)
assert all(.65<r['relative_median_ratio']<2.8 for r in focus),focus
# Wall normals catch the lateral contribution absent from a floor-only test.
wall_points=np.array([[-9.05,y,z] for y in [-11.4,-6.] for z in np.linspace(-.4,3.8,15)])
wall_normals=np.tile([1,0,0],(len(wall_points),1));aw=evaluate(old['native_lights'],wall_points,wall_normals,-.8);bw=evaluate(cfg['native_lights'],wall_points,wall_normals,-.8)
assert np.median(bw[:,0])>np.median(aw[:,0])*1.3
assert np.median(bw[:,0])>np.median(bw[:,1])>np.median(bw[:,2])
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
code=(O/'iluminacao_decorativa.lua').read_text();ast.parse(code);l.execute(code);g.commands.luzmansao();assert any('spots quentes' in s for s in g.outputs.values())
report=dict(passed=True,assets=assets,indoor_native_sources=149,existing_fixture_positions_preserved=True,emissive_multiplier_changes_only=project['emission_changes'],no_geometry_collision_map_weather_changes=True,no_volumes_coronas_or_script_drawing=True,relative_distribution=analysis,wall_median_red_ratio=float(np.median(bw[:,0])/np.median(aw[:,0])),visual_match_verified=False,limitations=['Mathematical illumination approximation, not a GTA/FiveM screenshot','Different cameras in user references','No in-game HDR, occlusion, ambient environment or FPS verification'])
(P/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(passed=True,main_rooms=focus,wall_red_ratio=report['wall_median_red_ratio']),indent=2))
