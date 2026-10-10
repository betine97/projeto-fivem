import bpy
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'mansao_acesso_reparado.blend'))
for obj in bpy.context.scene.objects:
 if obj.type!='MESH' or obj.hide_render or not obj.visible_get():continue
 me=obj.data;mx=obj.matrix_world;hits=[]
 for t in me.loop_triangles:
  ps=[mx@me.vertices[i].co for i in t.vertices]
  c=sum(ps,Vector())/3
  if 3.28<c.x<6.27 and 11.5<c.y<15.5 and -.74<c.z<1.65:hits.extend(ps)
 if hits:
  print('RESIDUE',obj.name,'root',obj.parent.name if obj.parent else '-', 'bbox',[[round(min(p[k] for p in hits),3) for k in range(3)],[round(max(p[k] for p in hits),3) for k in range(3)]],flush=True)
