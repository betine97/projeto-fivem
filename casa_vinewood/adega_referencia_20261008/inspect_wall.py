import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent
bpy.ops.wm.open_mainfile(filepath=str(W/'bar_referencia_20261008/mansao_bar_tapete_150.blend'))
for c in bpy.data.collections:
 if c.name.startswith(('01_','02_','03_','22_')):
  for o in c.objects:
   if o.type!='MESH':continue
   ps=[o.matrix_world@v.co for v in o.data.vertices]
   lo=[min(p[i] for p in ps) for i in range(3)];hi=[max(p[i] for p in ps) for i in range(3)]
   print('FIT_OBJECT',c.name,o.name,[round(v,3) for v in lo],[round(v,3) for v in hi],flush=True)
