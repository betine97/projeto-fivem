"""Minimal native lighting patch; no mesh, texture, map or weather changes."""
import sys,json,math,hashlib,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao';B=P/'backup';O=P/'package'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
import pymateria as rootpm
import pymateria.gta5 as pm
import pymateria.gta5.gen8 as g8
from szio.gta5.drawables import Light,LightType,LightFlashiness
from szio.gta5.native.adapters.drawable import _map_light_to_native
from szio.types import Vector
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['mansao_teto','mansao_pendentes','mansao_spots_led','mansao_tv']
targets=['stream/'+n+'.ydr' for n in names]+['iluminacao_ambiente.json','iluminacao_decorativa.lua','luzes_pendentes.json','README.md']
if not (P/'baseline.json').exists():
 (P/'baseline.json').write_text(json.dumps({f.relative_to(D).as_posix():sha(f) for f in D.rglob('*') if f.is_file()},indent=2))
 for rel in targets:
  dest=B/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(D/rel,dest)
baseline=json.loads((P/'baseline.json').read_text());assert all(sha(D/t)==baseline[t] for t in targets),'Concurrent lighting target edit'
(O/'stream').mkdir(parents=True,exist_ok=True)
assets={n:g8.Drawable.import_rsc(B/'stream'/(n+'.ydr')).result for n in names}
cfg=json.loads((B/'iluminacao_ambiente.json').read_text())
rows=cfg['native_lights'];white=[r for r in rows if r['kind']=='ceiling_white'];pend=[r for r in rows if r['kind']=='pendant_yellow']
assert len(white)==88 and len(pend)==9
warm=(255,208,140);led=(255,196,100);baseflags=pm.LightFlags.BOTH_INTERIOR_AND_EXTERIOR|pm.LightFlags.FX|pm.LightFlags.DONT_LIGHT_ALPHA
profile=[]
for name,data in [('mansao_teto',white),('mansao_pendentes',pend)]:
 for light,row in zip(assets[name].lights,data):
  assert np.allclose(list(light.position),row['position'],atol=1e-5)
  h=row['position'][2]-row['floor_z'];tall=h>5;linear=row['id'].startswith('linear')
  radius=(3.5 if tall else 2.5) if name=='mansao_teto' else (1.7 if linear else 2.2)
  power=(3.5 if tall else 2.2) if name=='mansao_teto' else (1.15 if linear else .85)
  old=dict(intensity=light.intensity,range=light.falloff,inner=light.cone_inner_angle,outer=light.cone_outer_angle)
  # A zero-degree inner cone removes the wide flat plateau. Fade extends all
  # the way from the axis to the outer edge, as in original Michael fixtures.
  light.intensity=power;light.cone_inner_angle=0;light.cone_outer_angle=math.degrees(math.atan(radius/h))
  light.falloff=max(h+2.5,math.hypot(h,radius)*1.35);light.falloff_exponent=4
  rgb=(255,255,255) if name=='mansao_teto' else warm
  light.color=rootpm.ColorRGB(*rgb);light.volume_outer_color=rootpm.ColorRGB(*rgb)
  for obsolete in ['brightness_multiplier_from_previous']:row.pop(obsolete,None)
  row.update(rgb=list(rgb),intensity=power,range=light.falloff,falloff_exponent=4,inner_angle=0,outer_angle=light.cone_outer_angle,floor_radius_m=radius,beam_height_m=h,edge_style='continuous_axis_to_edge_fade')
  profile.append(dict(id=row['id'],before=old,after={k:row[k] for k in ['intensity','range','inner_angle','outer_angle','floor_radius_m']}))

def native(ident,position,range_,power,rgb,kind=LightType.POINT,direction=(0,0,-1),length=1,floor=None,moving=False,exponent=8):
 flags=baseflags|pm.LightFlags.NO_SPECULAR
 if moving:flags|=pm.LightFlags.MOVING_LIGHT_SOURCE
 if floor is not None:flags|=pm.LightFlags.USE_CULL_PLANE
 return _map_light_to_native(Light(light_type=kind,position=Vector(position),direction=Vector(direction),tangent=Vector([0,1,0] if direction[0] else [1,0,0]),extent=Vector([length]*3),color=tuple(rgb),flashiness=LightFlashiness.CONSTANT,intensity=power,flags=flags.value,time_flags=0xffffff,bone_id=0,group_id=0,light_hash=ident,falloff=range_,falloff_exponent=exponent,culling_plane_normal=Vector([0,0,1] if floor is not None else [0,0,0]),culling_plane_offset=position[2]-floor+.03 if floor is not None else 0,volume_intensity=0,volume_size_scale=1,volume_outer_color=tuple(rgb),volume_outer_intensity=0,volume_outer_exponent=1,corona_size=0,corona_intensity=0,corona_z_bias=0,projected_texture_hash='',light_fade_distance=120,shadow_fade_distance=0,specular_fade_distance=0,volumetric_fade_distance=0,shadow_near_clip=.05,shadow_blur=0,cone_inner_angle=0,cone_outer_angle=0))

