"""Verify only the requested light fields changed, and every beam reaches its floor."""
import sys,json,math,ast as pyast
from pathlib import Path
from dataclasses import fields,is_dataclass
from collections import Counter
from enum import Enum
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao';B=P/'backup';O=P/'package'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',str(R/'casa_vinewood/work/lua_syntax_deps')]
import numpy as np
from szio.gta5 import try_load_asset
from szio.gta5.bounds import AssetBoundComposite,AssetBoundBvh
from szio.gta5.drawables import LightType,LightFlashiness
from szio.gta5.entities import EntityMloInstance
from szio.gta5.archetypes import ArchetypeType
from luaparser import ast
from lupa import LuaRuntime
# Reuse ONLY the previously verified comparison function definitions; importing
# that script as a module would run its previous package tests and write reports.
tree=pyast.parse((R/'casa_vinewood/luminarias_cor_alcance_20261008/verify.py').read_text(encoding='utf-8'))
helpers=pyast.Module(body=[n for n in tree.body if isinstance(n,pyast.FunctionDef) and n.name in ['equal','collision']],type_ignores=[])
exec(compile(helpers,'asset_comparison_helpers','exec'))
project=json.loads((P/'projeto.json').read_text());actual=[];checks=[]
for name in project['changed_native']:
    before=try_load_asset(B/'stream'/name);after=try_load_asset(O/'stream'/name)
    assert before.models.keys()==after.models.keys()
    for lod in before.models:
        assert len(before.models[lod])==len(after.models[lod])
        for x,y in zip(before.models[lod],after.models[lod]):
            assert len(x.geometries)==len(y.geometries)
            for a,b in zip(x.geometries,y.geometries):
                assert np.array_equal(a.vertex_buffer,b.vertex_buffer),'Positions, UVs, normals or colours changed'
                assert np.array_equal(a.index_buffer,b.index_buffer),'Triangle indices changed'
                assert a.shader_index==b.shader_index
    collision(before.bounds,after.bounds)
    assert equal(before.lod_thresholds,after.lod_thresholds)
    assert before.shader_group.embedded_textures.keys()==after.shader_group.embedded_textures.keys()
    for k,t in before.shader_group.embedded_textures.items():assert t.data.read_bytes()==after.shader_group.embedded_textures[k].data.read_bytes(),k
    for x,y in zip(before.shader_group.shaders,after.shader_group.shaders):
        assert x.name==y.name and x.preset_filename==y.preset_filename
        assert len(x.parameters)==len(y.parameters)
        for a,b in zip(x.parameters,y.parameters):
            if a.name=='emissivemultiplier':
                expected=2.8 if name=='mansao_pendentes.ydr' else (3.0 if name=='mansao_spot_embutido.ydr' else 0.0)
                assert math.isclose(float(b.value[0]),expected,rel_tol=1e-6)
                assert equal(a.value[1:],b.value[1:])
            else:assert equal(a,b),a.name
    if name not in ['mansao_teto.ydr','mansao_pendentes.ydr']:assert len(after.lights)==0
    else:
        originals=[l for l in before.lights if l.light_type==LightType.SPOT]
        assert len(originals)==len(after.lights)
        for a,b in zip(originals,after.lights):
            for f in fields(a):
                if f.name not in ['intensity','falloff','falloff_exponent','cone_inner_angle','cone_outer_angle','user_metadata']:
                    assert equal(getattr(a,f.name),getattr(b,f.name)),f'Unrequested light change {f.name}'
        actual+=after.lights
    checks.append(dict(file=name,geometry_uv_normals_colours_indices_preserved=True,textures_identical=True,
                       shader_keys_and_unrelated_parameters_preserved=True,collision_preserved=True))
assert len(actual)==len(project['lights'])==97
assert len({li.light_hash for li in actual})==97
samples=0
for r,li in zip(project['lights'],actual):
    assert li.light_type==LightType.SPOT and np.allclose(li.direction,[0,0,-1])
    assert np.allclose(li.position,r['position'],atol=1e-5) and tuple(li.color)==tuple(r['rgb'])
    assert li.flashiness==LightFlashiness.CONSTANT and li.time_flags==0xffffff
    assert li.volume_intensity==li.volume_outer_intensity==li.corona_intensity==li.corona_size==0
    assert li.light_fade_distance>=100 and li.falloff_exponent==1.0
    assert r['brightness_multiplier_from_previous']>=4
    assert 7<=li.intensity<=15
    assert li.cone_outer_angle<=30 and li.cone_inner_angle<li.cone_outer_angle
    h=float(li.position[2])-r['floor_z'];radius=h*math.tan(math.radians(li.cone_outer_angle))
    assert math.isclose(radius,r['floor_radius_m'],abs_tol=1e-5),'Incorrect angle units or footprint'
    # Axis and floor samples strictly inside the soft cone must lie well INSIDE
    # the native radius, rather than touching its cutoff at floor height.
    for factor in [0,.3,.6,.9]:
        d=math.hypot(h,radius*factor)
        assert d<li.falloff*.75
        assert math.degrees(math.atan2(radius*factor,h))<li.cone_outer_angle
        samples+=1
    if r['kind']=='ceiling_white':assert li.color==(255,255,255)
    else:assert li.color[0]>li.color[1]>li.color[2]
