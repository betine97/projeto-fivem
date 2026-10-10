import bpy,numpy as np
from pathlib import Path
D=Path(__file__).resolve().parents[1]/'source_assets/vaso_planta'
for name in ('leaves','pot'):
 ims=[bpy.data.images.load(str(D/(name+'.png'))),bpy.data.images.load(str(D/(name+'_diffuse.dds')))]
 data=[np.array(im.pixels[:]).reshape(im.size[1],im.size[0],4) for im in ims]
 for u,v in [( .14,.80),(.14,.22),(.5,.5),(.5,.65)]:
  print(name,u,v,[x[round(v*(x.shape[0]-1)),round(u*(x.shape[1]-1)),:3].tolist() for x in data],flush=True)
