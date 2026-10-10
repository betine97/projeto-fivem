"""Decode every packaged stride/pitch sample and verify the masked skeleton."""
import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
HERE=Path(__file__).resolve().parent
DEPS=Path('C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps')
sys.path[:0]=[str(DEPS),str(DEPS.parent/'sollumz')]
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
from szio.gta5.cwxml.clipdictionary import YCD
from Sollumz.ycd.ycdimport import combine_sequences_and_build_action_data
grid=json.loads((HERE/'crawl_grid.json').read_text())
report={'game_tested':False,'masked_binary_skeleton':True,'assets':{}}
for identifier,records in grid['assets'].items():
    short=identifier.split('_')[-1]
    bpy.ops.wm.open_mainfile(filepath=str(HERE/'sources'/f'rastejar_mira_{short}.blend'))
    rig=bpy.data.objects['GTA_Personagem_Rig'];scene=bpy.context.scene
    gun=bpy.data.objects['w_ar_'+('carbinerifle' if short=='ar' else 'assaultrifle')]
    # Mount is constant in the native right-wrist space, independent of root.
    mount=(rig.matrix_world@rig.pose.bones['SKEL_R_Hand'].matrix).inverted()@gun.matrix_world
    ordered=[]
    def visit(b):
        ordered.append(b)
        for child in b.children:visit(child)
    visit(rig.data.bones['SKEL_ROOT'])
    upper=[b for b in ordered if b.name=='SKEL_Spine0' or any(a.name=='SKEL_Spine0' for a in b.parent_recursive)]
    by_tag={b.bone_properties.tag:b for b in ordered}
    def local(data,b,frame):
        tracks=data[b.bone_properties.tag]
        return Matrix.LocRotScale(tracks[0][frame],tracks[1][frame],Vector((1,1,1)))
    reference=YCD.from_xml_file(str(HERE/'exports'/f'cidade_mira_v9_deitado_{short}.roundtrip.xml'))
    reference_data=combine_sequences_and_build_action_data(reference.animations[0])
    expected=[]
    for column in range(44):
        matrices={}
        for b in ordered:matrices[b.name]=(matrices[b.parent.name] if b.parent else Matrix.Identity(4))@local(reference_data,b,column)
        expected.append(matrices)
    binary=YCD.from_xml_file(str(HERE/'exports'/(identifier+'.roundtrip.xml')))
    original=YCD.from_xml_file(str(HERE/'exports'/(identifier+'.ycd.xml')))
    original_by_hash={a.hash:a for a in original.animations}
    decoded_by_hash={a.hash:a for a in binary.animations}
    checks={'samples':0,'max_pitch_error_degrees':0,'max_hand_position_error_m':0,'max_channel_error':0,'clips':{}}
    for clip in binary.clips:
        direction=clip.name.split('_')[-1];record=records[direction]
        anim=decoded_by_hash[clip.animation_hash]
        data=combine_sequences_and_build_action_data(anim)
        original_data=combine_sequences_and_build_action_data(original_by_hash[anim.hash])
        assert anim.frame_count==record['frames'] and set(data)==set(by_tag)
        assert abs(clip.start_time)<1e-7 and abs(clip.end_time-anim.duration)<1e-5
        for frame in range(anim.frame_count):
            row,column=divmod(frame,44);native_parent=Matrix(record['parents'][row])
            matrices={}
            for b in upper:
                tracks=data[b.bone_properties.tag]
                assert abs(tracks[1][frame].magnitude-1)<.002
                parent=native_parent if b.name=='SKEL_Spine0' else matrices[b.parent.name]
                matrices[b.name]=parent@local(data,b,frame)
                for track in (0,1):
                    error=max(abs(x-y) for x,y in zip(tracks[track][frame],original_data[b.bone_properties.tag][track][frame]))
                    checks['max_channel_error']=max(checks['max_channel_error'],error)
            for name in ('SKEL_R_Hand','SKEL_L_Hand'):
                checks['max_hand_position_error_m']=max(checks['max_hand_position_error_m'],
                    (matrices[name].translation-expected[column][name].translation).length)
            axis=((matrices['SKEL_R_Hand']@mount).to_3x3()@Vector((1,0,0))).normalized()
            pitch=math.degrees(math.asin(max(-1,min(1,axis.z))))
            checks['max_pitch_error_degrees']=max(checks['max_pitch_error_degrees'],abs(pitch-(-8+column)))
            checks['samples']+=1
        checks['clips'][direction]={'rows':record['rows'],'frames':anim.frame_count}
    assert checks['max_pitch_error_degrees']<.01 and checks['max_hand_position_error_m']<.0001 and checks['max_channel_error']<.002,checks
    checks['sha256']=hashlib.sha256((HERE/'exports'/(identifier+'.ycd')).read_bytes()).hexdigest()
    report['assets'][identifier]=checks
    print('CRAWL_AIM_BINARY_OK',identifier,json.dumps(checks),flush=True)
    if '--render' in sys.argv:
        # Composite decoded upper body onto the pelvis of a mid-stride native pose.
        rig.animation_data.action=None
        column,row=38,14
        for tag,tracks in reference_data.items():
            b=rig.pose.bones[by_tag[tag].name]
            rest=((b.bone.parent.matrix_local.inverted()@b.bone.matrix_local) if b.parent else b.bone.matrix_local).inverted()
            b.location=rest@tracks[0][column];b.rotation_mode='QUATERNION';b.rotation_quaternion=rest.to_quaternion()@tracks[1][column]
        bpy.context.view_layer.update()
        rig.pose.bones['SKEL_Spine0'].parent.matrix=Matrix(records['fwd']['parents'][row])
        clip=next(c for c in binary.clips if c.name.endswith('_fwd'))
        data=combine_sequences_and_build_action_data(decoded_by_hash[clip.animation_hash]);frame=row*44+column
        for bone in upper:
            b=rig.pose.bones[bone.name];tracks=data[bone.bone_properties.tag]
            rest=(bone.parent.matrix_local.inverted()@bone.matrix_local).inverted()
            b.location=rest@tracks[0][frame];b.rotation_quaternion=rest.to_quaternion()@tracks[1][frame]
        bpy.context.view_layer.update()
        root=rig.pose.bones['SKEL_ROOT'];root.matrix=Matrix.Rotation(-math.pi,4,'Z')@root.matrix
        bpy.context.view_layer.update()
        scene.render.engine='CYCLES';scene.cycles.samples=12
        scene.render.resolution_x=1000;scene.render.resolution_y=760;scene.render.resolution_percentage=100
        scene.render.image_settings.file_format='PNG'
        focus=gun.matrix_world.translation;scene.camera.location=focus+Vector((1.8,-.15,.7))
        scene.camera.rotation_euler=(focus-scene.camera.location).to_track_quat('-Z','Y').to_euler()
        scene.camera.data.type='ORTHO';scene.camera.data.ortho_scale=2.1
        scene.render.filepath=str(HERE/'exports'/(identifier+'_composite.png'))
        bpy.ops.render.render(write_still=True)
(HERE/'crawl_binary_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
