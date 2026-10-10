"""Scoped native lighting revision following the two supplied screenshots."""
import sys,json,math,hashlib,shutil,copy
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao';B=P/'backup';O=P/'package'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
import pymateria as rp
import pymateria.gta5 as pm
import pymateria.gta5.gen8 as g8
from szio.gta5.drawables import Light,LightType,LightFlashiness
from szio.gta5.native.adapters.drawable import _map_light_to_native
from szio.types import Vector
from PIL import Image
names=['mansao_teto','mansao_pendentes','mansao_tv']
targets=['stream/'+n+'.ydr' for n in names]+['iluminacao_ambiente.json','luzes_pendentes.json','iluminacao_decorativa.lua']
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
if not (P/'baseline.json').exists():
 (P/'baseline.json').write_text(json.dumps({f.relative_to(D).as_posix():sha(f) for f in D.rglob('*') if f.is_file()},indent=2))
 for rel in targets:
  q=B/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(D/rel,q)
baseline=json.loads((P/'baseline.json').read_text());assert all(sha(D/t)==baseline[t] for t in targets),'Concurrent lighting edit'
(O/'stream').mkdir(parents=True,exist_ok=True)
assets={n:g8.Drawable.import_rsc(B/'stream'/(n+'.ydr')).result for n in names}
cfg=json.loads((B/'iluminacao_ambiente.json').read_text())
rows=cfg['native_lights'];white=[r for r in rows if r['kind']=='ceiling_white'];pend=[r for r in rows if r['kind']=='pendant_yellow'];bounce=[r for r in rows if r['kind']=='bounce']
assert len(white)==88 and len(pend)==9 and len(bounce)==21
warm=(255,212,163);amber=(255,194,112)
def color(li,rgb):li.color=rp.ColorRGB(*rgb);li.volume_outer_color=rp.ColorRGB(*rgb)
def sync(row,li):
 row.update(position=list(li.position),rgb=list(li.color),intensity=float(li.intensity),range=float(li.falloff),falloff_exponent=float(li.falloff_exponent),inner_angle=float(li.cone_inner_angle),outer_angle=float(li.cone_outer_angle))
direct=[]
for name,data in [('mansao_teto',white),('mansao_pendentes',pend)]:
 for li,row in zip(assets[name].lights,data):
  assert np.allclose(li.position,row['position'],atol=1e-5)
  h=row['position'][2]-row['floor_z'];tall=h>5
  old={k:row[k] for k in ['intensity','range','inner_angle','outer_angle','rgb']}
  if name=='mansao_teto':
   radius=5.2 if tall else 3.2
   li.intensity=3.2 if tall else 1.9;li.falloff=max(h+3.1,math.hypot(h,radius)*1.35);li.falloff_exponent=3
   li.cone_inner_angle=0;li.cone_outer_angle=math.degrees(math.atan(radius/h));color(li,warm)
   row['kind']='ceiling_warm'
  else:
   radius=2.1 if row['id'].startswith('linear') else 2.8
   li.intensity=1.45 if row['id'].startswith('linear') else 1.15
   li.falloff=max(h+2.8,math.hypot(h,radius)*1.3);li.falloff_exponent=3
   li.cone_inner_angle=3;li.cone_outer_angle=math.degrees(math.atan(radius/h));color(li,amber)
  row['floor_radius_m']=radius;row['beam_height_m']=h;row['edge_style']='soft_warm_architectural';sync(row,li)
  direct.append(dict(id=row['id'],before=old,after=copy.deepcopy(row)))
# Bring up midtones in walls and furniture, with localized reflected light.
# Existing room points stay in place, remain native and keep the floor cull.
for li,row in zip(list(assets['mansao_teto'].lights)[88:],bounce):
 assert np.allclose(li.position,row['position'],atol=1e-5)
 li.intensity=.62 if row['room'] in ['Sala de estar','Sala de jantar'] else .48
 li.falloff_exponent=5;li.falloff+=.45;color(li,warm);sync(row,li)
flags=pm.LightFlags.BOTH_INTERIOR_AND_EXTERIOR|pm.LightFlags.FX|pm.LightFlags.DONT_LIGHT_ALPHA|pm.LightFlags.NO_SPECULAR
def native(ident,pos,radius,power,rgb,direction,length,floor=-.8,moving=False):
 f=flags|pm.LightFlags.USE_CULL_PLANE
 if moving:f|=pm.LightFlags.MOVING_LIGHT_SOURCE
 return _map_light_to_native(Light(light_type=LightType.CAPSULE,position=Vector(pos),direction=Vector(direction),tangent=Vector([0,1,0] if direction[0] else [1,0,0]),extent=Vector([length]*3),color=rgb,flashiness=LightFlashiness.CONSTANT,intensity=power,flags=f.value,time_flags=0xffffff,bone_id=0,group_id=0,light_hash=ident,falloff=radius,falloff_exponent=4,culling_plane_normal=Vector([0,0,1]),culling_plane_offset=pos[2]-floor+.03,volume_intensity=0,volume_outer_intensity=0,volume_size_scale=1,volume_outer_color=rgb,volume_outer_exponent=1,corona_size=0,corona_intensity=0,corona_z_bias=0,projected_texture_hash='',light_fade_distance=160,shadow_fade_distance=0,specular_fade_distance=0,volumetric_fade_distance=0,shadow_near_clip=.05,shadow_blur=0,cone_inner_angle=0,cone_outer_angle=0))
