"""Deterministic arm repair: fixed reachable targets, exact visible weapon mount."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
root=Path(__file__).resolve().parent.parent
profiles={}
for filename,idle_name,recoil_name,prone in [('ajoelhado_refinado.blend','ESTUDO_ajoelhar_mira','ESTUDO_recuo',False),('deitado_tiro.blend','DEITADO_mira','DEITADO_disparo',True)]:
 bpy.ops.wm.open_mainfile(filepath=str(root/filename));rig=bpy.data.objects['GTA_Personagem_Rig'];sc=bpy.context.scene
 rig.animation_data.action=bpy.data.actions[idle_name];sc.frame_set(1);bpy.context.view_layer.update()
 baseline={b.name:(b.location.copy(),b.rotation_quaternion.copy()) for b in rig.pose.bones}
 handq={s:rig.pose.bones[f'SKEL_{s}_Hand'].matrix.to_quaternion().copy() for s in ('L','R')}
 scope={'rig':rig,'bpy':bpy,'Vector':Vector,'Matrix':Matrix,'math':math};src=(root/'work/pose.py').read_text()
 exec(src[src.index('def orient('):src.index('# Legs:')],scope)
 # Centralize the handguard instead of reaching diagonally across the whole body.
 targets={'R':Vector((-.19,-.60,.26) if prone else (-.22,-.36,.93)),
          'L':Vector((-.13,-.79,.275) if prone else (-.16,-.55,.935))}
 poles={'R':Vector((-.34,-.40,.08) if prone else (-.38,-.12,.76)),
        'L':Vector((.24,-.47,-.08) if prone else (.24,-.26,.76))}
 # Use fixed source action snapshots; rerunning does not accumulate translations.
 for name,recoil in [(idle_name,False),(recoil_name,True)]:
  rig.animation_data.action=None
  for f in range(1,31):
   for b in rig.pose.bones:b.location,b.rotation_quaternion=baseline[b.name]
   bpy.context.view_layer.update()
   if prone:
    # Let the shoulder girdle turn with the reaching arm. Keeping the clavicle
    # in its T-pose while rotating the humerus alone pinched the jacket seam.
    for side,sign in [('L',1),('R',-1)]:
     clav=rig.pose.bones[f'SKEL_{side}_Clavicle'];clav.rotation_quaternion=(1,0,0,0);bpy.context.view_layer.update()
     upper=rig.pose.bones[f'SKEL_{side}_UpperArm']
     old=(upper.head-clav.head).normalized();desired=Vector((sign*.16,-.045,-.015)).normalized()
     clav.matrix=Matrix.Translation(clav.head)@(old.rotation_difference(desired)@clav.matrix.to_quaternion()).to_matrix().to_4x4();bpy.context.view_layer.update()
   back=(.009*math.sin(math.pi*(f-1)/9) if recoil and f<=10 else 0)
   for side in ('R','L'):
    # Restore rest arm roll before solving; do not accumulate arbitrary axial twists.
    for part in ('UpperArm','Forearm'):
     b=rig.pose.bones[f'SKEL_{side}_{part}'];b.rotation_quaternion=(1,0,0,0)
    bpy.context.view_layer.update()
    scope['chain'](f'SKEL_{side}_UpperArm',f'SKEL_{side}_Forearm',f'SKEL_{side}_Hand',targets[side]+Vector((0,back,0)),poles[side])
    hand=rig.pose.bones[f'SKEL_{side}_Hand'];hand.matrix=Matrix.Translation(hand.head)@handq[side].to_matrix().to_4x4();bpy.context.view_layer.update()
    # Twist helpers must follow the revised forearm, with no stretched translation.
    for namepart in ('RB_'+side+'_ArmRoll','RB_'+side+'_ForeArmRoll','MH_'+side+'_Elbow'):
     if namepart in rig.pose.bones:rig.pose.bones[namepart].location=(0,0,0)
   for b in rig.pose.bones:
    b.keyframe_insert(data_path='location',frame=f,group=b.name);b.keyframe_insert(data_path='rotation_quaternion',frame=f,group=b.name)
  old=bpy.data.actions.get(name)
  if old:old.name=name+'_before_v4'
  rig.animation_data.action.name=name;rig.animation_data.action.use_fake_user=True
 rig.animation_data.action=bpy.data.actions[idle_name];sc.frame_set(1);bpy.context.view_layer.update()
 gun=bpy.data.objects['w_ar_carbinerifle'];gun.constraints.clear()
 forward=Vector((0,-1,0));gun.rotation_quaternion=Matrix((forward,Vector((1,0,0)),Vector((0,0,1)))).transposed().to_quaternion()
 gun.location=(rig.matrix_world@rig.pose.bones['SKEL_R_Hand'].head)-(gun.rotation_quaternion@gun.data.bones['Gun_GripR'].head_local)
 bpy.context.view_layer.update()
 handworld=rig.matrix_world@rig.pose.bones['SKEL_R_Hand'].matrix
 local=handworld.inverted()@gun.matrix_world
 profiles['deitadotiro' if prone else 'ajoelharteste']={'position':list(local.translation),'rotation':[math.degrees(v) for v in local.to_euler('ZXY')],'basis':[list(local.to_3x3().col[i]) for i in range(3)]}
 c=gun.constraints.new('CHILD_OF');c.target=rig;c.subtarget='SKEL_R_Hand';c.inverse_matrix=handworld.inverted()
 sc.render.resolution_x=1100;sc.render.resolution_y=750;sc.cycles.samples=16
 cam=sc.camera;cam.location=(2.4,-2.7,1.25 if prone else 1.8);focus=Vector((0,-.25,.28 if prone else .68));cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.1 if prone else 2.0
 sc.render.filepath=str(root/('reparo_deitado_v4.png' if prone else 'reparo_ajoelhado_v4.png'))
 bpy.ops.wm.save_as_mainfile(filepath=str(root/filename));bpy.ops.render.render(write_still=True)
 for side in ('L','R'):
  p=[rig.matrix_world@rig.pose.bones[f'SKEL_{side}_{b}'].head for b in ('UpperArm','Forearm','Hand')]
  reach=(p[2]-p[0]).length/((p[1]-p[0]).length+(p[2]-p[1]).length)
  assert reach<.95,('Arm too straight',side,reach)
  print('ARM_REACH',filename,side,reach,'ELBOW',tuple(p[1]))
(root/'exports/weapon_mounts.json').write_text(json.dumps(profiles,indent=2))
print('MOUNTS',profiles)
