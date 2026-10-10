"""Only fixture-aligned ceiling/pendant spotlights; no bounce or decorative light.

Patch existing native arrays/material powers directly, retaining geometry,
collision, shader program keys, textures, maps, props and other resources.
"""
import sys,json,math,hashlib,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao';B=P/'backup';O=P/'package'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import pymateria as rootpm
import pymateria.gta5 as pm
import pymateria.gta5.gen8 as g8
import numpy as np
from szio.gta5 import try_load_asset
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
audit=json.loads((P/'audit.json').read_text())
native_targets=[r['file'] for r in audit]
targets=['stream/'+name for name in native_targets]+['iluminacao_ambiente.json','iluminacao_decorativa.lua','luzes_pendentes.json','bar_referencia_luzes.lua','adega_vitrines_luzes.lua','README.md']
if not (P/'baseline.json').exists():
    (P/'baseline.json').write_text(json.dumps({f.relative_to(D).as_posix():sha(f) for f in D.rglob('*') if f.is_file()},indent=2))
    for rel in targets:
        dst=B/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(D/rel,dst)
baseline=json.loads((P/'baseline.json').read_text())
assert all(sha(D/t)==baseline[t] for t in targets),'A lighting target changed during staging'
(O/'stream').mkdir(parents=True,exist_ok=True)
prior=json.loads((R/'casa_vinewood/luminarias_cor_alcance_20261008/projeto.json').read_text(encoding='utf-8'))
definitions=[];changed_native=[];removed_native=[];emission_off=[]
for name in native_targets:
    a=g8.Drawable.import_rsc(B/'stream'/name).result
    if name in ['mansao_teto.ydr','mansao_pendentes.ydr']:
        previous=[r for r in prior['lights'] if (r['kind']=='pendant_yellow')==(name=='mansao_pendentes.ydr')]
        assert len(a.lights)==len(previous)
        retained=[]
        for i,(light,row) in enumerate(zip(a.lights,previous)):
            assert np.allclose(list(light.position),row['position'],atol=1e-5)
            assert row['rgb']==list(light.color)
            if row['kind']=='bounce':continue
            assert light.type==pm.LightType.SPOT
            h=float(light.position.z)-row['floor_z'];assert h>1
            linear=row['id'].startswith('linear_')
            radius=.8 if linear else 1.10
            power=7.0 if linear else (8.0 if name=='mansao_pendentes.ydr' else (15.0 if h>4.5 else 8.5))
            light.intensity=power
            light.falloff=float(math.sqrt(h*h+radius*radius)*1.5+.4)
            light.falloff_exponent=1.0
            light.cone_inner_angle=math.degrees(math.atan2(radius*.68,h))
            light.cone_outer_angle=math.degrees(math.atan2(radius,h))
            light.volume_intensity=0;light.volume_outer_intensity=0;light.corona_intensity=0;light.corona_size=0
            updated={**row,'range':light.falloff,'intensity':power,'falloff_exponent':1.0,
                     'inner_angle':light.cone_inner_angle,'outer_angle':light.cone_outer_angle,
                     'floor_radius_m':radius,'beam_height_m':h,'brightness_multiplier_from_previous':power/row['intensity']}
            definitions.append(updated);retained.append(light)
        removed_native.append(dict(file=name,before=len(a.lights),after=len(retained)))
        a.lights=retained
    else:
        if a.lights:removed_native.append(dict(file=name,before=len(a.lights),after=0))
        a.lights=[]
    for i,shader in enumerate(a.shader_group.shaders):
        for param in shader.parameters:
            if param.name!=pm.HashString('emissivemultiplier'):continue
            if name in ['mansao_pendentes.ydr','mansao_spot_embutido.ydr']:
                # Keep only the actual lamp lenses visibly on. The narrow light
                # source supplies strength, without adding fog/glow volumes.
                power=2.8 if name=='mansao_pendentes.ydr' else 3.0
            else:
                power=0.0;emission_off.append(dict(file=name,shader=i))
            param.data=[rootpm.Vector4f(power,0,0,0)]
    output=O/'stream'/name;g8.Drawable.export_rsc(a,output);changed_native.append(name)
assert sum(r['kind']=='ceiling_white' for r in definitions)==88
assert sum(r['kind']=='pendant_yellow' for r in definitions)==9
cfg=dict(version=4,origin=prior['origin'],lighting_style='only_ceiling_fixtures',native_always_on=True,native_count=97,
         native_ceiling_count=88,native_pendant_count=9,native_bounce_count=0,max_lights=0,lights=[],
         floor_radius_m=dict(spot_and_cylinder=1.10,linear=.80),native_lights=definitions,
         description='Only strong downward narrow cones from actual ceiling and pendant lenses. No room fill, optional boost, decorative LEDs or volumetric lighting.')
(O/'iluminacao_ambiente.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
(O/'luzes_pendentes.json').write_text(json.dumps(dict(origin=prior['origin'],embedded_in='stream/mansao_pendentes.ydr',
    description='Six yellow cylinder and three yellow linear sources: narrow, strong and long enough to reach the floor.',
    lights=[r for r in definitions if r['kind']=='pendant_yellow']),indent=2))
(O/'iluminacao_decorativa.lua').write_text((P/'controller.lua').read_text(encoding='utf-8'),encoding='utf-8')
for name in ['bar_referencia_luzes.lua','adega_vitrines_luzes.lua']:
    (O/name).write_text('-- Decorative light disabled at the user\'s request: only ceiling/pendant fixtures illuminate the mansion.\n-- No local fill, glow light or per-frame light loop.\n')
readme=(B/'README.md').read_text(encoding='utf-8')
readme+='''\n\n## Apenas luminárias do teto — 08/10/2026\n\nEsta revisão substitui os preenchimentos e reforços das seções anteriores, a pedido do usuário. Só permanecem 88 spots brancos e nove fontes amarelas nos pendentes do teto. Todos usam feixes direcionados para baixo: raio de 1,10 m ao atingir o piso nos spots/cilindros e 0,80 m no pendente linear. A abertura foi calculada pela altura real de cada luminária até o piso; intensidade entre 7 e 15, de quatro a cinco vezes a anterior, e alcance com margem além do chão. Os limites descrevem o cone direto; reflexos do motor e exposição dependem do jogo.\n\nOs 19 preenchimentos nativos, reforço opcional Lua, fontes do aparador, bar e adega foram retirados. Emissão dos LEDs de escada, cozinha, bar, adega, aparador e substituto da fachada desativada, preservando malhas/texturas. As lentes dos spots/pendentes continuam acesas. Sem luzes de volume ou coronas, sem mudança de clima/filtros e sem proteção climática. As fontes são constantes em todos os horários e não dependem do cômodo ocupado.\n\n`luzmansao` e `mansaoluzes` no F8 mostram o estado; argumentos antigos de reforço não acrescentam luzes. No console do servidor, `restart cidade_mansao`; depois feche completamente o FiveM e reconecte para atualizar os arquivos nativos. Backup e verificações em `casa_vinewood/apenas_luminarias_teto_20261008/`. Aparência/FPS precisam ser conferidos no jogo após recarregar.\n'''
(O/'README.md').write_text(readme,encoding='utf-8')
(P/'projeto.json').write_text(json.dumps(dict(origin=prior['origin'],lights=definitions,removed_native=removed_native,
    decorative_emissive_slots_disabled=emission_off,changed_native=changed_native,in_game_verified=False),indent=2))
print('STAGED: 97 narrow fixture spotlights; zero fill or decorative lighting;',len(emission_off),'decorative emissive slots disabled',flush=True)
