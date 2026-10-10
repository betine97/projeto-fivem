"""Editable prone aim/recoil study on the user's local GTA skeleton."""
import bpy, math
from pathlib import Path
from mathutils import Matrix, Quaternion, Vector
root=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(root/'ajoelhado_refinado.blend'))
rig=bpy.data.objects['GTA_Personagem_Rig']
rig.animation_data.action=bpy.data.actions['ESTUDO_ajoelhar_mira']
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()
saved={n:rig.pose.bones[n].matrix.to_quaternion().copy() for n in ['SKEL_Head','SKEL_L_Hand','SKEL_R_Hand']}
fingers={b.name:b.rotation_quaternion.copy() for b in rig.pose.bones if 'Finger' in b.name}
attachments={b.name:b.matrix_basis.copy() for b in rig.pose.bones if b.name.startswith(('PH_','IK_')) and 'Hand' in b.name}
rig.animation_data_clear()
for b in rig.pose.bones:
 b.matrix_basis=Matrix.Identity(4); b.rotation_mode='QUATERNION'
rig.location=(0,0,.98)
bpy.context.view_layer.update()
# Use the same exact limb solver as the kneeling study, without running its scene generation.
source=(root/'work/pose.py').read_text(encoding='utf8')
exec(source[source.index('def orient('):source.index('# Legs:')])
rootbone=rig.pose.bones['SKEL_ROOT']
rootbone.matrix=Matrix.Translation(Vector((0,0,-.83)))@Matrix.Rotation(math.radians(80),4,'X')@rootbone.matrix.to_quaternion().to_matrix().to_4x4()
bpy.context.view_layer.update()
# Raise the chest gently while the pelvis and legs remain low.
spine=rig.pose.bones['SKEL_Spine1']
spine.matrix=Matrix.Translation(spine.head)@Matrix.Rotation(math.radians(-8),4,'X')@spine.matrix.to_quaternion().to_matrix().to_4x4()
bpy.context.view_layer.update()
neck=rig.pose.bones['SKEL_Neck_1']; head=rig.pose.bones['SKEL_Head']
neckq=(head.head-neck.head).normalized().rotation_difference(Vector((0,-.70,.71)).normalized())@neck.matrix.to_quaternion()
neck.matrix=Matrix.Translation(neck.head)@neckq.to_matrix().to_4x4()
bpy.context.view_layer.update()
head.matrix=Matrix.Translation(head.head)@Matrix.Rotation(math.radians(-12),4,'X')@saved['SKEL_Head'].to_matrix().to_4x4()
bpy.context.view_layer.update()
# Both legs extend backwards; ankle spread prevents intersecting trousers.
chain('SKEL_L_Thigh','SKEL_L_Calf','SKEL_L_Foot',(.24,.83,.105),(.20,.43,.045))
chain('SKEL_R_Thigh','SKEL_R_Calf','SKEL_R_Foot',(-.24,.83,.105),(-.20,.43,.045))
orient('SKEL_L_Foot',(.30,.94,-.15)); orient('SKEL_R_Foot',(-.30,.94,-.15))
# Two hand contacts and low elbow poles, keeping the rifle clear of the ground.
for side,target,pole in [('R',(-.22,-.57,.25),(-.36,-.42,.035)),('L',(-.19,-.79,.265),(.20,-.40,-.35))]:
 chain(f'SKEL_{side}_UpperArm',f'SKEL_{side}_Forearm',f'SKEL_{side}_Hand',target,pole)
 hand=rig.pose.bones[f'SKEL_{side}_Hand']
 hand.matrix=Matrix.Translation(hand.head)@saved[hand.name].to_matrix().to_4x4()
 bpy.context.view_layer.update()
for name,q in fingers.items():rig.pose.bones[name].rotation_quaternion=q
for name,matrix in attachments.items():rig.pose.bones[name].matrix_basis=matrix
bpy.context.view_layer.update()
for b in rig.pose.bones:
 for frame in (1,30):
  b.keyframe_insert(data_path='location',frame=frame,group=b.name)
  b.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=b.name)