# Local wall wash is limited to solid plaster walls/returns, not window glass.
# Vertical capsule attenuation avoids the isolated circular white patches.
wash=[]
for i,(pos,length,radius,power) in enumerate([
 ([-8.97,-11.40,2.30],4.2,1.5,.70),
 ([-8.97,-6.00,2.30],4.2,1.5,.70),
 ([6.10,-3.05,.75],2.5,1.6,.60),
 ([4.82,-1.08,.75],2.5,1.7,.58),
 ([10.8,-1.08,.75],2.5,1.7,.58),
 ([14.04,-6.4,.75],2.5,1.5,.52),
 ([-7.4,-1.08,.75],2.5,1.6,.52),
 ]):
  li=native(151+i,pos,radius,power,amber,[0,0,1],length);assets['mansao_teto'].lights.append(li)
  row=dict(id='warm_wall_'+str(i+1),kind='wall_wash',position=pos,floor_z=-.8,source_type='CAPSULE',direction=[0,0,1],length_m=length,no_specular=True,cull_below_floor=True);sync(row,li);wash.append(row)
# Follow the existing TV top strip and frame footprint. These lights move
# with the TV entity when its saved transform changes; geometry is unchanged.
tv=[];yc=(-9.870-7.677)/2
for i,(pos,direction,length,power,radius) in enumerate([
 ([-8.775,yc,1.464],[0,1,0],2.193,1.05,1.10),
 ([-8.775,-9.870,.92],[0,0,1],1.088,.55,.72),
 ([-8.775,-7.677,.92],[0,0,1],1.088,.55,.72),
 ([-8.775,yc,.376],[0,1,0],2.193,.48,.68),
 ]):
  li=native(251+i,pos,radius,power,amber,direction,length,moving=True)
  row=dict(id='tv_frame_'+str(i+1),kind='tv_yellow',position=pos,source_type='CAPSULE',direction=direction,length_m=length,floor_z=-.8);sync(row,li);tv.append((li,row))
assets['mansao_tv'].lights=[li for li,_ in tv]
# Increase only existing emitter brightness, preserving their texture/shader
# hashes and every other material parameter.
emission_changes=[]
for name,power in [('mansao_pendentes',2.4),('mansao_tv',2.2)]:
 for shader in assets[name].shader_group.shaders:
  for param in shader.parameters:
   if param.name==pm.HashString('emissivemultiplier'):
    old=list(param.data[0]);param.data=[rp.Vector4f(power,0,0,0)];emission_changes.append(dict(model=name,before=old,after=power))
for name,a in assets.items():g8.Drawable.export_rsc(a,O/'stream'/(name+'.ydr'))
cfg['native_lights']=pend+white+bounce+wash
cfg['decorative_native_lights']=[r for r in cfg['decorative_native_lights'] if not r['kind'].startswith('tv')]+[r for _,r in tv]
cfg.update(version=7,lighting_style='warm_architectural_reference',native_count=149,native_wall_wash_count=7,native_tv_led_count=4,native_ceiling_color=list(warm),description='Warm architectural reference: softened warm ceiling fixtures, amber pendants, localized wall wash and TV frame halo. Fixed native lights, no fog/coronas/weather/global exposure changes.')
(O/'iluminacao_ambiente.json').write_text(json.dumps(cfg,indent=2,ensure_ascii=False),encoding='utf-8')
pcfg=json.loads((B/'luzes_pendentes.json').read_text());pcfg.update(lights=pend,description='Amber pendants with brighter existing lenses and continuous softened illumination to the floor.')
(O/'luzes_pendentes.json').write_text(json.dumps(pcfg,indent=2,ensure_ascii=False),encoding='utf-8')
controller=(B/'iluminacao_decorativa.lua').read_text().replace('spots brancos','spots quentes').replace('Focos suaves ate o piso;','Perfil quente da referencia, focos suaves ate o piso;').replace('Lentes brancas em quatro LODs','Lentes em quatro LODs')
(O/'iluminacao_decorativa.lua').write_text(controller,encoding='utf-8')
metrics=[]
for name,path,box in [('reference',r'C:/Users/erons/AppData/Local/Temp/codex-clipboard-6c821d9b-80a5-47c8-8aa0-cc514d163ac0.png',[.20,.86,.34,.98]),('current',r'C:/Users/erons/AppData/Local/Temp/codex-clipboard-cdc0810d-f5cd-4ede-b714-c0f240cf79de.png',[.30,.85,.35,.98])]:
 im=Image.open(path).convert('RGB');w,h=im.size;crop=im.crop([int(box[0]*w),int(box[1]*h),int(box[2]*w),int(box[3]*h)]);rgb=np.median(np.asarray(crop).reshape(-1,3),axis=0)
 metrics.append(dict(image=name,floor_sample_median_rgb=rgb.tolist(),normalized_rgb=(rgb/rgb[0]).tolist(),limitations='Different camera/framing: color guide, not pixel equivalence or new render.'))
(P/'project.json').write_text(json.dumps(dict(targets=targets,direct=direct,bounce=bounce,wash=wash,tv=[r for _,r in tv],emission_changes=emission_changes,reference_metrics=metrics,in_game_verified=False),indent=2));print('WARM_LIGHTING_STAGED',len(targets),'targets;149 total indoor native sources')
