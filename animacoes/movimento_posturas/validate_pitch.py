"""Compare every frame of the actual packaged YCD against the Blender source."""
import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
HERE=Path(__file__).resolve().parent
DEPS=Path('C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps')
sys.path[:0]=[str(DEPS),str(DEPS.parent/'sollumz')]
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
from szio.gta5.cwxml.clipdictionary import YCD
from Sollumz.ycd.ycdimport import combine_sequences_and_build_action_data
build=json.loads((HERE/'pitch_build.json').read_text())
report={'game_tested':False,'assets':{}}
for identifier,asset in build['assets'].items():
    posture,short=identifier.split('_')[-2:]
    bpy.ops.wm.open_mainfile(filepath=str(HERE/'sources'/f'{posture}_{short}_mira_vertical.blend'))
    rig=bpy.data.objects['GTA_Personagem_Rig'];scene=bpy.context.scene
    gun=bpy.data.objects['w_ar_'+('carbinerifle' if short=='ar' else 'assaultrifle')]
    action=bpy.data.actions[f'MIRA_VERTICAL_{posture}_{short}']
    dictionary=YCD.from_xml_file(str(HERE/'exports'/(identifier+'.roundtrip.xml')))
    assert len(dictionary.clips)==len(dictionary.animations)==1
    clip,anim=dictionary.clips[0],dictionary.animations[0]
    assert clip.name.split('/')[-1]=='mira_vertical' and anim.frame_count==asset['frames']
    assert abs(clip.start_time)<1e-7 and abs(clip.end_time-anim.duration)<1e-6
    data=combine_sequences_and_build_action_data(anim)
    original_anim=YCD.from_xml_file(str(HERE/'exports'/(identifier+'.ycd.xml'))).animations[0]
    original_data=combine_sequences_and_build_action_data(original_anim)
    by_tag={b.bone.bone_properties.tag:b for b in rig.pose.bones}
    assert set(data)==set(by_tag) and len(by_tag)==98
    inverse={tag:((b.bone.parent.matrix_local.inverted()@b.bone.matrix_local) if b.parent else b.bone.matrix_local).inverted()
             for tag,b in by_tag.items()}
    checks={'frames':anim.frame_count,'max_matrix_error':0,'max_pitch_error_degrees':0,'max_channel_error':0}
    for frame in range(anim.frame_count):
        rig.animation_data.action=action;scene.frame_set(frame+1);bpy.context.view_layer.update()
        expected={b.name:b.matrix.copy() for b in rig.pose.bones}
        rig.animation_data.action=None
        for tag,tracks in data.items():
            b=by_tag[tag];rest=inverse[tag]
            assert set(tracks)=={0,1} and abs(tracks[1][frame].magnitude-1)<.002
            for track in (0,1):
                error=max(abs(x-y) for x,y in zip(tracks[track][frame],original_data[tag][track][frame]))
                if error>checks['max_channel_error']:
                    checks['max_channel_error']=error;checks['worst_channel']=[b.name,track,frame]
            b.location=rest@tracks[0][frame];b.rotation_mode='QUATERNION'
            b.rotation_quaternion=rest.to_quaternion()@tracks[1][frame];b.scale=(1,1,1)
        bpy.context.view_layer.update()
        root=rig.pose.bones['SKEL_ROOT'];root.matrix=Matrix.Rotation(-math.pi,4,'Z')@root.matrix
        bpy.context.view_layer.update()
        checks['max_matrix_error']=max(checks['max_matrix_error'],max(abs(b.matrix[i][j]-expected[b.name][i][j])
                for b in rig.pose.bones for i in range(4) for j in range(4)))
        axis=(gun.matrix_world.to_3x3()@Vector((1,0,0))).normalized()
        pitch=math.degrees(math.asin(max(-1,min(1,axis.z))))
        checks['max_pitch_error_degrees']=max(checks['max_pitch_error_degrees'],abs(pitch-(asset['min_pitch']+frame)))
        if '--render' in sys.argv and frame in (0,-asset['min_pitch'],anim.frame_count-1):
            scene.render.engine='CYCLES';scene.cycles.samples=12
            scene.render.resolution_x=1000;scene.render.resolution_y=760;scene.render.resolution_percentage=100
            scene.render.image_settings.file_format='PNG'
            focus=gun.matrix_world.translation
            scene.camera.location=focus+Vector((1.75,-.15,.6))
            scene.camera.rotation_euler=(focus-scene.camera.location).to_track_quat('-Z','Y').to_euler()
            scene.camera.data.type='ORTHO';scene.camera.data.ortho_scale=2.0
            scene.render.filepath=str(HERE/'exports'/f'{identifier}_{asset["min_pitch"]+frame}.png')
            bpy.ops.render.render(write_still=True)
    print('PITCH_DECODE_CHECK',identifier,json.dumps(checks),flush=True)
    assert checks['max_matrix_error']<.002 and checks['max_pitch_error_degrees']<.1,checks
    checks['sha256']=hashlib.sha256((HERE/'exports'/(identifier+'.ycd')).read_bytes()).hexdigest()
    report['assets'][identifier]=checks
    print('PITCH_BINARY_OK',identifier,json.dumps(checks),flush=True)
(HERE/'binary_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
