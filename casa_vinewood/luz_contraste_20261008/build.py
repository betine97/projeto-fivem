"""Revise lighting from the user's overexposed in-game screenshot."""
import sys, json, hashlib, shutil, math
from pathlib import Path
from collections import Counter
P=Path(__file__).resolve().parent; R=P.parents[1]; D=R/'server-data/resources/cidade_mansao'; B=P/'backup'; O=P/'package'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(R/'casa_vinewood/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import pymateria as rp
import pymateria.gta5 as pm
import pymateria.gta5.gen8 as g8
import numpy as np
from PIL import Image
from szio.rpf import open_rpf
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon
from shapely.ops import unary_union
names=['mansao_teto','mansao_pendentes','mansao_tv']
targets=['stream/'+n+'.ydr' for n in names]+['iluminacao_ambiente.json','luzes_pendentes.json','iluminacao_decorativa.lua']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if not (P/'baseline.json').exists():
 (P/'baseline.json').write_text(json.dumps({f.relative_to(D).as_posix():sha(f) for f in D.rglob('*') if f.is_file()},indent=2))
 for rel in targets:
  q=B/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(D/rel,q)
baseline=json.loads((P/'baseline.json').read_text());assert all(sha(D/t)==baseline[t] for t in targets),'Concurrent lighting edit'
(O/'stream').mkdir(parents=True,exist_ok=True)
cfg=json.loads((B/'iluminacao_ambiente.json').read_text());assets={n:g8.Drawable.import_rsc(B/'stream'/(n+'.ydr')).result for n in names}
assert len(assets['mansao_teto'].lights)==116 and len(assets['mansao_pendentes'].lights)==9
ceiling=[r for r in cfg['native_lights'] if r['kind'].startswith('ceiling')]
pend=[r for r in cfg['native_lights'] if r['kind']=='pendant_yellow']
bounce=[r for r in cfg['native_lights'] if r['kind']=='bounce']
wash=[r for r in cfg['native_lights'] if r['kind']=='wall_wash']
assert [len(a) for a in [ceiling,pend,bounce,wash]]==[88,9,21,7]
changes=[]
def sync(r,li):
 r.update(position=list(li.position),rgb=list(li.color),intensity=float(li.intensity),range=float(li.falloff),falloff_exponent=float(li.falloff_exponent),inner_angle=float(li.cone_inner_angle),outer_angle=float(li.cone_outer_angle),no_specular=bool(li.flags & pm.LightFlags.NO_SPECULAR))
def tune(li,r,scale,rgb):
 old=dict(intensity=li.intensity,rgb=list(li.color),position=list(li.position),flags=li.flags.value)
 li.intensity*=scale;li.color=rp.ColorRGB(*rgb);li.volume_outer_color=rp.ColorRGB(*rgb)
 li.flags|=pm.LightFlags.NO_SPECULAR;li.specular_fade_distance=0
 sync(r,li);changes.append(dict(id=r['id'],before=old,after=dict(intensity=li.intensity,rgb=list(li.color),position=list(li.position),flags=li.flags.value)))
for li,row in zip(assets['mansao_teto'].lights,ceiling+bounce+wash):
 assert np.allclose(li.position,row['position'],atol=1e-5)
 if row['kind'].startswith('ceiling'): tune(li,row,.48,(255,186,110))
 elif row['kind']=='bounce':
  # A low source near the floor flooded the pale tiles. Lift the existing
  # indirect source to body height, lower it, and keep its floor cull plane.
  pos=list(li.position);pos[2]+=0.85;li.position=rp.Vector3f(*pos)
  li.culling_plane.distance+=.85
  tune(li,row,.40,(255,195,132))
 else: tune(li,row,.70,(255,180,94))
for li,row in zip(assets['mansao_pendentes'].lights,pend): tune(li,row,.68,(255,173,80))
tv=[r for r in cfg['decorative_native_lights'] if r['kind']=='tv_yellow']
for li,row in zip(assets['mansao_tv'].lights,tv): tune(li,row,.58,(255,180,94))
emission=[]
for name,power in [('mansao_pendentes',1.5),('mansao_tv',1.2)]:
 for shader in assets[name].shader_group.shaders:
  for param in shader.parameters:
   if param.name==pm.HashString('emissivemultiplier'):
    emission.append(dict(model=name,before=list(param.data[0]),after=power));param.data=[rp.Vector4f(power,0,0,0)]
for name,a in assets.items():g8.Drawable.export_rsc(a,O/'stream'/(name+'.ydr'))
# Validate exact variable spelling against original local GTA data, read-only.
postfx={'postfx_intensity_bloom':.08,'postfx_noise':0.,'screen_blur_intensity':0.,'dof_blur_mid':0.,'dof_blur_far':0.}
game=Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V')
rpf=open_rpf(game/'common.rpf');root=ET.fromstring(rpf.read_bytes('data/timecycle/timecycle_mods_1.xml'));tags={e.tag for e in root.iter()};rpf.close()
assert set(postfx)<=tags
regions=json.loads((R/'casa_vinewood/luz_permanente_20261008/projeto_luminotecnico.json').read_text())['regions']
shape=unary_union([Polygon(r['polygon']).buffer(.21) for r in regions]);parts=list(shape.geoms) if shape.geom_type=='MultiPolygon' else [shape]
cfg['clean_postfx']={'enabled':True,'modifier':'mansao_luz_nitida_v8','variables':postfx,'interior_polygons':[list(map(list,p.exterior.coords)) for p in parts],'z_min':-.75,'z_max':6.7}
cfg.update(version=8,lighting_style='warm_contrast_reduced_glare',native_ceiling_color=[255,186,110],description='Warm fixtures with lower overlapping intensity and no local specular glare; indirect sources raised off tiles. Interior-only bloom/noise/DOF control; no weather/fog overrides.')
(O/'iluminacao_ambiente.json').write_text(json.dumps(cfg,indent=2,ensure_ascii=False),encoding='utf-8')
pcfg=json.loads((B/'luzes_pendentes.json').read_text());pcfg.update(lights=pend,description='Amber pendants: controlled power and emissive brightness, unchanged softened beam coverage.')
(O/'luzes_pendentes.json').write_text(json.dumps(pcfg,indent=2,ensure_ascii=False),encoding='utf-8')
shutil.copy2(P/'controller.lua',O/'iluminacao_decorativa.lua')
measure=[]
for name,path,box in [('reference',r'C:/Users/erons/AppData/Local/Temp/codex-clipboard-6c821d9b-80a5-47c8-8aa0-cc514d163ac0.png',[.21,.86,.34,.98]),('reported_overexposure',r'C:/Users/erons/AppData/Local/Temp/codex-clipboard-4b73e243-fa2b-4933-a9a6-baca448c486e.png',[.6,.83,.72,.94])]:
 im=Image.open(path).convert('RGB');w,h=im.size;crop=np.asarray(im.crop([int(box[0]*w),int(box[1]*h),int(box[2]*w),int(box[3]*h)]));rgb=np.median(crop.reshape(-1,3),axis=0)
 measure.append(dict(image=name,normalized_crop=box,median_rgb=rgb.tolist()))
(P/'project.json').write_text(json.dumps(dict(targets=targets,changes=changes,emission_changes=emission,postfx=postfx,variable_names_checked_in_original_game=True,screenshot_samples=measure,diagnosis='Bloom/excess local light are inferred from screenshot; no live weather/filter values recorded yet.',visual_match_verified=False),indent=2))
print('STAGED',len(targets),'files; native counts preserved; five supported postfx variables')
