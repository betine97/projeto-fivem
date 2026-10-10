"""Refine hand contacts and author staged prone -> knee -> standing exit."""
import bpy,math
from pathlib import Path
from mathutils import Matrix,Vector
root=Path(__file__).resolve().parent.parent

def refine(file,idle_name,recoil_name):
 bpy.ops.wm.open_mainfile(filepath=str(root/file))
 rig=bpy.data.objects['GTA_Personagem_Rig']; gun=bpy.data.objects['w_ar_carbinerifle']
 rig.animation_data.action=bpy.data.actions[idle_name];bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
 # Keep the full wrist orientation: translating an attached weapon alone leaves
 # its trigger grip disconnected. Move both arm chains together instead.
 scope={'rig':rig,'bpy':bpy,'Vector':Vector,'Matrix':Matrix,'math':math}
 src=(root/'work/pose.py').read_text(encoding='utf8')
 exec(src[src.index('def orient('):src.index('# Legs:')],scope)
 chain=scope['chain']
 shift=Vector((-.035,-.065,.012))
 for actionname in (idle_name,recoil_name):
  action=bpy.data.actions[actionname];rig.animation_data.action=action
  samples=[]
  for f in range(1,31):
   bpy.context.scene.frame_set(f);bpy.context.view_layer.update()
   samples.append({side:(rig.matrix_world@rig.pose.bones[f'SKEL_{side}_Hand'].head,
                rig.pose.bones[f'SKEL_{side}_Hand'].matrix.to_quaternion().copy(),
                rig.matrix_world@rig.pose.bones[f'SKEL_{side}_Forearm'].head) for side in ('L','R')})
  for f,sample in enumerate(samples,1):
   bpy.context.scene.frame_set(f)
   for side,(target,q,elbow) in sample.items():
    chain(f'SKEL_{side}_UpperArm',f'SKEL_{side}_Forearm',f'SKEL_{side}_Hand',target+shift,elbow+shift)
    hand=rig.pose.bones[f'SKEL_{side}_Hand'];hand.matrix=Matrix.Translation(hand.head)@q.to_matrix().to_4x4()
    bpy.context.view_layer.update()
   # Close support fingers around the handguard, using their actual joint axes.
   for finger in range(1,5):
    for segment,direction in [(0,Vector((-.12,-.25,1))),(1,Vector((1,-.15,.35))),(2,Vector((1,0,-.45)))]:
     b=rig.pose.bones[f'SKEL_L_Finger{finger}{segment}'];q=b.matrix.to_quaternion()
     child=rig.pose.bones.get(f'SKEL_L_Finger{finger}{segment+1}')
     axis=(child.head-b.head).normalized() if child else q@Vector((1,0,0))
     b.matrix=Matrix.Translation(b.head)@(axis.rotation_difference(direction.normalized())@q).to_matrix().to_4x4()
     bpy.context.view_layer.update()
   for b in rig.pose.bones:
    if any(k in b.name for k in ('UpperArm','Forearm','Hand','Finger')):
     b.keyframe_insert(data_path='location',frame=f,group=b.name)
     b.keyframe_insert(data_path='rotation_quaternion',frame=f,group=b.name)
 rig.animation_data.action=bpy.data.actions[idle_name];bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
 # Rebuild the preview attachment against the revised hand.
 gun.constraints.clear();gun.location=(rig.matrix_world@rig.pose.bones['SKEL_R_Hand'].head)-(gun.rotation_quaternion@gun.data.bones['Gun_GripR'].head_local)
 bpy.context.view_layer.update()
 c=gun.constraints.new('CHILD_OF');c.target=rig;c.subtarget='SKEL_R_Hand';c.inverse_matrix=(rig.matrix_world@rig.pose.bones['SKEL_R_Hand'].matrix).inverted()
 pose={b.name:(b.location.copy(),b.rotation_quaternion.copy()) for b in rig.pose.bones}
 sc=bpy.context.scene;sc.render.resolution_x=1000;sc.render.resolution_y=700;sc.cycles.samples=16
 sc.render.filepath=str(root/('revisao_deitado.png' if 'deitado' in file else 'revisao_ajoelhado.png'))
 bpy.ops.wm.save_as_mainfile(filepath=str(root/file));bpy.ops.render.render(write_still=True)
 return pose

knee=refine('ajoelhado_refinado.blend','ESTUDO_ajoelhar_mira','ESTUDO_recuo')
prone=refine('deitado_tiro.blend','DEITADO_mira','DEITADO_disparo')
rig=bpy.data.objects['GTA_Personagem_Rig']
# Standing lower body uses the original rest transforms; retain rifle grip above waist.
standing={n:(loc.copy(),q.copy()) for n,(loc,q) in knee.items()}
for b in rig.pose.bones:
 if b.name=='SKEL_ROOT' or any(t in b.name for t in ('Thigh','Calf','Foot','Toe','Pelvis')):
  standing[b.name]=(Vector((0,0,0)),Matrix.Identity(4).to_quaternion())
rig.animation_data.action=None
for f in range(1,92):
 if f<=49: a,b,t=prone,knee,(f-1)/48
 elif f<=61: a,b,t=knee,knee,0
 else: a,b,t=knee,standing,(f-61)/30
 t=t*t*(3-2*t)
 for pb in rig.pose.bones:
  pb.location=a[pb.name][0].lerp(b[pb.name][0],t)
  pb.rotation_quaternion=a[pb.name][1].slerp(b[pb.name][1],t)
  pb.keyframe_insert(data_path='location',frame=f,group=pb.name)
  pb.keyframe_insert(data_path='rotation_quaternion',frame=f,group=pb.name)
exit_action=rig.animation_data.action;exit_action.name='DEITADO_levantar';exit_action.use_fake_user=True
sc=bpy.context.scene;sc.frame_end=91;sc.timeline_markers.clear()
for label,f in [('Deitado',1),('Ajoelhado',49),('Levantar',61),('Em pe',91)]:sc.timeline_markers.new(label,frame=f)
sc.frame_set(49);bpy.context.view_layer.update()
cam=sc.camera;cam.data.ortho_scale=2.8
cam.location=(2.8,-3,1.8);cam.rotation_euler=(Vector((0,-.08,.6))-cam.location).to_track_quat('-Z','Y').to_euler()
sc.render.filepath=str(root/'revisao_transicao.png');bpy.ops.render.render(write_still=True)
sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(root/'deitado_tiro.blend'))
print('REFINEMENT: grips and 3 second exit saved')
