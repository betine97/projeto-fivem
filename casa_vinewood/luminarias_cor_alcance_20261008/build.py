"""Fixture-aligned downward light, correct colours, restrained low room bounce.

Stage only. Patch native light arrays/material references without rehashing any
architecture shaders or altering the restored BASE collision / map types.
"""
import sys,json,math,shutil,hashlib
from pathlib import Path
from collections import Counter
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao';O=P/'package';B=P/'backup'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from PIL import Image
import pymateria as pmroot
import pymateria.gta5 as pm
import pymateria.gta5.gen8 as g8
from szio.gta5 import try_load_asset
from szio.gta5.drawables import Light,LightType,LightFlashiness
from szio.gta5.native.adapters.drawable import _map_light_to_native
from szio.types import Vector

targets=['stream/mansao_teto.ydr','stream/mansao_pendentes.ydr','stream/mansao_spot_embutido.ydr',
         'iluminacao_ambiente.json','iluminacao_decorativa.lua','luzes_pendentes.json','luzes_pendentes.lua','README.md']
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
if not (P/'baseline.json').exists():
    (P/'baseline.json').write_text(json.dumps({f.relative_to(D).as_posix():sha(f) for f in D.rglob('*') if f.is_file()},indent=2))
    for rel in targets:
        dest=B/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(D/rel,dest)
baseline=json.loads((P/'baseline.json').read_text())
assert all(sha(D/t)==baseline[t] for t in targets),'Target changed during staging'
(O/'stream').mkdir(parents=True,exist_ok=True)
origin=json.loads((B/'luzes_pendentes.json').read_text())['origin']
roof=g8.Drawable.import_rsc(B/'stream/mansao_teto.ydr').result
pendants=g8.Drawable.import_rsc(B/'stream/mansao_pendentes.ydr').result
fixture=g8.Drawable.import_rsc(B/'stream/mansao_spot_embutido.ydr').result
rows=[]
flags=(pm.LightFlags.BOTH_INTERIOR_AND_EXTERIOR|pm.LightFlags.FX|pm.LightFlags.DONT_LIGHT_ALPHA)

def add(ident,kind,pos,floor,radius,power,color,inner=28,outer=65,shadow=False):
    row=dict(id=ident,kind=kind,position=[round(float(x),5) for x in pos],floor_z=round(float(floor),5),
             rgb=color,range=radius,intensity=power,falloff_exponent=2.0 if kind!='bounce' else 1.0,
             direction=[0,0,-1],inner_angle=inner,outer_angle=outer,shadow=shadow)
    rows.append(row);return row

# Measure the floor BELOW each actual installed ceiling fixture. A 6.45 m
# fixture can illuminate the upper floor or the double-height ground floor.
floors=try_load_asset(D/'stream/mansao_pisos.ydr');tris=[]
for lod,ms in floors.models.items():
    if lod.name!='HIGH':continue
    for m in ms:
        for g in m.geometries:
            t=g.vertex_buffer['Position'][g.index_buffer.reshape(-1,3)]
            n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);tris.extend(t[n[:,2]>.00001])
tris=np.array(tris,dtype=float)
def floor_under(p):
    x,y,z=p;a=tris[:,0];b=tris[:,1];c=tris[:,2]
    denom=(b[:,1]-c[:,1])*(a[:,0]-c[:,0])+(c[:,0]-b[:,0])*(a[:,1]-c[:,1])
    u=((b[:,1]-c[:,1])*(x-c[:,0])+(c[:,0]-b[:,0])*(y-c[:,1]))/denom
    v=((c[:,1]-a[:,1])*(x-c[:,0])+(a[:,0]-c[:,0])*(y-c[:,1]))/denom
    h=u*a[:,2]+v*b[:,2]+(1-u-v)*c[:,2]
    valid=(u>=-1e-5)&(v>=-1e-5)&(u+v<=1.00001)&(h<z-.3)
    assert valid.any(),f'No floor under fixture {p}'
    return float(h[valid].max())

installed=try_load_asset(D/'stream/mansao_referencias.ymap')
for i,e in enumerate(installed.entities):
    assert str(e.archetype_name)=='mansao_spot_embutido'
    pos=np.array(e.position)-origin;floor=floor_under(pos);pos[2]-=.075
    tall=pos[2]-floor>4.5
    add(f'spot_{i+1}','ceiling_white',pos,floor,12.0 if tall else 6.4,2.8 if tall else 1.7,[255,255,255])

