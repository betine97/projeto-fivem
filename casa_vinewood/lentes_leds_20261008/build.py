"""Local native patch: readable lenses, yellow pendants, stair and TV LEDs.
Preserves existing map, physics, furniture and native ceiling beam settings.
"""
import sys,json,math,hashlib,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao';B=P/'backup';O=P/'package'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from PIL import Image
import pymateria as rootpm
import pymateria.gta5 as pm
import pymateria.gta5.gen8 as g8
from szio.gta5.drawables import Light,LightType,LightFlashiness
from szio.gta5.native.adapters.drawable import _map_light_to_native
from szio.types import Vector
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
targets=['stream/'+n+'.ydr' for n in ['mansao_spot_embutido','mansao_pendentes','mansao_spots_led','mansao_tv']]+['iluminacao_ambiente.json','iluminacao_decorativa.lua','luzes_pendentes.json','README.md']
if not (P/'baseline.json').exists():
 (P/'baseline.json').write_text(json.dumps({f.relative_to(D).as_posix():sha(f) for f in D.rglob('*') if f.is_file()},indent=2))
 for rel in targets:
  out=B/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(D/rel,out)
baseline=json.loads((P/'baseline.json').read_text());assert all(sha(D/t)==baseline[t] for t in targets),'Concurrent lighting target edit'
(O/'stream').mkdir(parents=True,exist_ok=True)
def load(n):return g8.Drawable.import_rsc(B/'stream'/(n+'.ydr')).result
def save(n,a):g8.Drawable.export_rsc(a,O/'stream'/(n+'.ydr'))
def emission(shader,power):
 p=next(p for p in shader.parameters if p.name==pm.HashString('emissivemultiplier'))
 p.data=[rootpm.Vector4f(power,0,0,0)]
def recolor(asset,key,rgb):
 f=P/(key+'.dds');Image.new('RGBA',(4,4),tuple(rgb)+(255,)).save(f,pixel_format='DXT5')
 asset.shader_group.texture_dictionary.textures[pm.HashString(key)].import_dds(f)

spot=load('mansao_spot_embutido');template=spot.lods[pm.LodType.HIGH].models[2].geometries[0]
radius_by_lod={pm.LodType.HIGH:.050,pm.LodType.MED:.052,pm.LodType.LOW:.055,pm.LodType.VLOW:.055}
lens=[]
for key,lod in spot.lods.items():
 g=lod.models[2].geometries[0];v=g.vb.buffer
 old=v['POSITION'].copy();r=float(np.linalg.norm(old[:,:2],axis=1).max());lo,hi=old[:,2].min(),old[:,2].max()
 # A thin diffuser just below the opening is readable at oblique angles.
 # Keep the collar, reflector, prism, textures and vertex/index counts intact.
 scale=np.array([radius_by_lod[key]/r,radius_by_lod[key]/r,.001/(hi-lo)],dtype=np.float32)
 v['POSITION'][:,:2]*=scale[:2];v['POSITION'][:,2]=-.004+(old[:,2]-lo)*scale[2]
 v['NORMAL'][:]/=scale;v['NORMAL'][:]/=np.maximum(np.linalg.norm(v['NORMAL'],axis=1,keepdims=True),1e-9)
 assert np.max(np.linalg.norm(v['POSITION'][:,:2],axis=1))<.058
 lens.append(dict(lod=key.name,radius_m=radius_by_lod[key],surface_z=[-.004,-.003],threshold_m=lod.lod_threshold))
emission(spot.shader_group.shaders[2],3.0);save('mansao_spot_embutido',spot)

def geometry(vertices,faces,normals,shader):
 g=g8.Geometry();g.shader=shader;g.primitive_type=template.primitive_type;g.matrix_palette=template.matrix_palette
 g.vb=g8.VertexBuffer();g.vb.fvf=template.vb.fvf;g.vb.resize(len(vertices));v=g.vb.buffer
 v['POSITION']=np.array(vertices,dtype=np.float32);v['NORMAL']=np.array(normals,dtype=np.float32)
 v['DIFFUSE'][:]=255;v['TEXTURE0'][:]=.5
 g.ib=g8.IndexBuffer();g.ib.indices=np.asarray(faces,dtype=np.uint16).flatten();return g
def disc(center,radius,segments,shader):
 vs=[];fs=[];ns=[]
 for normal,winding,z in [(-1,-1,0),(1,1,.001)]:
  start=len(vs);vs.append([center[0],center[1],center[2]+z]);ns.append([0,0,normal])
  for i in range(segments):
   t=i*2*math.pi/segments;vs.append([center[0]+radius*math.cos(t),center[1]+radius*math.sin(t),center[2]+z]);ns.append([0,0,normal])
  for i in range(segments):
   u=start+1+i;v=start+1+(i+1)%segments
   fs.append([start,u,v] if winding==1 else [start,v,u])
 return geometry(vs,fs,ns,shader)
