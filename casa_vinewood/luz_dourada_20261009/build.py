"""Warm architectural lighting refinement based on the latest gameplay image."""
import sys,json,hashlib,shutil,math
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'server-data/resources/cidade_mansao';B=P/'backup';O=P/'package'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from PIL import Image
import pymateria as rp
import pymateria.gta5 as pm
import pymateria.gta5.gen8 as g8
names=['mansao_teto','mansao_pendentes','mansao_tv','mansao_spot_embutido']
targets=['stream/'+n+'.ydr' for n in names]+['iluminacao_ambiente.json','luzes_pendentes.json','iluminacao_decorativa.lua']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if not (P/'baseline.json').exists():
 (P/'baseline.json').write_text(json.dumps({f.relative_to(D).as_posix():sha(f) for f in D.rglob('*') if f.is_file()},indent=2))
 for t in targets:
  q=B/t;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(D/t,q)
base=json.loads((P/'baseline.json').read_text());assert all(sha(D/t)==base[t] for t in targets),'Concurrent lighting edit'
(O/'stream').mkdir(parents=True,exist_ok=True)
assets={n:g8.Drawable.import_rsc(B/'stream'/(n+'.ydr')).result for n in names}
cfg=json.loads((B/'iluminacao_ambiente.json').read_text())
ceiling=[r for r in cfg['native_lights'] if r['kind'].startswith('ceiling')];bounce=[r for r in cfg['native_lights'] if r['kind']=='bounce'];wash=[r for r in cfg['native_lights'] if r['kind']=='wall_wash'];pend=[r for r in cfg['native_lights'] if r['kind']=='pendant_yellow']
assert [len(r) for r in [ceiling,bounce,wash,pend]]==[88,21,7,9]
changes=[]
def sync(row,li):
 row.update(position=list(li.position),rgb=list(li.color),intensity=float(li.intensity),range=float(li.falloff),falloff_exponent=float(li.falloff_exponent),inner_angle=float(li.cone_inner_angle),outer_angle=float(li.cone_outer_angle),shadow=bool(li.flags & pm.LightFlags.CAST_SHADOWS),no_specular=True)
def tint(li,rgb):li.color=rp.ColorRGB(*rgb);li.volume_outer_color=rp.ColorRGB(*rgb)
for li,row in zip(assets['mansao_teto'].lights,ceiling+bounce+wash):
 old=dict(position=list(li.position),intensity=float(li.intensity),rgb=list(li.color))
 if row['kind'].startswith('ceiling'):
  tint(li,(255,165,76));li.intensity*=.90
 elif row['kind']=='bounce':
  tint(li,(255,185,105));li.intensity*=.72 if row['room'] in ['Sala de estar','Sala de jantar'] else .80
 else:
  # Put each wash on its intended interior face, not in a partition or on
  # the opposite side. Keep seven local sources rather than a broad fill.
  settings=[([-8.70,-11.40,2.30],4.2,1.7,.80),([-8.70,-6.00,2.30],4.2,1.7,.80),
            ([6.72,-2.65,1.15],2.2,2.0,.95),([11.80,-1.38,1.20],2.1,2.2,.80),
            ([6.05,-2.40,1.15],2.2,1.7,.75),([13.82,-6.40,.90],2.2,1.5,.65),
            ([-7.40,-1.20,1.15],2.2,1.7,.70)]
  pos,length,radius,power=settings[wash.index(row)]
  li.position=rp.Vector3f(*pos);li.extents=rp.Vector3f(length,length,length);li.falloff=radius;li.intensity=power
  li.culling_plane.distance=pos[2]-row['floor_z']+.03;tint(li,(255,158,62));row['length_m']=length
 sync(row,li);changes.append(dict(id=row['id'],before=old,after=dict(position=list(li.position),intensity=float(li.intensity),rgb=list(li.color))))
for li,row in zip(assets['mansao_pendentes'].lights,pend):
 li.intensity*=1.25 if row['id'].startswith('cylinder') else 1.10;tint(li,(255,174,72));sync(row,li)
# Preserve the existing shadow source and add four restrained sources: two
# pendant highlights and two ceiling sources in the living/piano area.
shadows=[]
for target in [(-6.,-7.5),(-6.,-2.3)]:
 candidates=[(li,row) for li,row in zip(assets['mansao_teto'].lights,ceiling) if row['position'][2]-row['floor_z']>5]
 li,row=min(candidates,key=lambda q:math.dist(q[1]['position'][:2],target))
 li.flags|=pm.LightFlags.CAST_SHADOWS;li.shadow_fade_distance=28;li.shadow_blur=2;sync(row,li);shadows.append(row['id'])
