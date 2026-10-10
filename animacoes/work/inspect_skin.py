import bpy
from pathlib import Path
bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).resolve().parent.parent/'deitado_tiro.blend'))
r=bpy.data.objects['GTA_Personagem_Rig'];r.animation_data.action=bpy.data.actions['DEITADO_mira'];bpy.context.scene.frame_set(1)
for b in r.pose.bones:print('BONE',b.name,b.parent.name if b.parent else '',tuple(round(v,3) for v in b.location))
for o in bpy.data.objects:
 if o.type=='MESH' and not o.hide_render and any('UpperArm' in g.name for g in o.vertex_groups):
  print('SKIN',o.name,'WEIGHTS',[g.name for g in o.vertex_groups]);print('MOD',[(m.name,m.type,m.object.name if m.type=='ARMATURE' and m.object else '') for m in o.modifiers])
