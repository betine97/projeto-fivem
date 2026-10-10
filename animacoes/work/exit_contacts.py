"""Author the exit with foot targets instead of interpolating bent leg rotations."""
import bpy,math
from pathlib import Path
from mathutils import Matrix,Vector
root=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(root/'deitado_tiro.blend'))
rig=bpy.data.objects['GTA_Personagem_Rig'];sc=bpy.context.scene
with bpy.data.libraries.load(str(root/'ajoelhado_refinado.blend'),link=False) as (src,dst):
 dst.actions=['ESTUDO_ajoelhar_mira']
knee_action=dst.actions[0]
def snapshot(action):
 rig.animation_data.action=action;sc.frame_set(1);bpy.context.view_layer.update()
 return ({b.name:(b.location.copy(),b.rotation_quaternion.copy()) for b in rig.pose.bones},
         {s:((rig.matrix_world@rig.pose.bones[f'SKEL_{s}_Foot'].head).copy(),rig.pose.bones[f'SKEL_{s}_Foot'].matrix.to_quaternion().copy(),
             (rig.matrix_world@rig.pose.bones[f'SKEL_{s}_Calf'].head).copy()) for s in ('L','R')})
prone,pfeet=snapshot(bpy.data.actions['DEITADO_mira']);knee,kfeet=snapshot(knee_action)
standing={n:(v.copy(),q.copy()) for n,(v,q) in knee.items()}
for b in rig.pose.bones:
 if b.name=='SKEL_ROOT' or any(t in b.name for t in ('Thigh','Calf','Foot','Toe','Pelvis')):
  standing[b.name]=(Vector((0,0,0)),Matrix.Identity(4).to_quaternion())
for pb in rig.pose.bones:pb.location,pb.rotation_quaternion=standing[pb.name]
rig.animation_data.action=None;bpy.context.view_layer.update()
sfeet={s:((rig.matrix_world@rig.pose.bones[f'SKEL_{s}_Foot'].head).copy(),rig.pose.bones[f'SKEL_{s}_Foot'].matrix.to_quaternion().copy(),
         (rig.matrix_world@rig.pose.bones[f'SKEL_{s}_Calf'].head).copy()) for s in ('L','R')}
scope={'rig':rig,'bpy':bpy,'Vector':Vector,'Matrix':Matrix,'math':math}
text=(root/'work/pose.py').read_text();exec(text[text.index('def orient('):text.index('# Legs:')],scope)
for f in range(1,92):
 if f<=49:a,b,af,bf,t=prone,knee,pfeet,kfeet,(f-1)/48
 elif f<=61:a,b,af,bf,t=knee,knee,kfeet,kfeet,0
 else:a,b,af,bf,t=knee,standing,kfeet,sfeet,(f-61)/30
 t=t*t*(3-2*t)
 for pb in rig.pose.bones:
  pb.location=a[pb.name][0].lerp(b[pb.name][0],t);pb.rotation_quaternion=a[pb.name][1].slerp(b[pb.name][1],t)
 bpy.context.view_layer.update()
 if f not in (1,49,61,91):
  for side in ('L','R'):
   target=af[side][0].lerp(bf[side][0],t)
   pole=af[side][2].lerp(bf[side][2],t)
   scope['chain'](f'SKEL_{side}_Thigh',f'SKEL_{side}_Calf',f'SKEL_{side}_Foot',target,pole)
   foot=rig.pose.bones[f'SKEL_{side}_Foot'];q=af[side][1].slerp(bf[side][1],t)
   foot.matrix=Matrix.Translation(foot.head)@q.to_matrix().to_4x4();bpy.context.view_layer.update()
 for pb in rig.pose.bones:
  pb.keyframe_insert(data_path='location',frame=f,group=pb.name)
  pb.keyframe_insert(data_path='rotation_quaternion',frame=f,group=pb.name)
old=bpy.data.actions.get('DEITADO_levantar')
if old:old.name='DEITADO_levantar_old'
rig.animation_data.action.name='DEITADO_levantar';rig.animation_data.action.use_fake_user=True
sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(root/'deitado_tiro.blend'))
print('EXIT CONTACTS saved')
