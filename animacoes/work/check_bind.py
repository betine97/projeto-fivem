import bpy
from pathlib import Path
root=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(root/'deitado_tiro.blend'))
r=bpy.data.objects['GTA_Personagem_Rig']
for o in bpy.data.objects:
 if o.type=='MESH' and not o.hide_render and 'SKEL_L_UpperArm' in o.vertex_groups:
  print('PARENT',o.name,o.parent.name)
  other=o.parent
  for n in ['SKEL_L_UpperArm','SKEL_L_Forearm','RB_L_ArmRoll','SKEL_L_Clavicle','SKEL_Spine3']:
   if other.type=='ARMATURE':
    a,b=r.data.bones[n],other.data.bones[n];print('REST_DIFF',n,max(abs(a.matrix_local[i][j]-b.matrix_local[i][j]) for i in range(4) for j in range(4)))
  print('MATRIX',list(map(list,o.matrix_world)))
