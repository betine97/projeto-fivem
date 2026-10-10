import bpy,sys,json
from pathlib import Path
root=Path(__file__).resolve().parent.parent
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'combate_base.blend'))
from Sollumz.ycd.ycdimport import import_ycd
rig=bpy.data.objects['a_m_y_business_01']
d=import_ycd(str(root/'work/assets/aim_reference.ycd.xml'))
a=next(o for o in bpy.data.objects if o.sollum_type=='sollumz_animation')
a.animation_properties.target_id=rig.data
rig.animation_data_create();rig.animation_data.action=a.animation_properties.action;rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
result={b.name:{'loc':list(b.location),'quat':list(b.rotation_quaternion),'matrix':[list(row) for row in b.matrix_basis]} for b in rig.pose.bones}
(root/'work/aim_upper.json').write_text(json.dumps(result),encoding='utf8')
print('HEAD',[tuple(rig.pose.bones[n].head) for n in ['SKEL_Head','SKEL_R_Hand','SKEL_L_Hand','PH_R_Hand']])