idle=rig.animation_data.action;idle.name='DEITADO_mira';idle.use_fake_user=True
recoil=idle.copy();recoil.name='DEITADO_disparo';recoil.use_fake_user=True
rig.animation_data.action=recoil
# Short recoil through shoulders and wrists; pelvis, legs and elbow anchors stay fixed.
base={n:rig.pose.bones[n].matrix.copy() for n in ['SKEL_L_Hand','SKEL_R_Hand','SKEL_Head']}
for frame,back in [(1,0),(3,.018),(6,.007),(10,0),(30,0)]:
 for side,pole in [('R',(-.36,-.42,.035)),('L',(.20,-.40,-.35))]:
  n=f'SKEL_{side}_Hand';target=rig.matrix_world@base[n].translation+Vector((0,back,back*.16))
  chain(f'SKEL_{side}_UpperArm',f'SKEL_{side}_Forearm',n,target,pole)
  hand=rig.pose.bones[n];hand.matrix=Matrix.Translation(hand.head)@base[n].to_quaternion().to_matrix().to_4x4()
  bpy.context.view_layer.update()
 for b in rig.pose.bones:
  b.keyframe_insert(data_path='location',frame=frame,group=b.name)
  b.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=b.name)
rig.animation_data.action=idle;bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
gun=bpy.data.objects['w_ar_carbinerifle'];gun.constraints.clear()
forward=Vector((0,-1,0))
gun.rotation_quaternion=Matrix((forward,Vector((0,0,1)).cross(forward),Vector((0,0,1)))).transposed().to_quaternion()
gun.location=(rig.matrix_world@rig.pose.bones['SKEL_R_Hand'].head)-(gun.rotation_quaternion@gun.data.bones['Gun_GripR'].head_local)
bpy.context.view_layer.update()
follow=gun.constraints.new('CHILD_OF');follow.target=rig;follow.subtarget='SKEL_R_Hand';follow.inverse_matrix=(rig.matrix_world@rig.pose.bones['SKEL_R_Hand'].matrix).inverted()
rig['status']='ESTUDO DEITADO: mira e disparo; ainda nao instalado no FiveM'
sc=bpy.context.scene;sc.frame_start=1;sc.frame_end=30
sc.timeline_markers.clear()
for label,frame in [('Inicio / mira',1),('Recuo maximo',3),('Retorno',10)]:sc.timeline_markers.new(label,frame=frame)
cam=sc.camera;cam.location=(2.8,-2.9,1.7);cam.rotation_euler=(Vector((0,-.08,.30))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.75
sc.render.resolution_x=1200;sc.render.resolution_y=800;sc.cycles.samples=24
note=bpy.data.texts.get('LEIA-ME');note.clear();note.write('Tiro deitado: estudo sobre o esqueleto GTA original.\nDEITADO_mira: postura sustentada. DEITADO_disparo: recuo em 10 frames, seguido de repouso.\nA arma acompanha a mao direita. Referencias incorporadas.\nAinda nao instalado no servidor; avaliar apoio dos cotovelos e contato das maos.\n')
bpy.ops.wm.save_as_mainfile(filepath=str(root/'deitado_tiro.blend'))
sc.render.filepath=str(root/'previa_deitado.png');bpy.ops.render.render(write_still=True)
cam.location=(3,-.02,.85);cam.rotation_euler=(Vector((0,-.06,.25))-cam.location).to_track_quat('-Z','Y').to_euler()
sc.render.filepath=str(root/'previa_deitado_lateral.png');bpy.ops.render.render(write_still=True)
print('PRONE_JOINTS',[(n,tuple(rig.matrix_world@rig.pose.bones[n].head)) for n in ['SKEL_Pelvis','SKEL_Head','SKEL_L_Forearm','SKEL_R_Forearm','SKEL_L_Foot','SKEL_R_Foot']])
