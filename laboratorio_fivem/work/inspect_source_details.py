import bpy
from mathutils import Vector
from pathlib import Path
root=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(root/'preparacao_fivem_stage18/warehouse_stage18_preparacao.blend'))
for cname in ('EXPORT_Estrutura','EXPORT_Props','EXPORT_Vegetacao'):
 c=bpy.data.collections.get(cname)
 print('COLLECTION',cname,'objects',len(c.objects) if c else None,flush=True)
 if not c:continue
 for o in c.objects:
  n=o.name.upper()
  if cname=='EXPORT_Vegetacao' or any(q in n for q in ('FAN','VENT','DUCT','FLOOR','DRAIN','PLANT','STEM','TRUNK','BRANCH','TECH_','DOOR','RACK','LED_','LIGHT_')):
   bb=[o.matrix_world@Vector(v) for v in o.bound_box]
   lo=[round(min(v[j] for v in bb),3) for j in range(3)];hi=[round(max(v[j] for v in bb),3) for j in range(3)]
   mats=[m.name for m in o.data.materials if m] if hasattr(o.data,'materials') else []
   print(o.name,'lo',lo,'hi',hi,'mats',mats,flush=True)
