import sys,json,math
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(R/'casa_vinewood/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from PIL import Image,ImageDraw
from shapely.geometry import Polygon,Point,box
from shapely.ops import unary_union
from shapely import affinity
from szio.gta5 import try_load_asset,LodLevel
d=json.loads((R/'castelo_rockford/medidas.json').read_text());origin=np.array(d['origin']);a=try_load_asset(R/'server-data/resources/cidade_castelo_livre/stream/bh1_45_plot4a_ter_dcs.ydr')
triangles=[];shaders=[]
for m in a.models[LodLevel.HIGH]:
 for g in m.geometries:
  for t in (g.vertex_buffer['Position']+origin)[g.index_buffer.reshape(-1,3)]:triangles.append(t);shaders.append(g.shader_index)
np.savez_compressed(P/'terreno.npz',triangles=np.array(triangles),shaders=shaders)
anchor=np.array([-946.,207.]);rot=lambda ps,ang:np.array(ps)@np.array([[math.cos(math.radians(ang)),math.sin(math.radians(ang))],[-math.sin(math.radians(ang)),math.cos(math.radians(ang))]])+anchor
foot=unary_union([box(-14,-10,14,10)]+[Point(x,y).buffer(3.1,quad_segs=10) for x in [-11.5,11.5] for y in [-8,8]])
world=affinity.translate(affinity.rotate(foot,-30,origin=(0,0)),*anchor)
courtdata=json.loads((R/'castelo_rockford/modelo/quadra_original_local.json').read_text());court=unary_union([Polygon(p) for p in courtdata['polygon']]);court=affinity.translate(affinity.rotate(court,60,origin=(0,0)),*anchor)
im=Image.new('RGB',(1300,1080),'#f2efe7');dr=ImageDraw.Draw(im)
def xy(p):return ((p[0]+1000)*14,1050-(p[1]-172)*14)
colors=['#adb0a7','#b9c2a6','#c5b8a0','#a5b8a2','#d2ccc0','#bcb1a0','#ddd0b8','#b2c3af','#a4b7a4','#8c9f87','#d0c2aa']
for t,idx in zip(triangles,shaders):
 dr.polygon([xy(p) for p in t],fill=colors[idx%len(colors)])
def line(poly,color,width):dr.line([xy(p) for p in poly.exterior.coords],fill=color,width=width)
line(world,'#c42424',4);line(court,'#247bc4',4)
for p in range(-995,-914,5):
 dr.line([xy((p,175)),xy((p,240))],fill='#ffffff',width=1);dr.text(xy((p,173)),str(p),fill='black')
for p in range(175,241,5):dr.text(xy((-998,p)),str(p),fill='black')
for loc in [(0,-15),(-19,0),(0,15),(19,0)]:
 pt=rot([loc],-30)[0];dr.text(xy(pt),str(loc),fill='black')
im.save(P/'implantacao_diagnostico.png')
print('NEW FOOT outside previously cleared:',world.difference(Polygon(d['removed_footprint_polygons'][0])).area,'court intersection',world.intersection(court).area)
print('world bounds',world.bounds,'court',court.bounds)
for i,s in enumerate(a.shader_group.shaders):print(i,s.preset_filename,[(p.name,p.value) for p in s.parameters if isinstance(p.value,str)])