for li,row in zip(assets['mansao_pendentes'].lights,pend):
 if row['id'] in ['cylinder_2','cylinder_5']:
  li.flags|=pm.LightFlags.CAST_SHADOWS;li.shadow_fade_distance=22;li.shadow_blur=2;sync(row,li);shadows.append(row['id'])
tv=[r for r in cfg['decorative_native_lights'] if r['kind']=='tv_yellow']
for li,row in zip(assets['mansao_tv'].lights,tv):li.intensity*=1.3;tint(li,(255,174,70));sync(row,li)
emission=[]
for name,power in [('mansao_pendentes',2.7),('mansao_tv',1.7),('mansao_spot_embutido',3.6)]:
 for shader in assets[name].shader_group.shaders:
  for param in shader.parameters:
   if param.name==pm.HashString('emissivemultiplier'):
    emission.append(dict(model=name,before=list(param.data[0]),after=power));param.data=[rp.Vector4f(power,0,0,0)]
# Replace only the existing tiny constant-colour lens swatch. No photograph,
# surface texture or model geometry is edited; the white bezel stays white.
f=P/'spot_lente_quente.dds';Image.new('RGBA',(4,4),(255,223,160,255)).save(f,pixel_format='DXT5')
assets['mansao_spot_embutido'].shader_group.texture_dictionary.textures[pm.HashString('spot_lente')].import_dds(f)
for n,a in assets.items():g8.Drawable.export_rsc(a,O/'stream'/(n+'.ydr'))
cfg.update(version=9,lighting_style='golden_architectural_accents',native_ceiling_color=[255,165,76],native_shadow_count=sum(bool(li.flags & pm.LightFlags.CAST_SHADOWS) for n,a in assets.items() for li in a.lights),description='Golden fixtures and brighter warm lenses; seven face-aligned wall washes, lower indirect fill, limited native shadows. Preserve v8 interior optical cleanup and fixed light availability.')
assert cfg['native_shadow_count']<=5
cfg['clean_postfx']['modifier']='mansao_luz_nitida_v9'
(O/'iluminacao_ambiente.json').write_text(json.dumps(cfg,indent=2,ensure_ascii=False),encoding='utf-8')
pcfg=json.loads((B/'luzes_pendentes.json').read_text());pcfg.update(lights=pend,description='Golden pendant lenses and controlled direct light, with two additional bounded shadow sources.')
(O/'luzes_pendentes.json').write_text(json.dumps(pcfg,indent=2,ensure_ascii=False),encoding='utf-8')
controller=(B/'iluminacao_decorativa.lua').read_text().replace('PERFIL v8','PERFIL v9').replace('Perfil v8','Perfil v9').replace('potencia e brilho especular reduzidos.','destaques dourados, paredes e sombras locais.');(O/'iluminacao_decorativa.lua').write_text(controller,encoding='utf-8')
measure=[]
for label,path,box in [('reference',r'C:/Users/erons/AppData/Local/Temp/codex-clipboard-dbb50afa-0e5a-48b4-a6c3-4274e66b5bf4.png',[.21,.86,.34,.98]),('current_v8',r'C:/Users/erons/AppData/Local/Temp/codex-clipboard-183b9011-4ff4-430c-8ace-b634b85f8947.png',[.55,.82,.68,.94])]:
 im=Image.open(path).convert('RGB');w,h=im.size;rgb=np.median(np.asarray(im.crop([int(box[0]*w),int(box[1]*h),int(box[2]*w),int(box[3]*h)])).reshape(-1,3),axis=0);measure.append(dict(image=label,median_rgb=rgb.tolist(),crop=box))
(P/'project.json').write_text(json.dumps(dict(targets=targets,changes=changes,emission_changes=emission,wall_wash=wash,additional_shadow_ids=shadows,total_shadow_sources=cfg['native_shadow_count'],screenshot_samples=measure,optical_profile_values_unchanged=True,observed_v8_log=dict(clear_weather='EXTRASUNNY',primary_filter=-1,previous_extra_filter=-1),visual_match_verified=False),indent=2))
print('STAGED',len(targets),'files;',cfg['native_shadow_count'],'shadow sources; total lights unchanged')