# Sparse, low-power approximation of reflected fixture light; no extra visible
# emitter, floor spotlight, volume or player-dependent Lua drawing.
older=json.loads((R/'casa_vinewood/luminarias_cor_alcance_20261008/projeto.json').read_text())
regions=json.loads((R/'casa_vinewood/luz_permanente_20261008/projeto_luminotecnico.json').read_text())['regions']
bounce=[]
for i,(old,region) in enumerate(zip([r for r in older['lights'] if r['kind']=='bounce'],regions)):
 p=old['position'];large=i in [0,1,10,13,14];small=i in [5,7,9,11,12,15,16]
 radius=5.8 if i in [0,1] else (5.0 if large else (3.0 if small else 4.3))
 power=.35 if i in [0,1] else (.4 if large else (.24 if small else .30))
 exponent=6 if i in [0,1] else 8
 rgb=(255,239,217) if i in [0,1,2] else (255,250,242)
 positions=[[p[0],y,p[2]] for y in [-9.3,-3.6]] if i in [0,1] else [p]
 for j,position in enumerate(positions):
  li=native(101+len(bounce),position,radius,power,rgb,floor=old['floor_z'],exponent=exponent)
  assets['mansao_teto'].lights.append(li)
  bounce.append(dict(id='bounce_'+str(i)+'_'+str(j),kind='bounce',room=region['name'],level=region['level'],position=position,floor_z=old['floor_z'],rgb=list(rgb),range=radius,intensity=power,falloff_exponent=exponent,direction=[0,0,-1],inner_angle=0,outer_angle=0,shadow=False,cull_below_floor=True,no_specular=True))
assert len(bounce)==21

# Linear LEDs use native capsule sources, as the original GTA clothing stores
# do. Match source extent to the already installed strip, with a local halo.
stairs=assets['mansao_spots_led'];stairrows=[]
for i,row in enumerate(cfg['decorative_native_lights'][:20]):
 row.update(rgb=list(led),range=.42,intensity=.5,falloff_exponent=4,source_type='CAPSULE',direction=[1,0,0])
 stairs.lights[i]=native(231+i,row['position'],row['range'],row['intensity'],led,LightType.CAPSULE,[1,0,0],row['length_m'],exponent=4)
 stairrows.append(row)
tvrow=dict(id='tv_top_linear',kind='tv_top_yellow',position=[-8.800,(-9.870-7.677)/2,1.464],rgb=list(led),range=.60,intensity=.6,falloff_exponent=6,source_type='CAPSULE',direction=[0,1,0],length_m=2.193)
assets['mansao_tv'].lights=[native(251,tvrow['position'],tvrow['range'],tvrow['intensity'],led,LightType.CAPSULE,[0,1,0],tvrow['length_m'],moving=True,exponent=6)]
for name,a in assets.items():g8.Drawable.export_rsc(a,O/'stream'/(name+'.ydr'))

