"""Standing turret operator, authored on the same GTA rig as combat poses."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector,Matrix
root=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(root/'work'),r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
from export_orientation import forward_action
from Sollumz.ycd.ycdimport import create_clip_dictionary_template,create_anim_obj
from Sollumz.ycd.ycdexport import export_ycd
from Sollumz.sollumz_properties import SollumType
bpy.ops.wm.open_mainfile(filepath=str(root/'ajoelhado_refinado.blend'))
rig=bpy.data.objects['GTA_Personagem_Rig']
rig.animation_data.action=bpy.data.actions['ESTUDO_ajoelhar_mira'];bpy.context.scene.frame_set(1)
handq={s:rig.pose.bones[f'SKEL_{s}_Hand'].matrix.to_quaternion().copy() for s in ['L','R']}
fingers={b.name:b.matrix_basis.copy() for b in rig.pose.bones if 'Finger' in b.name}
rig.animation_data_clear();rig.location=(0,0,.98)
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4);b.rotation_mode='QUATERNION'
bpy.context.view_layer.update()
source=(root/'work/pose.py').read_text(encoding='utf8')
exec(source[source.index('def orient('):source.index('# Legs:')])
for s,x in [('L',.17),('R',-.17)]:
 chain(f'SKEL_{s}_Thigh',f'SKEL_{s}_Calf',f'SKEL_{s}_Foot',(x,0,.085),(x,-.35,.48))
 orient(f'SKEL_{s}_Foot',(0,-1,-.12))
 chain(f'SKEL_{s}_UpperArm',f'SKEL_{s}_Forearm',f'SKEL_{s}_Hand',(x,-.38,1.30),(x*2.4,-.17,1.05))
 b=rig.pose.bones[f'SKEL_{s}_Hand'];b.matrix=Matrix.Translation(b.head)@handq[s].to_matrix().to_4x4()
 bpy.context.view_layer.update()
for n,m in fingers.items():rig.pose.bones[n].matrix_basis=m
for b in rig.pose.bones:
 for frame in [1,30]:
  b.keyframe_insert(data_path='location',frame=frame,group=b.name)
  b.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=b.name)
action=rig.animation_data.action;action.name='SERTAO_operador';action.use_fake_user=True
contacts={s:list(rig.matrix_world@rig.pose.bones[f'SKEL_{s}_Hand'].head) for s in ['L','R']}
for s,x in [('L',.17),('R',-.17)]:assert (Vector(contacts[s])-Vector((x,-.38,1.30))).length<.015,contacts
d,c,a=create_clip_dictionary_template('cidade_sertao_torre')
anim=create_anim_obj(SollumType.ANIMATION);anim.name='operador_anim';anim.parent=a
anim.animation_properties.hash='operador_anim';anim.animation_properties.target_id=rig.data
anim.animation_properties.action=forward_action(rig,action)
clip=create_anim_obj(SollumType.CLIP);clip.parent=c;clip.name='operador'
clip.clip_properties.hash='operador';clip.clip_properties.name='operador';clip.clip_properties.duration=29/30
item=clip.clip_properties.animations.add();item.animation=anim;item.start_frame=1;item.end_frame=30
assert export_ycd(d,str(root/'exports/cidade_sertao_torre.ycd.xml'))
# Editable source opens with the authored pose; exported action handles game facing.
rig.animation_data.action=action;bpy.context.scene.frame_set(1)
for o in bpy.data.objects:
 if 'carbine' in o.name.lower():o.hide_render=True;o.hide_set(True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'sertao_operador.blend'))
(root/'exports/sertao_contacts.json').write_text(json.dumps(contacts,indent=2))
print('TURRET_POSE_OK',contacts)
