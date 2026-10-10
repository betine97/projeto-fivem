"""Exercise IK contacts and root controls in memory, preserving the saved template."""
import bpy,sys,json
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
DEPS=Path(r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
sys.path[:0]=[str(DEPS),str(DEPS.parent/'sollumz')]
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
bpy.ops.wm.open_mainfile(filepath=str(HERE/'esqueleto_trabalho.blend'))
rig=bpy.data.objects['GTA_Personagem_Rig']
bpy.context.view_layer.update()
before=rig.matrix_world@rig.pose.bones['SKEL_Head'].head
bpy.data.objects['CTRL_ROOT'].location.z+=.10
bpy.context.view_layer.update()
after=rig.matrix_world@rig.pose.bones['SKEL_Head'].head
assert abs((after-before).z-.10)<.0001, 'Root control does not move the full body'
bpy.data.objects['CTRL_ROOT'].location.z-=.10
bpy.context.view_layer.update()
results={}
for side in ('L','R'):
    for kind,parts in [('HAND',('UpperArm','Forearm','Hand')),('FOOT',('Thigh','Calf','Foot'))]:
        upper,lower,end=[rig.pose.bones[f'SKEL_{side}_{part}'] for part in parts]
        start=rig.matrix_world@upper.head
        finish=rig.matrix_world@end.head
        target=bpy.data.objects[f'CTRL_{side}_{kind}']
        target.location=start+(finish-start)*.93+Vector((0,-.035,0))
        target['IK']=1.0;target.update_tag()
        bpy.context.view_layer.update()
        error=(rig.matrix_world@end.head-target.matrix_world.translation).length
        assert error<.001, ('IK missed target',side,kind,error)
        assert all(max(abs(v-1) for v in b.scale)<.001 for b in (upper,lower,end)), 'IK stretches bones'
        results[f'{side}_{kind}']={'contact_error_m':error,'no_stretch':True}
(HERE/'reports/template-tests.json').write_text(json.dumps({'root_control':True,'ik':results,'source_modified':False},indent=2),encoding='utf8')
print('IK_TEMPLATE_PASS',results)
