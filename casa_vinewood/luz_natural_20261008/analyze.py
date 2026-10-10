"""Relative analytic light distribution, NOT a FiveM render or exposure test.
Uses CodeWalker attenuation/angular formula and a Lambertian horizontal floor.
Ignores geometry occlusion, textures, HDR tone mapping and global environment.
"""
import sys,json,math
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(R/'casa_vinewood/work/pydeps')]
import numpy as np
from shapely.geometry import Polygon,Point
from PIL import Image,ImageDraw,ImageFont
before=json.loads((P/'backup/iluminacao_ambiente.json').read_text());after=json.loads((P/'package/iluminacao_ambiente.json').read_text())
regions=json.loads((R/'casa_vinewood/luz_permanente_20261008/projeto_luminotecnico.json').read_text())['regions']

def evaluate(rows,points,floor):
 result=np.zeros(len(points))
 for r in rows:
  if not math.isclose(r['floor_z'],floor,abs_tol=.01):continue
  delta=np.array(r['position'])-points;dist=np.linalg.norm(delta,axis=1);d=dist/r['range']
  atten=np.clip((1-d)/(1+d*d*r['falloff_exponent']),0,1)
  cosine=np.clip(delta[:,2]/np.maximum(dist,1e-8),0,1)
  if r['kind']!='bounce':
   angle=np.degrees(np.arccos(np.clip(delta[:,2]/np.maximum(dist,1e-8),-1,1)))
   inner=r['inner_angle'];outer=r['outer_angle'];edge=np.clip(1-(angle-inner)/(outer-inner),0,1)
   atten*=edge
  result+=atten*cosine*r['intensity']
 return result

results=[]
for region in regions:
 poly=Polygon(region['polygon']).buffer(-.2);floor=-.8 if region['level']=='terreo' else 2.808
 x0,y0,x1,y1=poly.bounds;points=np.array([[x,y,floor+.01] for x in np.arange(x0,x1,.15) for y in np.arange(y0,y1,.15) if poly.contains(Point(x,y))])
 old=evaluate(before['native_lights'],points,floor);new=evaluate(after['native_lights'],points,floor)
 stats=lambda a:dict(zip(['min','p10','median','p90','max'],map(float,np.quantile(a,[0,.1,.5,.9,1]))))
 cv=lambda a:float(a.std()/a.mean()) if a.mean()>0 else None
 results.append(dict(room=region['name'],level=region['level'],sample_count=len(points),before=stats(old),after=stats(new),coefficient_of_variation_before=cv(old),coefficient_of_variation_after=cv(new)))

# Compare isolated fixture profiles as well as the room sum. This tests removal
# of the overbright flat core and verifies a continuous edge to zero.
ratios=[];profiles=[]
for a,b in zip(before['native_lights'],after['native_lights'][:97]):
 h=b['position'][2]-b['floor_z'];radius=b['floor_radius_m'];x,y,z=b['position']
 points=np.array([[x+offset,y,b['floor_z']+.01] for offset in [0,radius*.25,radius*.5,radius*.75,radius*1.01]])
 aa=evaluate([a],points,a['floor_z']);bb=evaluate([b],points,b['floor_z'])
 assert np.all(np.diff(bb)<0) and bb[-1]==0 and bb[0]>0
 ratio=float(bb[0]/aa[0]);assert ratio<.3
 ratios.append(ratio);profiles.append(dict(id=b['id'],axis_ratio=ratio,radial_fraction=[0,.25,.5,.75,1.01],new_irradiance=bb.tolist()))
focus=[r for r in results if r['room'] in ['Sala de estar','Sala de jantar','Cozinha']]
assert len(focus)==3 and all(r['coefficient_of_variation_after']<r['coefficient_of_variation_before']*.65 for r in focus)
assert all(r['after']['min']>0 for r in focus)
output=dict(passed=True,method='CodeWalker attenuation and angular ramp, relative intensity multiplied by horizontal Lambertian response',limitations=['Not GTA/FiveM exposure or visual QA','No geometry occlusion, textures, HDR, postprocessing or environmental light','Decorative LEDs excluded','Only fixture-assigned floor is sampled'],fixture_axis_reduction_percent=dict(min=100*(1-max(ratios)),median=100*(1-float(np.median(ratios))),max=100*(1-min(ratios))),rooms=results,fixture_profiles=profiles)
(P/'distribution_analysis.json').write_text(json.dumps(output,indent=2))
print(json.dumps(dict(axis_reduction_percent=output['fixture_axis_reduction_percent'],main_rooms=focus),indent=2),flush=True)

# Illustrative measured-function graph. Labels explicitly distinguish this
# numeric approximation from screenshots or a game preview.
canvas=Image.new('RGB',(1100,620),'#faf8f4');draw=ImageDraw.Draw(canvas)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
draw.text((40,20),'Distribuição relativa no piso — aproximação matemática',fill='#222d36',font=font)
draw.text((40,52),'Mesma fonte branca, mesmo piso; sem exposição, texturas ou oclusão do FiveM.',fill='#59636d',font=small)
a=next(r for r in before['native_lights'] if r['kind']=='ceiling_white' and 3<r['beam_height_m']<4)
b=next(r for r in after['native_lights'] if r['id']==a['id']);x,y,z=b['position'];offset=np.linspace(-3,3,601)
points=np.array([[x+v,y,b['floor_z']+.01] for v in offset]);old=evaluate([a],points,a['floor_z']);new=evaluate([b],points,b['floor_z'])
x0,y0,x1,y1=100,115,1040,465;ymax=float(old.max())*1.1
draw.line((x0,y0,x0,y1,x1,y1),fill='#78848e',width=2)
for tick in np.arange(-3,3.1,1):
 xp=x0+(tick+3)/6*(x1-x0);draw.line((xp,y0,xp,y1),fill='#e0e3e4');draw.text((xp-8,y1+10),str(int(tick)),fill='#59636d',font=small)
for values,color in [(old,'#b86d43'),(new,'#34716a')]:
 xy=[(x0+(v+3)/6*(x1-x0),y1-val/ymax*(y1-y0)) for v,val in zip(offset,values)];draw.line(xy,fill=color,width=4)
draw.text((410,505),'Distância lateral ao eixo da luminária (m)',fill='#59636d',font=small)
draw.text((120,115),'Anterior: foco intenso e borda curta',fill='#b86d43',font=font)
draw.text((120,145),'Atual: pico menor e queda gradual',fill='#34716a',font=font)
draw.text((40,555),'O preenchimento indireto é separado do foco e reduz as áreas escuras entre luminárias.',fill='#222d36',font=small)
draw.text((40,583),'Resultado final e FPS precisam ser conferidos no jogo após recarregar os arquivos.',fill='#59636d',font=small)
canvas.save(P/'distribuicao_relativa.png')
