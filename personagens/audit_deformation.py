import bpy,sys,addon_utils,json
from pathlib import Path
from mathutils import Vector
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
root=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(root.parent/'animacoes/deitado_tiro.blend'))
source=bpy.data.objects['GTA_Personagem_Rig'];source.animation_data.action=bpy.data.actions['DEITADO_mira'];bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
pose={b.name:b.matrix_basis.copy() for b in source.pose.bones}
bpy.ops.wm.open_mainfile(filepath=str(root/'cartelking.blend'))
visible=[bpy.data.objects[n] for n in ['SKEL_ROOT','SKEL_ROOT.003','SKEL_ROOT.005']]
def test(label):
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();bad=[]
 for o in visible:
  ev=o.evaluated_get(dg);m=ev.to_mesh()
  for e in o.data.edges:
   a,b=e.vertices;d0=(o.data.vertices[a].co-o.data.vertices[b].co).length;d1=(m.vertices[a].co-m.vertices[b].co).length
   if d1>max(.15,d0*3):
    detail=[]
    for i in [a,b]:
     v=o.data.vertices[i];detail.append({'p':list(v.co),'w':[(o.vertex_groups[g.group].name,round(g.weight,3)) for g in v.groups]})
    bad.append((round(d1,3),o.name,detail))
  ev.to_mesh_clear()
 bad.sort(reverse=True,key=lambda x:x[0]);print('AUDIT',label,'STRETCHED',len(bad),'WORST',bad[:6])
 return len(bad)
for r in bpy.data.objects:
 if r.type=='ARMATURE':
  for b in r.pose.bones:
   if b.name in pose:b.matrix_basis=pose[b.name]
bpy.context.scene.frame_set(1);test('prone')