# Replace the old high, overlapping spherical fill with one gentle low source
# per room, so faces/furniture stay legible without burning out the ceiling.
previous=json.loads((R/'casa_vinewood/luz_permanente_20261008/projeto_luminotecnico.json').read_text())
cfgold=json.loads((B/'iluminacao_ambiente.json').read_text());boost=[]
for i,old in enumerate(cfgold['lights']):
    floor=-.8 if old['level']=='terreo' else 2.808
    p=old['position'][:];p[2]=floor+1.55
    tall=old['range']>8
    row=add(f'bounce_{i}','bounce',p,floor,6.3 if tall else 4.8,.45 if tall else .28,[255,255,255],0,0)
    boost.append(dict(id='boost_'+str(i),position=p,rgb=[255,255,255],range=row['range'],intensity=.42 if tall else .28))

# The original six light points averaged top and bottom cap faces into wrong
# positions. Re-measure the lowest luminous component of each real cylinder.
caps=json.loads((P/'caps_medidas.json').read_text());groups=[]
for cap in sorted(caps,key=lambda q:q['center'][1]):
    if not groups or abs(cap['center'][1]-groups[-1][0]['center'][1])>.15:groups.append([])
    groups[-1].append(cap)
assert len(groups)==6
pendant_rows=[]
for i,group in enumerate(groups):
    cap=min(group,key=lambda q:q['center'][2]);p=cap['center'][:];p[2]-=.035
    pendant_rows.append(add(f'cylinder_{i+1}','pendant_yellow',p,-.8,6.2,1.8,[255,196,110],26,64))
for i,y in enumerate([-9.75,-9,-8.25]):
    pendant_rows.append(add(f'linear_{i+1}','pendant_yellow',[10.45,y,1.315],-.8,5.0,1.35,[255,196,110],28,70,shadow=i==1))

def native(r,i):
    f=flags
    if r['kind']=='bounce':f|=pm.LightFlags.NO_SPECULAR
    if r['shadow']:f|=pm.LightFlags.CAST_SHADOWS|pm.LightFlags.CAST_STATIC_GEOM_SHADOWS|pm.LightFlags.CAST_DYNAMIC_GEOM_SHADOWS|pm.LightFlags.CAST_ONLY_LOWRES_SHADOWS
    return _map_light_to_native(Light(light_type=LightType.POINT if r['kind']=='bounce' else LightType.SPOT,
        position=Vector(r['position']),direction=Vector([0,0,-1]),tangent=Vector([1,0,0]),extent=Vector([1,1,1]),
        color=tuple(r['rgb']),flashiness=LightFlashiness.CONSTANT,intensity=r['intensity'],flags=f.value,time_flags=0xffffff,
        bone_id=0,group_id=0,light_hash=i+1,falloff=r['range'],falloff_exponent=r['falloff_exponent'],
        culling_plane_normal=Vector([0,0,0]),culling_plane_offset=0,volume_intensity=0,volume_size_scale=1,
        volume_outer_color=tuple(r['rgb']),volume_outer_intensity=0,volume_outer_exponent=1,
        corona_size=0,corona_intensity=0,corona_z_bias=0,projected_texture_hash='',light_fade_distance=120,
        shadow_fade_distance=30 if r['shadow'] else 0,specular_fade_distance=35 if r['kind']!='bounce' else 0,
        volumetric_fade_distance=0,shadow_near_clip=.1,shadow_blur=160,cone_inner_angle=r['inner_angle'],cone_outer_angle=r['outer_angle']))

roof_rows=[r for r in rows if r['kind']!='pendant_yellow']
roof.lights=[native(r,i) for i,r in enumerate(roof_rows)]
pendants.lights=[native(r,200+i) for i,r in enumerate(pendant_rows)]

# The full prism lens, rather than only its 8 mm core, emits neutral white.
# Reuse the existing emissive shader, with no geometry or texture size increase.
led=fixture.shader_group.shaders[2]
# Prior high-level exports rehashed unresolved shader names. Use the SAME
# actual emissive program key as the original GTA lamp inspected in this folder.
led.basis_shader=pm.HashString('emissive')
def set_emission(shader,power):
    param=next(p for p in shader.parameters if p.name==pm.HashString('emissivemultiplier'))
    param.data=[pmroot.Vector4f(power,0,0,0)]
set_emission(led,2.0)
white=P/'spot_lente_branca.dds';Image.new('RGBA',(4,4),(245,245,245,255)).save(white,pixel_format='DXT5')
tx=fixture.shader_group.texture_dictionary.textures[pm.HashString('spot_lente')];tx.import_dds(white)
remaps=0
for lod in fixture.lods.values():
    for m in lod.models:
        for g in m.geometries:
            if g.shader==fixture.shader_group.shaders[1]:g.shader=led;remaps+=1