cfg.update(version=6,lighting_style='natural_soft_focus_and_sparse_indirect',native_count=139,native_bounce_count=21,native_stair_count=20,native_tv_led_count=1,native_always_on=True,max_lights=0,lights=[])
cfg.pop('floor_radius_m',None)
cfg['native_lights']=pend+white+bounce
cfg['decorative_native_lights']=stairrows+[tvrow]
cfg['description']='White ceiling lights and warm yellow pendants with gradual beam edges, reduced peak intensity and sparse low-power native indirect fill. Linear warm stair/TV LEDs. Constant lights; no weather, global filter, fog or bloom changes.'
cfg['reference_inspection']='227 native sources read from original Michael and clothing-store GTA assets; adapted to mansion dimensions, without copying original assets.'
(O/'iluminacao_ambiente.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
pcfg=json.loads((B/'luzes_pendentes.json').read_text());pcfg['lights']=pend
pcfg['description']='Six warm yellow cylinders and three warm yellow linear beams with a soft continuous edge and reduced peak power, reaching the floor.'
(O/'luzes_pendentes.json').write_text(json.dumps(pcfg,indent=2),encoding='utf-8')
controller=(B/'iluminacao_decorativa.lua').read_text(encoding='utf-8')
controller=controller.replace('-- Native fixture lighting plus only the requested stair and TV LEDs. No draw thread.','-- Soft native fixture lighting and sparse indirect fill. Diagnostic commands only.')
controller=controller.replace("    print('[Mansao luz] Feixes fortes para baixo ate o piso: raio 1,10 m; linear 0,80 m. Preenchimentos e reforcos: desligados. LEDs amarelos da escada e topo da TV: ligados.')","    print(('[Mansao luz] Focos suaves ate o piso; %d preenchimentos indiretos nativos de baixa potencia, sem reflexos especulares.'):format(config.native_bounce_count))")
(O/'iluminacao_decorativa.lua').write_text(controller,encoding='utf-8')
readme='''# Iluminação atual da mansão — 08/10/2026\n\nPerfil natural inspirado na casa do Michael e nas lojas de roupa do GTA. A revisão substitui os focos anteriores extremamente fortes e estreitos: os 88 spots brancos têm bordas contínuas e potência menor; os nove focos dos pendentes usam amarelo quente menos saturado. A abertura se adapta à altura de cada luminária, alcançando o piso com transição suave.\n\nVinte e um pontos nativos discretos aproximam a luz refletida pelo ambiente, sem emissão visível, sombras extras ou reflexos especulares; dois em cada sala maior, um nos demais ambientes. As fontes são constantes e não dependem de onde o personagem está. A queda inferior dos preenchimentos é recortada ao nível do pavimento. Não há novo MLO, alterações de clima, proteção contra chuva/névoa, filtros ou bloom global. Os LEDs da escada e da TV agora têm fontes lineares de baixa intensidade, evitando halos pontuais repetidos. As lentes visíveis dos spots, os difusores amarelos dos pendentes e as faixas existentes permanecem intactos.\n\nReferência: 227 fontes nativas foram consultadas nos arquivos originais do GTA, sem modificá-los nem instalar cópias na mansão. Os valores foram adaptados às alturas e dimensões locais; intensidade isolada não equivale à exposição percebida. Contagem nos quatro modelos alterados: 97 focos, 21 preenchimentos e 21 fontes lineares = 139 fontes nativas, com a única sombra preexistente mantida. Fachada e garagem permanecem com suas fontes originais, fora dessa contagem. Nenhuma iluminação Lua por quadro.\n\nValidação local: leitura nativa por duas bibliotecas, preservação das malhas, materiais, texturas, colisões, LODs e demais arquivos; análise geométrica de distribuição e atenuação. A análise de atenuação usa a fórmula do [renderizador do CodeWalker](https://github.com/dexyfex/CodeWalker/blob/master/CodeWalker.Shaders/LightPS.hlsli) como aproximação, sem representar a exposição, oclusão, FPS ou resultado visual final do FiveM. [Flags nativas](https://docs.sollumz.org/2.6/documentation/lighting-.ydr/light-flags).\n\nPara carregar: no console do servidor execute `restart cidade_mansao`; feche completamente o FiveM e reconecte. No F8, `luzmansao` ou `mansaoluzes` mostra o perfil e o clima observado. Backup, comparação e verificações: `casa_vinewood/luz_natural_20261008/`. A aparência no jogo precisa ser conferida após recarregar.\n\n---\n\nHistórico de revisões anteriores:\n\n'''+(B/'README.md').read_text(encoding='utf-8')
(O/'README.md').write_text(readme,encoding='utf-8')
(P/'projeto.json').write_text(json.dumps(dict(targets=targets,direct_profile=profile,bounce=bounce,stairs=stairrows,tv_lights=[tvrow],native_sources=139,geometry_materials_textures_collision_unchanged=True,in_game_visual_verified=False),indent=2))
print('STAGED: 97 softened fixtures; 21 sparse indirect sources; 21 linear stair/TV LED sources. All meshes and materials unchanged.',flush=True)
