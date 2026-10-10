import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parent; W=P.parent
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_piano_tapetes.blend'))
for c in bpy.data.collections:
 if c.name.startswith(('01_','02_','04_','22_COZINHA')):
  for o in c.objects:
   if o.type!='MESH':continue
   ps=[o.matrix_world@v.co for v in o.data.vertices]
   lo=[min(p[i] for p in ps) for i in range(3)];hi=[max(p[i] for p in ps) for i in range(3)]
   if hi[0]>7 or 'Cozinha' in o.name:print('SCENE_OBJECT',c.name,o.name,[round(v,3) for v in lo],[round(v,3) for v in hi],flush=True)
