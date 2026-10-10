"""Keep the evaluated foot meshes above the ground throughout the exit."""
import bpy
from pathlib import Path
root=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(root/'deitado_tiro.blend'))
rig=bpy.data.objects['GTA_Personagem_Rig'];sc=bpy.context.scene
rig.animation_data.action=bpy.data.actions['DEITADO_levantar']
meshes=[o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render
        and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)]
assert meshes
samples=[]
for f in range(1,92):
 sc.frame_set(f);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
 lowest=10
 for obj in meshes:
  evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh()
  lowest=min(lowest,min((evaluated.matrix_world@v.co).z for v in mesh.vertices))
  evaluated.to_mesh_clear()
 samples.append((rig.pose.bones['SKEL_ROOT'].matrix.copy(),lowest))
baseline=min(samples[0][1],samples[-1][1],0)
for f,(matrix,lowest) in enumerate(samples,1):
 sc.frame_set(f)
 matrix.translation.z+=max(0,baseline-lowest)
 rig.pose.bones['SKEL_ROOT'].matrix=matrix
 rig.pose.bones['SKEL_ROOT'].keyframe_insert(data_path='location',frame=f)
sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(root/'deitado_tiro.blend'))
print('GROUND correction',max(baseline-lowest for _,lowest in samples))
