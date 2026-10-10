import bpy,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_encaixada.blend'))
rows=[]
for c in bpy.data.collections:
 if c.name.startswith(('01_','02_','03_','04_','05_','06_','10_')):
  for o in c.objects:
   if o.type!='MESH':continue
   pts=[o.matrix_world@v.co for v in o.data.vertices]
   lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
   rows.append(dict(name=o.name,collection=c.name,lo=lo,hi=hi))
(W/'work/decor_scene_bounds.json').write_text(json.dumps(rows,indent=2))
print('DECOR_PROBE',len(rows),flush=True)