assert remaps==4,f'Expected prism remap in four LODs, got {remaps}'
# Lower lens overexposure retains the yellow tint instead of clipping to white.
set_emission(pendants.shader_group.shaders[1],1.8)
pendants.shader_group.shaders[1].basis_shader=pm.HashString('emissive')
for name,asset in [('mansao_teto',roof),('mansao_pendentes',pendants),('mansao_spot_embutido',fixture)]:
    g8.Drawable.export_rsc(asset,O/'stream'/f'{name}.ydr')

config=dict(version=3,origin=origin,native_always_on=True,native_count=len(rows),native_ceiling_count=88,native_pendant_count=9,
            native_bounce_count=len(boost),max_lights=len(boost),activation_distance=120,lights=boost,
            description='White broad downward ceiling spots, yellow pendants at real bottom caps, low neutral bounce. No volumetric fog or weather override.')
(O/'iluminacao_ambiente.json').write_text(json.dumps(config,indent=2))
(O/'luzes_pendentes.json').write_text(json.dumps(dict(origin=origin,embedded_in='stream/mansao_pendentes.ydr',
    description='Always-on native yellow lights, no separate script draws.',lights=pendant_rows),indent=2))
(O/'luzes_pendentes.lua').write_text('-- Nine yellow light sources now live in mansao_pendentes.ydr at the actual lower lenses.\n-- They remain on in every room, all hours; no second per-frame light loop.\n')
(O/'iluminacao_decorativa.lua').write_text((P/'controller.lua').read_text(encoding='utf-8'),encoding='utf-8')
readme=(B/'README.md').read_text(encoding='utf-8')
readme+='''\n\n## Luminárias, cor e alcance — 08/10/2026\n\nEsta revisão substitui o projeto de 68 pontos altos da seção anterior. São 88 fontes brancas direcionadas para baixo nas posições dos spots, nove fontes amarelas nos pendentes e 19 preenchimentos neutros baixos. As lentes dos spots emitem branco em todos os quatro LODs. Os dois materiais emissivos tiveram a chave do programa corrigida para `emissive` (0x8f245469), confirmada em uma lâmpada nativa do GTA; seus presets e demais materiais foram preservados. O alcance foi medido até o piso real sob cada spot, distinguindo o mezanino do pé-direito duplo. As seis fontes dos cilindros foram reposicionadas nas tampas inferiores reais; antes não havia luz nativa nos pendentes, e o controlador separado estava desativado.\n\nO excesso de branco no teto foi reduzido removendo preenchimentos altos sobrepostos, direcionando a luz das luminárias para baixo e moderando a emissão das lentes. Volumes de névoa e coronas permanecem em zero; não há alteração de clima, timecycle, bloom global ou nova proteção climática. O tempo exterior ainda pode afetar a imagem, pois a proteção climática foi adiada.\n\nNo F8: `luzmansao 1` usa o padrão; `luzmansao 1.5` a `2` reforça os preenchimentos baixos. `mansaoluzes` mostra quantidade, cores, alcance, clima e índices dos filtros atmosféricos observados, sem alterar o tempo ou filtros. As fontes nativas são constantes e não dependem do cômodo ocupado; no padrão, zero chamadas Lua de iluminação por quadro. Só uma fonte adicional usa sombras.\n\nNo console do servidor: `restart cidade_mansao`. Depois feche completamente o FiveM e conecte novamente para atualizar os drawables. Fonte, backup e validações em `casa_vinewood/luminarias_cor_alcance_20261008/`. Testes de dados nativos, cobertura até o piso e controlador Lua locais; confirmação visual/FPS no FiveM pendente.\n'''
(O/'README.md').write_text(readme,encoding='utf-8')
(P/'projeto.json').write_text(json.dumps(dict(origin=origin,lights=rows,regions=previous['regions'],fixture_count=88,
    native_count=len(rows),roof_count=len(roof_rows),pendant_count=9,prism_lods_remapped=remaps,
    fog_diagnosis='Disabled fixture emitters and high overlapping spherical lights confirmed. Upper blowout/bloom inferred from screenshot; external weather can still contribute, not overridden.',
    in_game_verified=False),ensure_ascii=False,indent=2),encoding='utf-8')
print('STAGED',len(rows),'native sources;',Counter(r['kind'] for r in rows),'four lens LODs; shadow sources',sum(r['shadow'] for r in rows),flush=True)
