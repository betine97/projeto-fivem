import bpy,json,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path.insert(0,str(R/'laboratorio_fivem/work/pydeps'))
from PIL import Image
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_encaixada.blend'))
ob=bpy.data.objects['Painel TV rack e decoracao Meshy'];me=ob.data;uv=me.uv_layers[0]
im=np.array(Image.open(W/'work/materiais/tv_original_albedo.jpg').convert('RGB'));h,w=im.shape[:2]
rows=[]
for p in me.polygons:
 c=p.center
 if not(-10.8<c.y<-6.8 and .3<c.z<2.2 and p.normal.x>.75):continue
 u=np.array([uv.data[i].uv for i in p.loop_indices]);m=u.mean(0)
 color=im[int((1-m[1])*(h-1)),int(m[0]*(w-1))]
 rows.append(dict(index=p.index,center=list(c),normal=list(p.normal),uv=u.tolist(),color=color.tolist()))
dark=[r for r in rows if max(r['color'])<35]
print('DARK_FACE_BOUNDS',np.min([r['center'] for r in dark],0),np.max([r['center'] for r in dark],0),len(dark),flush=True)
(W/'work/tv_screen_faces.json').write_text(json.dumps(rows))
print('TV_SCREEN_ROWS',len(rows),flush=True)
