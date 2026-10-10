import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('personagens/catalogo_nativo').resolve()))
import render_catalog as r
from PIL import ImageDraw
base=r.ROOT/'personagens/calca_tatica'
a=r.try_load_asset(base/'source/lowr_001_r.ydd');d=next(iter(a.drawables.values()));im=r.Image.new('RGB',(1024,1024),(35,35,35));dr=ImageDraw.Draw(im)
for m in d.models[min(d.models)]:
 for g in m.geometries:
  v=g.vertex_buffer;p=v['Position'];uv=v['TexCoord0'];n=v['Normal']
  print('bounds',p.min(0),p.max(0),'uv',uv.min(0),uv.max(0))
  for tri in g.index_buffer.reshape(-1,3):
   pos=p[tri].mean(0); norm=n[tri].mean(0);sign=1 if pos[0]>0 else -1
   exterior=sign*norm[0]>.5
   color=(80,80,80)
   if exterior and -.38<pos[2]<-.10:color=(255,45,45)
   elif exterior and -.88<pos[2]<-.55:color=(30,180,255)
   elif abs(pos[0])<.25 and pos[2]>-.10:color=(170,150,30)
   dr.polygon([tuple(x*1024) for x in uv[tri]],fill=color,outline=(100,100,100))
  for z in [-.2,-.3,-.6,-.8]:
   ix=(abs(p[:,2]-z)<.025)&(r.np.sign(p[:,0])*n[:,0]>.7)
   if ix.any():print(z,'exterior UV',uv[ix].min(0),uv[ix].max(0))
im.save(base/'uv_guide.png')
