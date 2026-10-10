import bpy
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(root/'preparacao_fivem_stage18/warehouse_stage18_preparacao.blend'))
for o in bpy.data.collections['EXPORT_Props'].objects:
 n=o.name.lower()
 if ('BENCH' in o.name or 'BOX' in o.name or 'BIN' in o.name) and o.location.y>2.5:
  bb=[o.matrix_world@Vector(v) for v in o.bound_box]
  lo=[min(v[j] for v in bb) for j in range(3)];hi=[max(v[j] for v in bb) for j in range(3)]
  print(o.name,'min',*[round(x,2) for x in lo],'max',*[round(x,2) for x in hi],flush=True)

