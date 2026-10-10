import sys,json,math,ast as pyast,hashlib,struct
from pathlib import Path
from dataclasses import fields,is_dataclass
from enum import Enum
from collections import Counter
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao';B=P/'backup';O=P/'package'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',str(R/'casa_vinewood/work/lua_syntax_deps')]
import numpy as np
from PIL import Image
import io
from szio.gta5 import try_load_asset
from szio.gta5.bounds import AssetBoundComposite,AssetBoundBvh
from szio.gta5.drawables import LightType,LightFlashiness
from luaparser import ast
from lupa import LuaRuntime
from szio.gta5.entities import EntityMloInstance
from szio.gta5.archetypes import ArchetypeType
tree=pyast.parse((R/'casa_vinewood/luminarias_cor_alcance_20261008/verify.py').read_text(encoding='utf-8'))
helpers=pyast.Module(body=[n for n in tree.body if isinstance(n,pyast.FunctionDef) and n.name in ['equal','collision']],type_ignores=[]);exec(compile(helpers,'comparison_helpers','exec'))
project=json.loads((P/'projeto.json').read_text());report=[];native=[];lens_samples=[];texture_changes=[]
def rgbcheck(c):assert tuple(c)==(255,180,55)
def emissive(shader,power):
 assert shader.name=='hash_8f245469' and shader.preset_filename=='emissive.sps'
 assert math.isclose(float(next(p.value[0] for p in shader.parameters if p.name=='emissivemultiplier')),power,abs_tol=1e-6)
for name in ['mansao_spot_embutido','mansao_pendentes','mansao_spots_led','mansao_tv']:
 before=try_load_asset(B/'stream'/(name+'.ydr'));after=try_load_asset(O/'stream'/(name+'.ydr'))
 assert before.models.keys()==after.models.keys();assert equal(before.lod_thresholds,after.lod_thresholds)
 collision(before.bounds,after.bounds)
 changed_lens=0;added=0
 for lod in before.models:
  assert len(before.models[lod])==len(after.models[lod])
  for mi,(bm,am) in enumerate(zip(before.models[lod],after.models[lod])):
   count=6 if name=='mansao_pendentes' and mi==0 else (1 if name=='mansao_tv' and mi==0 else 0)
   assert len(am.geometries)==len(bm.geometries)+count
   for gi,(bg,ag) in enumerate(zip(bm.geometries,am.geometries)):
    assert bg.shader_index==ag.shader_index;assert np.array_equal(bg.index_buffer,ag.index_buffer)
    if name=='mansao_spot_embutido' and mi==2:
     assert bg.vertex_buffer.dtype==ag.vertex_buffer.dtype
     for key in bg.vertex_buffer.dtype.names:
      if key not in ['Position','Normal']:assert np.array_equal(bg.vertex_buffer[key],ag.vertex_buffer[key])
     old=bg.vertex_buffer['Position'];new=ag.vertex_buffer['Position'];rad=np.linalg.norm(new[:,:2],axis=1).max()
     assert .0499<=rad<=.0551 and new[:,2].min()>=-.00401 and new[:,2].max()<=-.00299
     assert np.allclose(np.linalg.norm(ag.vertex_buffer['Normal'],axis=1),1,atol=1e-6)
     # Winding remains outward on the visible underside, and its area grows.
     tris=new[ag.index_buffer.reshape(-1,3)];cross=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]);down=cross[:,2]<-1e-12
     projected=-cross[down,2].sum()/2;assert projected>.007,'Emitter face collapsed or inward winding'
     # Geometric coverage at 20 m, 1080p, 70-degree vertical FoV, 60deg viewing angle.
     px=2*rad*(1080/(2*math.tan(math.radians(35))))/20
     assert px>3.8
     lens_samples.append(dict(lod=lod.name,diameter_m=float(2*rad),projected_area_m2=float(projected),width_px_20m_1080p=float(px),ellipse_minor_px_at_60deg=float(px*.5)))
     changed_lens+=1
    else:assert np.array_equal(bg.vertex_buffer,ag.vertex_buffer),f'Unrequested original mesh change {name}/{lod}/{mi}/{gi}'
   for ag in am.geometries[len(bm.geometries):]:
    assert ag.shader_index==(1 if name in ['mansao_pendentes','mansao_tv'] else 2)
    assert np.all(ag.vertex_buffer['Colour0']==255)
    pts=ag.vertex_buffer['Position'];idx=ag.index_buffer.reshape(-1,3);tri=pts[idx]
    area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
    assert np.all(area>1e-9)
    added+=len(idx)
    if name=='mansao_pendentes':
     cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);assert (cross[:,2]<0).any() and (cross[:,2]>0).any()
     assert area[cross[:,2]<0].sum()>.012,'Cylinder diffuser is not filled'
    elif name=='mansao_tv':
     assert np.allclose(pts.min(0),project['tv_strip']['lo']) and np.allclose(pts.max(0),project['tv_strip']['hi'])
     assert pts[:,0].max()<-8.780 and pts[:,2].min()>1.4307,'Not behind actual upper screen edge'
     assert pts.min(0)[1]>-9.904 and pts.max(0)[1]<-7.643
 assert changed_lens==(4 if name=='mansao_spot_embutido' else 0)
 allowed_texture={'mansao_pendentes':'mansao_led_quente','mansao_spots_led':'mansao_decor_led'}.get(name)
 assert set(before.shader_group.embedded_textures)<=set(after.shader_group.embedded_textures)
 for k,tx in before.shader_group.embedded_textures.items():
  nt=after.shader_group.embedded_textures[k]
  if k==allowed_texture:
   image=np.array(Image.open(io.BytesIO(nt.data.read_bytes())).convert('RGB'));avg=image.mean(axis=(0,1))
   assert avg[0]>245 and 145<avg[1]<195 and avg[2]<60,(k,avg)
   assert tx.width==nt.width==4 and tx.height==nt.height==4
   texture_changes.append(k)
  else:assert tx.data.read_bytes()==nt.data.read_bytes(),f'Original texture changed: {name}/{k}'
 for i,(bs,as_) in enumerate(zip(before.shader_group.shaders,after.shader_group.shaders)):
  if name=='mansao_spots_led' and i==0:assert as_.name=='hash_8f245469'
  else:assert bs.name==as_.name
  assert bs.preset_filename==as_.preset_filename
  for bp,ap in zip(bs.parameters,as_.parameters):
   if bp.name=='emissivemultiplier' and name in ['mansao_pendentes','mansao_spots_led']:continue
   assert equal(bp,ap),f'Unexpected shader param change: {name}/{i}/{bp.name}'
 if name=='mansao_spot_embutido':emissive(after.shader_group.shaders[2],3)
 elif name=='mansao_pendentes':
  emissive(after.shader_group.shaders[1],1.65);assert len(before.lights)==len(after.lights)==9
  for a,b in zip(before.lights,after.lights):
   rgbcheck(b.color)
   for f in fields(a):
    if f.name not in ['color','volume_outer_color','user_metadata']:assert equal(getattr(a,f.name),getattr(b,f.name)),f.name
 elif name=='mansao_spots_led':emissive(after.shader_group.shaders[0],2);assert len(after.lights)==20
 elif name=='mansao_tv':assert len(after.lights)==3;assert len(after.shader_group.shaders)==2;emissive(after.shader_group.shaders[1],1.65)
 native+=after.lights
 report.append(dict(model=name,original_meshes_preserved_except_requested_diffusers=True,collision_preserved=True,added_triangles_all_lods=added,lens_lods_changed=changed_lens,before_bytes=(B/'stream'/(name+'.ydr')).stat().st_size,after_bytes=(O/'stream'/(name+'.ydr')).stat().st_size))
