"""Measure existing architectural joins and render horizontal sections."""
import sys,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps')]
import numpy as np
from PIL import Image,ImageDraw,ImageFont
rows=json.loads((W/'colisoes_fivem.json').read_text())
spec=json.loads((W/'encaixe_fachada.json').read_text())
im=Image.new('RGB',(1800,1250),'#eeeeee');d=ImageDraw.Draw(im)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
def section(p,z):
 out=[]
 for a,b in zip(p,np.roll(p,-1,axis=0)):
  if (a[2]<=z<b[2]) or (b[2]<=z<a[2]):out.append(a+(b-a)*(z-a[2])/(b[2]-a[2]))
 return out
for i,z in enumerate([-.7,1.6,2.6,2.9,4.5,6.4]):
 ox=(i%3)*600;oy=(i//3)*625
 def xy(p):return (ox+25+(p[0]+14)*17,oy+60+(12-p[1])*17)
 d.text((ox+15,oy+10),f'Local Z={z:.2f} m',font=font,fill='black')
 for key in ['ground_polygon','upper_polygon']:
  q=spec[key];d.line([xy(p) for p in q+[q[0]]],fill='#888888',width=1)
 for row in rows:
  if row['group']!='mansao_paredes':continue
  q=section(np.array(row['points']),z)
  if len(q)==2:d.line([xy(p) for p in q],fill=('#ca3020' if row['source']=='Revestimento da fachada nativa' else '#1957af'),width=2)
 for row in rows:
  if row['group']!='mansao_vidros':continue
  q=section(np.array(row['points']),z)
  if len(q)==2:d.line([xy(p) for p in q],fill='#009c92',width=2)
im.save(W/'work/secoes_antes_frestas.png')
raw=json.loads((W/'work/all_shell_faces.json').read_text())
levels={}
for q in raw:
 if not any(k in q['material'].lower() for k in ['wall32','wall_brick_32','idwall','doors']):continue
 for p in q['points']:
  key=round(p[2],3);levels[key]=levels.get(key,0)+1
print('Native wall frequent Z',sorted(levels.items(),key=lambda x:x[1],reverse=True)[:40])
print('SECTIONS',W/'work/secoes_antes_frestas.png')
