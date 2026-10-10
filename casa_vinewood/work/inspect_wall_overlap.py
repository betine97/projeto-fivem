import bpy,json
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_fivem_preparada.blend'))
s=bpy.context.scene;dg=bpy.context.evaluated_depsgraph_get();origin=Vector((-.3,-5.2,3.8))
for q in [(-9.056,-9,2.46),(-9.056,-9,2.7),(-9.056,-9,2.2),(-7,-12.984,2.46)]:
 target=Vector(q);hit,co,n,index,ob,matrix=s.ray_cast(dg,origin,(target-origin).normalized())
 print('WALL_RAY',q,hit,ob.name if ob else None,co[:],flush=True)
print('GROUND_UPPER_OVERLAP',json.loads((W/'espessuras_estruturais.json').read_text())['solids'][0],flush=True)