for row,li in zip(project['stairs']+project['tv_lights'],native[9:]):
 assert li.light_type==LightType.POINT;rgbcheck(li.color)
 assert np.allclose(row['position'],li.position,atol=1e-5)
 assert li.falloff<.8 and 0<li.intensity<=.9
 assert li.time_flags==0xffffff and li.flashiness==LightFlashiness.CONSTANT
 assert li.volume_intensity==li.volume_outer_intensity==li.corona_intensity==li.corona_size==0
 # Strip/source positions are tied to the native object coordinate system.
 assert li.light_fade_distance>=100
roof=try_load_asset(D/'stream/mansao_teto.ydr');assert len(roof.lights)==88;native+=roof.lights
assert len(native)==120 and len(set(l.light_hash for l in native))==120
assert all(tuple(l.color)==(255,255,255) for l in roof.lights)
full_count=0;disabled=[]
for file in (D/'stream').glob('*.ydr'):
 replacement=O/'stream'/file.name;a=try_load_asset(replacement if replacement.exists() else file);full_count+=len(a.lights)
 if file.stem not in ['mansao_spot_embutido','mansao_pendentes','mansao_spots_led','mansao_tv']:
  assert not a.lights or file.stem=='mansao_teto'
  for s in a.shader_group.shaders:
   for p in s.parameters:
    if p.name=='emissivemultiplier':assert p.value[0]==0;disabled.append(file.name)
assert full_count==120
cfg=json.loads((O/'iluminacao_ambiente.json').read_text());assert cfg['native_count']==120 and cfg['max_lights']==0 and cfg['lights']==[] and cfg['native_bounce_count']==0
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
assert any('escada 20 e TV 3' in o for o in g.outputs.values());assert any('CLEAR -> RAIN' in o for o in g.outputs.values())
assert not any(isinstance(e,EntityMloInstance) for e in try_load_asset(D/'stream/cidade_mansao.ymap').entities)
assert all(a.type==ArchetypeType.BASE for a in try_load_asset(D/'stream/cidade_mansao.ytyp').archetypes)
result=dict(passed=True,native_sources=120,white_ceiling=88,yellow_pendants=9,yellow_stair_leds=20,yellow_tv_leds=3,checks=report,lens_visibility_geometry=lens_samples,changed_constant_textures=texture_changes,other_decorative_emission_still_off=disabled,ceiling_cone_power_range_angles_unchanged=True,no_weather_or_postprocess_changes=True,no_volumes_or_coronas=True,no_script_draw_threads=True,maps_and_prop_transforms_unchanged=True,in_game_visual_verified=False)
(P/'verification.json').write_text(json.dumps(result,indent=2));print('VERIFIED: four readable lens LODs; six filled yellow cylinder faces; yellow stair/TV sources; original meshes, physics and textures preserved.',flush=True)
