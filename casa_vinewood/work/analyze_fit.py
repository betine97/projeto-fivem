import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from PIL import Image,ImageDraw
from szio.gta5 import try_load_asset
a=try_load_asset(W/'work/native/ch2_09b_hs05.ydr')
faces=[]
models=next(iter(a.models.values()))
for m in models:
 for g in m.geometries:
  sh=a.shader_group.shaders[g.shader_index]
  mat=next(p.value for p in sh.parameters if p.name.lower()=='diffusesampler')
  if not isinstance(mat,str):mat=str(mat)
  vs=g.vertex_buffer['Position'].astype(float)
  for ids in g.index_buffer.reshape(-1,3):
   p=vs[ids];n=np.cross(p[1]-p[0],p[2]-p[0]);length=np.linalg.norm(n)
   if length<1e-8:continue
   faces.append(dict(material=mat,points=p.tolist(),normal=(n/length).tolist(),area=length*.5))
(W/'work/all_shell_faces.json').write_text(json.dumps(faces))
im=Image.new('RGB',(1500,950),'white');d=ImageDraw.Draw(im)
for panel,z in enumerate([0,4.5]):
 def xy(p):return (panel*750+80+(p[0]+15)*21,80+(16-p[1])*21)
 for y in range(-18,16,2):d.line([xy((-15,y)),xy((17,y))],fill='#dddddd');d.text(xy((-15,y)),str(y),fill='black')
 for x in range(-14,18,2):d.line([xy((x,-18)),xy((x,16))],fill='#dddddd');d.text(xy((x,16)),str(x),fill='black')
 for f in faces:
  p=np.array(f['points']);n=np.array(f['normal']);mat=f['material']
  if abs(n[2])>.2 or p[:,2].min()>z or p[:,2].max()<z:continue
  hits=[]
  for u,v in zip(p,np.roll(p,-1,axis=0)):
   if (u[2]<=z<v[2]) or (v[2]<=z<u[2]):hits.append(u+(v-u)*(z-u[2])/(v[2]-u[2]))
  if len(hits)==2:
   c='#1686d9' if 'wins' in mat else '#be7725' if 'doors' in mat else '#303030'
   d.line([xy(q) for q in hits],fill=c,width=3)
 d.text((panel*750+100,30),f'Native wall slice z={z} (blue windows, brown doors)',fill='black')
im.save(W/'work/native_slices.png')
print('faces',len(faces),'materials',sorted(set(q['material'] for q in faces)))