def box(lo,hi,shader):
 vs=[];fs=[];ns=[]
 for axis,side in [(0,0),(0,1),(1,0),(1,1),(2,0),(2,1)]:
  others=[a for a in range(3) if a!=axis];start=len(vs);n=np.zeros(3);n[axis]=-1 if side==0 else 1
  pts=[]
  for u,v in [(0,0),(1,0),(1,1),(0,1)]:
   p=np.zeros(3);p[axis]=hi[axis] if side else lo[axis];p[others[0]]=hi[others[0]] if u else lo[others[0]];p[others[1]]=hi[others[1]] if v else lo[others[1]];pts.append(p)
  if np.dot(np.cross(pts[1]-pts[0],pts[2]-pts[0]),n)<0:pts=pts[::-1]
  vs.extend([p.tolist() for p in pts]);ns.extend([n.tolist()]*4);fs.extend([[start,start+1,start+2],[start,start+2,start+3]])
 return geometry(vs,fs,ns,shader)

warm=[255,180,55];pends=load('mansao_pendentes');lamp=pends.shader_group.shaders[1]
emission(lamp,1.65);recolor(pends,'mansao_led_quente',[255,174,40])
caps=json.loads((P/'bottom_caps.json').read_text());cap_rows=[]
for cap in caps:
 center=cap['center'][:];center[2]=cap['min'][2]-.004
 radius=min((cap['max'][0]-cap['min'][0])/2,(cap['max'][1]-cap['min'][1])/2)*.87
 cap_rows.append(dict(center=center,radius_m=radius))
for key,lod in pends.lods.items():
 segments={pm.LodType.HIGH:32,pm.LodType.MED:24,pm.LodType.LOW:16,pm.LodType.VLOW:12}[key]
 for cap in cap_rows:lod.models[0].geometries.append(disc(cap['center'],cap['radius_m'],segments,lamp))
for light in pends.lights:light.color=rootpm.ColorRGB(*warm);light.volume_outer_color=rootpm.ColorRGB(*warm)
save('mansao_pendentes',pends)

def native_point(ident,position,range_,power,moving=False):
 flags=pm.LightFlags.BOTH_INTERIOR_AND_EXTERIOR|pm.LightFlags.FX|pm.LightFlags.DONT_LIGHT_ALPHA|pm.LightFlags.NO_SPECULAR
 if moving:flags|=pm.LightFlags.MOVING_LIGHT_SOURCE
 return _map_light_to_native(Light(light_type=LightType.POINT,position=Vector(position),direction=Vector([0,0,-1]),tangent=Vector([1,0,0]),extent=Vector([1,1,1]),color=tuple(warm),flashiness=LightFlashiness.CONSTANT,intensity=power,flags=flags.value,time_flags=0xffffff,bone_id=0,group_id=0,light_hash=ident,falloff=range_,falloff_exponent=2,culling_plane_normal=Vector([0,0,0]),culling_plane_offset=0,volume_intensity=0,volume_size_scale=1,volume_outer_color=tuple(warm),volume_outer_intensity=0,volume_outer_exponent=1,corona_size=0,corona_intensity=0,corona_z_bias=0,projected_texture_hash='',light_fade_distance=100,shadow_fade_distance=0,specular_fade_distance=0,volumetric_fade_distance=0,shadow_near_clip=.05,shadow_blur=0,cone_inner_angle=0,cone_outer_angle=0))
stairs=load('mansao_spots_led');stairshader=stairs.shader_group.shaders[0]
stairshader.basis_shader=pm.HashString('emissive');emission(stairshader,2.0);recolor(stairs,'mansao_decor_led',[255,174,40])
stair_rows=[]
for lod in stairs.lods.values():
 for m in lod.models:
  for g in m.geometries:
   if g.shader!=stairshader:continue
   pos=g.vb.buffer['POSITION'];lo=pos.min(axis=0);hi=pos.max(axis=0);center=((lo+hi)*.5).tolist()
   # Sources sit under the real strip, facing the front of each tread.
   center[1]=(float(lo[1])-.024) if center[0]<1.0 or hi[0]-lo[0]>2 else (float(hi[1])+.024)
   center[2]=float(lo[2])-.025
   stair_rows.append(dict(id='stair_'+str(len(stair_rows)+1),kind='stair_yellow',position=center,rgb=warm,range=.72,intensity=.90,length_m=float(hi[0]-lo[0])))
assert len(stair_rows)==20
stairs.lights=[native_point(231+i,r['position'],r['range'],r['intensity']) for i,r in enumerate(stair_rows)]
save('mansao_spots_led',stairs)