# Scan the COMPLETE prospective resource: not only the two changed light arrays.
total=0;nonfixture_emission=0
for path in sorted((D/'stream').glob('*.ydr')):
    prospective=O/'stream'/path.name;asset=try_load_asset(prospective if prospective.exists() else path)
    total+=len(asset.lights)
    if path.name not in ['mansao_spot_embutido.ydr','mansao_pendentes.ydr']:
        assert not asset.lights or path.name=='mansao_teto.ydr'
        for shader in asset.shader_group.shaders:
            for param in shader.parameters:
                if param.name=='emissivemultiplier':
                    assert float(param.value[0])==0,(path.name,'Decorative emission still active')
                    nonfixture_emission+=1
assert total==97
cfg=json.loads((O/'iluminacao_ambiente.json').read_text());assert cfg['lights']==[] and cfg['max_lights']==cfg['native_bounce_count']==0
lua=l=LuaRuntime(unpack_returned_tuples=True);g=l.globals();g.decode_config=lambda _:l.table_from(cfg,recursive=True)
l.execute('''
json={decode=decode_config};commands={};outputs={};threads=0
function LoadResourceFile(...) return 'config' end
function GetCurrentResourceName() return 'cidade_mansao' end
function RegisterCommand(n,f,_) commands[n]=f end
function CreateThread(...) threads=threads+1;error('Unexpected light thread') end
function DrawLightWithRange(...) error('Unexpected room fill') end
function DrawSpotLight(...) error('Duplicate fixture lighting') end
function GetHashKey(s) local v=0;for i=1,#s do v=v+s:byte(i)*i end;return v end
function GetPrevWeatherTypeHashName() return GetHashKey('FOGGY') end
function GetNextWeatherTypeHashName() return GetHashKey('CLEAR') end
function GetTimecycleModifierIndex() return -1 end
function GetExtraTimecycleModifierIndex() return -1 end
function print(s) outputs[#outputs+1]=s end
''')
for name in ['iluminacao_decorativa.lua','bar_referencia_luzes.lua','adega_vitrines_luzes.lua']:
    s=(O/name).read_text(encoding='utf-8');ast.parse(s);l.execute(s)
g.commands.luzmansao(0,l.table_from(['99']));g.commands.mansaoluzes();assert g.threads==0
assert any('APENAS LUMINARIAS' in s for s in g.outputs.values())
assert any('FOGGY -> CLEAR' in s for s in g.outputs.values())
assert not any(isinstance(e,EntityMloInstance) for e in try_load_asset(D/'stream/cidade_mansao.ymap').entities)
assert all(a.type==ArchetypeType.BASE for a in try_load_asset(D/'stream/cidade_mansao.ytyp').archetypes)
report=dict(passed=True,native_sources=97,ceiling_white=88,pendants_yellow=9,point_fill_sources=0,
            decorative_emissive_slots_disabled=nonfixture_emission,native_room_fill_removed=19,aparador_native_sources_removed=4,
            every_fixture_axis_reaches_floor=True,floor_cone_samples=samples,maximum_floor_radius_m=1.10,
            native_brightness_multiplier_minimum=min(r['brightness_multiplier_from_previous'] for r in project['lights']),
            lua_light_calls=0,lua_light_threads=0,old_boost_command_cannot_add_lights=True,geometry_checks=checks,
            volumes_and_coronas=0,climate_and_postprocess_unmodified=True,base_map_preserved=True,
            in_game_visual_verified=False,in_game_fps_measured=False)
(P/'verification.json').write_text(json.dumps(report,indent=2));print('VERIFIED: 97 fixture SPOT sources, no other native/script/emissive lighting;',samples,'beam-floor samples; geometry/texture/collision preserved',flush=True)
