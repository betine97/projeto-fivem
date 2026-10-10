"""Inspect the installed GTA crawl skeleton before masking authored upper body."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Matrix,Vector
HERE=Path(__file__).resolve().parent
DEPS=Path('C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps')
sys.path[:0]=[str(DEPS),str(DEPS.parent/'sollumz')]
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
from szio.gta5.cwxml.clipdictionary import YCD
from Sollumz.ycd.ycdimport import combine_sequences_and_build_action_data
bpy.ops.wm.open_mainfile(filepath=str(HERE/'sources/deitado_ar_mira_vertical.blend'))
rig=bpy.data.objects['GTA_Personagem_Rig'];gun=bpy.data.objects['w_ar_carbinerifle']
rig.animation_data.action=None
by_tag={b.bone.bone_properties.tag:b for b in rig.pose.bones}
inverse={t:((b.bone.parent.matrix_local.inverted()@b.bone.matrix_local) if b.parent else b.bone.matrix_local).inverted()
         for t,b in by_tag.items()}
def apply(data,frame,upper=False):
    for tag,tracks in data.items():
        if tag not in by_tag:continue
        b=by_tag[tag]
        if upper and not any(ancestor.name=='SKEL_Spine0' for ancestor in [b,*b.parent_recursive]):continue
        if 0 in tracks:b.location=inverse[tag]@tracks[0][frame]
        if 1 in tracks:b.rotation_mode='QUATERNION';b.rotation_quaternion=inverse[tag].to_quaternion()@tracks[1][frame]
        b.scale=(1,1,1)
    bpy.context.view_layer.update()
native=YCD.from_xml_file(str(HERE/'exports/native_move_crawl.xml'))
clip=next(c for c in native.clips if c.name=='pack:/onfront_fwd.clip')
anims={a.hash:a for a in native.animations}
authored=YCD.from_xml_file(str(HERE/'exports/cidade_mira_v9_deitado_ar.roundtrip.xml')).animations[0]
ad=combine_sequences_and_build_action_data(authored)
apply(ad,8)
target=(gun.matrix_world.to_3x3()@Vector((1,0,0))).normalized()
target_parent=rig.pose.bones['SKEL_Spine0'].parent.matrix.copy()
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
for binding in clip.animations:
    a=anims[binding.animation_hash];data=combine_sequences_and_build_action_data(a)
    frame=round(binding.start_time/a.duration*(a.frame_count-1))
    apply(data,frame)
    if 0 in data:print('NATIVE_ROOT',list(data[0][1][frame]),list(data[0][0][frame]))
native_parent=rig.pose.bones['SKEL_Spine0'].parent.matrix.copy()
apply(ad,8,upper=True)
axis=(gun.matrix_world.to_3x3()@Vector((1,0,0))).normalized()
report={'target_axis':list(target),'masked_axis':list(axis),'yaw_error':math.degrees(axis.angle(target)),
        'target_parent':[list(r) for r in target_parent],'native_parent':[list(r) for r in native_parent]}
(HERE/'crawl_skeleton_check.json').write_text(json.dumps(report,indent=2))
print('CRAWL_SKELETON',json.dumps(report))
