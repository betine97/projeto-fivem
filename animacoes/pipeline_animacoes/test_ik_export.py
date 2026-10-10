"""Create a test-only animated IK fixture, without changing the template."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(HERE/'esqueleto_trabalho.blend'))
rig=bpy.data.objects['GTA_Personagem_Rig']
target=bpy.data.objects['CTRL_L_HAND']
upper=rig.matrix_world@rig.pose.bones['SKEL_L_UpperArm'].head
end=rig.matrix_world@rig.pose.bones['SKEL_L_Hand'].head
target['IK']=1.0
for frame,offset in [(1,0),(10,.015)]:
    target.location=upper+(end-upper)*.93+Vector((0,-.035,offset))
    target.keyframe_insert(data_path='location',frame=frame)
    rig.pose.bones['SKEL_ROOT'].keyframe_insert(data_path='location',frame=frame)
rig.animation_data.action.name='TEST_CONTROLES'
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'reports/ik_export_fixture.blend'))
print('IK_FIXTURE_OK')
