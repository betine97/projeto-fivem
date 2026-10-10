import bpy
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'mansao_bar_tapete_150.blend'))
s=bpy.context.scene;camera=s.camera;frame=camera.data.view_frame(scene=s)
x=min(v.x for v in frame)+(max(v.x for v in frame)-min(v.x for v in frame))*1280/1440
y=min(v.y for v in frame)+(max(v.y for v in frame)-min(v.y for v in frame))*(1-779/940)
d=camera.matrix_world.to_3x3()@Vector((x,y,frame[0].z)).normalized()
hit,loc,n,index,obj,matrix=s.ray_cast(bpy.context.evaluated_depsgraph_get(),camera.location,d)
print('PREVIEW_RAY',hit,obj.name if obj else None,tuple(loc),[c.name for c in obj.users_collection] if obj else None,flush=True)
if hit:
 print('PREVIEW_MATERIAL',index,[(i,m.name if m else None) for i,m in enumerate(obj.data.materials)],flush=True)
 print('HIT_MATERIAL_INDEX',obj.data.polygons[index].material_index,flush=True)
 for o in s.objects:
  if o.type=='MESH' and o.name!=obj.name and not o.hide_render and all(not c.hide_render for c in o.users_collection):
   ps=[o.matrix_world@Vector(v) for v in o.bound_box]
   if min(p.x for p in ps)<loc.x<max(p.x for p in ps) and min(p.y for p in ps)<loc.y<max(p.y for p in ps):
    print('ABOVE_HIT',o.name,[c.name for c in o.users_collection],[(min(p[i] for p in ps),max(p[i] for p in ps)) for i in range(3)],flush=True)