tv=load('mansao_tv')
# Separate imported shader object: leave every original TV material untouched.
extra=load('mansao_pendentes');tvshader=extra.shader_group.shaders[1];emission(tvshader,1.65)
tvtex=extra.shader_group.texture_dictionary.textures[pm.HashString('mansao_led_quente')];tvtex.import_dds(P/'mansao_led_quente.dds')
tv.shader_group.shaders.append(tvshader);tv.shader_group.texture_dictionary.textures[pm.HashString('mansao_led_quente')]=tvtex
# Native face sampling measured the actual screen: Y -9.904..-7.643,
# front X -8.780, upper Z 1.431. Fit the strip behind that upper edge.
tvstrip=dict(lo=[-8.800,-9.870,1.432],hi=[-8.792,-7.677,1.444],behind_screen_front=True)
for lod in tv.lods.values():lod.models[0].geometries.append(box(tvstrip['lo'],tvstrip['hi'],tvshader))
tv_rows=[]
for i,y in enumerate(np.linspace(tvstrip['lo'][1]+.28,tvstrip['hi'][1]-.28,3)):
 tv_rows.append(dict(id='tv_top_'+str(i+1),kind='tv_top_yellow',position=[-8.800,float(y),1.464],rgb=warm,range=.78,intensity=.80))
tv.lights=[native_point(251+i,r['position'],r['range'],r['intensity'],True) for i,r in enumerate(tv_rows)]
save('mansao_tv',tv)

cfg=json.loads((B/'iluminacao_ambiente.json').read_text());cfg.update(version=5,lighting_style='ceiling_with_requested_stair_tv_leds',native_count=120,native_stair_count=20,native_tv_led_count=3,ceiling_lens_diffuser_lods=lens)
for row in cfg['native_lights']:
 if row['kind']=='pendant_yellow':row['rgb']=warm
cfg['decorative_native_lights']=stair_rows+tv_rows
cfg['description']='Strong narrow white ceiling cones; yellow pendants; only the requested yellow stair and top TV LEDs restored. No room fill, volume lighting, weather or global filter changes.'
(O/'iluminacao_ambiente.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
pcfg=json.loads((B/'luzes_pendentes.json').read_text())
for row in pcfg['lights']:row['rgb']=warm
pcfg['description']='Six cylinders with full yellow emitting lower faces and three yellow linear sources. Existing narrow floor-reaching beams preserved.'
(O/'luzes_pendentes.json').write_text(json.dumps(pcfg,indent=2),encoding='utf-8')
controller=(B/'iluminacao_decorativa.lua').read_text(encoding='utf-8').replace('-- Fixture-only native lighting. No room fill, additive boost or draw thread.','-- Native fixture lighting plus only the requested stair and TV LEDs. No draw thread.')
controller=controller.replace('APENAS LUMINARIAS:','LUMINARIAS:').replace('Preenchimentos, reforcos e LEDs decorativos: desligados.','Preenchimentos e reforcos: desligados. LEDs amarelos da escada e topo da TV: ligados.')
controller=controller.replace("    print('[Mansao luz] Fontes nativas constantes;", "    print(('[Mansao luz] Lentes brancas em quatro LODs; escada %d e TV %d fontes nativas amarelas.'):format(config.native_stair_count,config.native_tv_led_count))\n    print('[Mansao luz] Fontes nativas constantes;")
(O/'iluminacao_decorativa.lua').write_text(controller,encoding='utf-8')
readme=(B/'README.md').read_text(encoding='utf-8')+'''\n\n## Lentes visíveis, escada e TV — 08/10/2026\n\nEsta revisão mantém os 88 feixes estreitos brancos e os nove feixes amarelos dos pendentes, com alcance e força até o piso preservados. O pequeno núcleo recuado dos spots foi convertido em difusor de 10 a 11 cm, junto à abertura, em todos os quatro LODs; moldura, refletor e prismas preservados. Os seis cilindros ganharam faces inferiores preenchidas em amarelo, com malhas simples em todos os LODs. Sua textura emissiva usa amarelo mais saturado e potência moderada para reduzir o branco por excesso de exposição.\n\nA pedido do usuário, restaurados somente os 20 LEDs amarelos dos degraus, com emissão e fontes nativas locais sem sombras, e adicionada uma faixa atrás da borda superior da tela da TV, com três fontes locais amarelas. A faixa e suas luzes estão no próprio modelo da TV e acompanham seu reposicionamento. O painel, rack e colisão não mudam. Demais emissões decorativas e preenchimentos continuam desligados. Nenhuma alteração de clima, filtros, névoa, proteção climática ou bloom global.\n\n`luzmansao` e `mansaoluzes` no F8 mostram o estado. Aplicação: no console do servidor, `restart cidade_mansao`; depois feche completamente o FiveM e reconecte. Backup e verificações em `casa_vinewood/lentes_leds_20261008/`. A aparência e FPS no FiveM precisam ser conferidos após recarregar; a inspeção local valida arquivos nativos, cores, LODs e preservação dos demais dados.\n'''
(O/'README.md').write_text(readme,encoding='utf-8')
(P/'projeto.json').write_text(json.dumps(dict(targets=targets,lens_lods=lens,cylinder_faces=cap_rows,stairs=stair_rows,tv_lights=tv_rows,tv_strip=tvstrip,native_sources=120,ceiling_beams_unchanged=True,in_game_visual_verified=False),indent=2))
print('STAGED: four lens LODs; six yellow filled cylinder faces; 20 stair and three TV native LED sources.',flush=True)
