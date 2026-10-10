import bpy,json
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'backup_antes_acabamentos_camera/mansao_encaixada.blend'))
rows=[]
for ob in bpy.data.objects:
 if ob.type!='MESH':continue
 if not any(c.name.startswith(('04_','05_')) for c in ob.users_collection):continue
 ps=[ob.matrix_world@v.co for v in ob.data.vertices]
 rows.append(dict(name=ob.name,lo=[min(p[i] for p in ps) for i in range(3)],hi=[max(p[i] for p in ps) for i in range(3)]))
(W/'work/scene_finishing_bounds.json').write_text(json.dumps(rows,indent=2))
for r in rows:
 if any(k in r['name'].lower() for k in ('piso','laje','patamar','chegada','fechamento')):print(r,flush=True)
