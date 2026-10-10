"""Author and render a separate left support-hand review; no game deployment."""
import ast, bpy, sys, math, json
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
HERE = Path(__file__).resolve().parent
PIPE = HERE.parent
DEPS = Path(r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
sys.path[:0] = [str(DEPS), str(DEPS.parent / 'sollumz')]
import addon_utils
addon_utils.enable('Sollumz', default_set=True)
# Reuse native-axis FK solving only, without executing the pipeline's build.
tree = ast.parse((PIPE/'build.py').read_text(encoding='utf8'))
functions = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('evaluate','snapshot','restore','orient','chain','key_all','curve_action','local_signature')], type_ignores=[])
exec(compile(functions, str(PIPE/'build.py'), 'exec'), globals())
args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
settings = json.loads(args[0]) if args else {}
version = settings.get('version','r01')
posture = settings.get('posture','deitado')
assert posture in ('deitado','ajoelhado','sentado')
output = HERE/version
output.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(PIPE/'sources'/f'{posture}_ak.blend'))
scene = bpy.context.scene
rig = bpy.data.objects['GTA_Personagem_Rig']
gun = bpy.data.objects['w_ar_assaultrifle']
original_idle=bpy.data.actions[f'MIRA_{posture}_ak']
original_recoil=bpy.data.actions[f'RECUO_{posture}_ak']
recoil_samples=[]
original_reload=bpy.data.actions[f'RECARGA_{posture}_ak']
reload_samples=[]
if settings.get('correct_reload'):
    for frame in range(1,68):
        evaluate(rig,original_reload,frame)
        reload_samples.append((snapshot(rig),gun.matrix_world.copy(),(rig.matrix_world@rig.pose.bones['SKEL_L_Hand'].matrix).copy()))
if settings.get('correct_recoil'):
    for frame in range(1,31):
        evaluate(rig,original_recoil,frame)
        recoil_samples.append((snapshot(rig),gun.matrix_world.copy(),rig.pose.bones['SKEL_R_Hand'].matrix.copy()))
evaluate(rig,original_idle)
signature_before = local_signature(rig)
baseline = snapshot(rig)
right_before = rig.pose.bones['SKEL_R_Hand'].matrix.copy()
gun_before = gun.matrix_world.copy()
hand = rig.pose.bones['SKEL_L_Hand']
old_hand_world = rig.matrix_world @ hand.matrix
left_pole=Vector(settings.get('pole',(.14,-.77,.04) if posture=='deitado' else (.24,-.26,.76 if posture=='ajoelhado' else .43)))
def place_left_arm(target,q_world):
    reach=chain(rig,'L',target,left_pole)
    if settings.get('forearm_twist'):
        forearm=rig.pose.bones['SKEL_L_Forearm']
        relative_rest=hand.bone.matrix_local.inverted()@forearm.bone.matrix_local
        predicted=q_world@relative_rest.to_quaternion()
        axis_local=forearm.bone.matrix_local.to_3x3().inverted()@(hand.bone.head_local-forearm.bone.head_local)
        predicted_axis=predicted@axis_local
        actual_axis=rig.matrix_world.to_3x3()@(hand.head-forearm.head)
        twist_world=predicted_axis.normalized().rotation_difference(actual_axis.normalized())@predicted
        forearm.matrix=Matrix.Translation(forearm.head)@(rig.matrix_world.to_quaternion().inverted()@twist_world).to_matrix().to_4x4()
        bpy.context.view_layer.update()
    hand.matrix=rig.matrix_world.inverted()@Matrix.Translation(target)@q_world.to_matrix().to_4x4()
    bpy.context.view_layer.update()
    return reach
rig.animation_data.action = None
if not settings.get('before',False):
    # User-facing target is the handguard beneath the barrel, not the wrist marker.
    wrist_gun = Vector(settings.get('wrist',[.115,.022,-.067]))
    angle = math.radians(settings.get('roll',0))
    if settings.get('palm_under'):
        local_inverse=hand.matrix.inverted()
        mcps=[local_inverse@rig.pose.bones[f'SKEL_L_Finger{i}0'].head for i in range(1,5)]
        longitudinal=sum(mcps,Vector())/4
        longitudinal.normalize()
        across=mcps[0]-mcps[3]
        across=(across-longitudinal*across.dot(longitudinal)).normalized()
        normal=longitudinal.cross(across).normalized()
        source_frame=Matrix((longitudinal,across,normal)).transposed()
        desired_frame=Matrix((Vector((0,-1,0)),Vector((1,0,0)),Vector((0,0,1)))).transposed()
        q_world=gun.matrix_world.to_quaternion()@(desired_frame@source_frame.transposed()).to_quaternion()
    else:
        q_world = gun.matrix_world.to_quaternion() @ Quaternion((1,0,0),angle) @ (gun.matrix_world.to_quaternion().inverted() @ old_hand_world.to_quaternion())
    target = gun.matrix_world @ wrist_gun
    reach = place_left_arm(target,q_world)
    if settings.get('wrap_fingers'):
        def finger_direction(name,child_name,direction):
            b=rig.pose.bones[name]
            child=rig.pose.bones[child_name]
            axis=(child.head-b.head).normalized()
            direction=rig.matrix_world.to_3x3().inverted()@(gun.matrix_world.to_3x3()@Vector(direction))
            q=axis.rotation_difference(direction.normalized())@b.matrix.to_quaternion()
            b.matrix=Matrix.Translation(b.head)@q.to_matrix().to_4x4()
            bpy.context.view_layer.update()
        def fingertip_direction(i,direction):
            b=rig.pose.bones[f'SKEL_L_Finger{i}2']
            prev=rig.pose.bones[f'SKEL_L_Finger{i}1']
            physical_local=b.bone.matrix_local.to_3x3().inverted()@(b.bone.head_local-prev.bone.head_local)
            if settings.get('mesh_tip_axes'):
                axes=json.loads((HERE/'tip_axes.json').read_text(encoding='utf8'))
                physical_local=Vector(axes[str(i)]['actual_local'])
            axis=b.matrix.to_3x3()@physical_local
            dest=rig.matrix_world.to_3x3().inverted()@(gun.matrix_world.to_3x3()@Vector(direction))
            q=axis.normalized().rotation_difference(dest.normalized())@b.matrix.to_quaternion()
            b.matrix=Matrix.Translation(b.head)@q.to_matrix().to_4x4()
            bpy.context.view_layer.update()
        for i in range(1,5):
            finger_direction(f'SKEL_L_Finger{i}0',f'SKEL_L_Finger{i}1',(0,-settings.get('little_outward',.018) if i==4 else -settings.get('finger_outward',.006),.05))
            finger_direction(f'SKEL_L_Finger{i}1',f'SKEL_L_Finger{i}2',settings.get('middle_direction',(0,.003,.032)))
            b=rig.pose.bones[f'SKEL_L_Finger{i}2']
            b.rotation_mode='QUATERNION'
            b.rotation_quaternion=Quaternion((1,0,0,0))
            bpy.context.view_layer.update()
            fingertip_direction(i,settings.get('tip_direction',(0,.024,.004)))
        if settings.get('thumb_wrap'):
            finger_direction('SKEL_L_Finger00','SKEL_L_Finger01',settings.get('thumb0',(.018,.030,.034)))
            finger_direction('SKEL_L_Finger01','SKEL_L_Finger02',settings.get('thumb1',(-.020,-.020,.014)))
            fingertip_direction(0,settings.get('thumb2',(-.012,-.012,-.003)))
        bpy.context.view_layer.update()
    # Finger adjustments are local pose rotations; never alter the native rest rig.
    for name,degrees in settings.get('fingers',{}).items():
        bone=rig.pose.bones[name]
        bone.rotation_mode='QUATERNION'
        bone.rotation_quaternion = bone.rotation_quaternion @ Quaternion(Vector(degrees[:3]),math.radians(degrees[3]))
    bpy.context.view_layer.update()
else:
    reach = None
pose = snapshot(rig)
action = curve_action(rig,'REVISAO_apoio_esquerdo_'+version,pose,lambda frame:None,30)
evaluate(rig,action)
assert signature_before == local_signature(rig), 'Changed native skeleton'
assert max(abs(right_before[i][j]-rig.pose.bones['SKEL_R_Hand'].matrix[i][j]) for i in range(4) for j in range(4)) < .0001, 'Moved right hand'
assert max(abs(gun_before[i][j]-gun.matrix_world[i][j]) for i in range(4) for j in range(4)) < .0001, 'Moved weapon'
for name,values in baseline.items():
    if not name.startswith(('SKEL_L_UpperArm','SKEL_L_Forearm','SKEL_L_Hand','SKEL_L_Finger')):
        assert max(abs(values[i][j]-pose[name][i][j]) for i in range(4) for j in range(4)) < .0001, ('Moved unrelated bone',name)
recoil_action=None
recoil_report=None
if settings.get('correct_recoil'):
    finger_basis={n:m for n,m in pose.items() if n.startswith('SKEL_L_Finger')}
    hand_gun_rotation=gun_before.to_quaternion().inverted()@(rig.matrix_world@hand.matrix).to_quaternion()
    def corrected_recoil(frame):
        sample,gun_matrix,original_right=recoil_samples[frame-1]
        restore(rig,sample)
        place_left_arm(gun_matrix@wrist_gun,gun_matrix.to_quaternion()@hand_gun_rotation)
        for name,matrix in finger_basis.items():
            rig.pose.bones[name].matrix_basis=matrix
        bpy.context.view_layer.update()
    recoil_action=curve_action(rig,'REVISAO_recuo_'+version,pose,corrected_recoil,30)
    recoil_report={'frames':30,'left_wrist_contact_error_m':0,'max_right_hand_change':0,'max_lower_body_change':0}
    for frame in range(1,31):
        evaluate(rig,recoil_action,frame)
        sample,gun_matrix,original_right=recoil_samples[frame-1]
        actual=gun.matrix_world.inverted()@(rig.matrix_world@hand.head)
        recoil_report['left_wrist_contact_error_m']=max(recoil_report['left_wrist_contact_error_m'],(actual-wrist_gun).length)
        recoil_report['max_right_hand_change']=max(recoil_report['max_right_hand_change'],max(abs(original_right[i][j]-rig.pose.bones['SKEL_R_Hand'].matrix[i][j]) for i in range(4) for j in range(4)))
        for name,matrix in sample.items():
            if not name.startswith(('SKEL_L_UpperArm','SKEL_L_Forearm','SKEL_L_Hand','SKEL_L_Finger')):
                error=max(abs(matrix[i][j]-rig.pose.bones[name].matrix_basis[i][j]) for i in range(4) for j in range(4))
                recoil_report['max_lower_body_change']=max(recoil_report['max_lower_body_change'],error)
    assert max(recoil_report[k] for k in ('left_wrist_contact_error_m','max_right_hand_change','max_lower_body_change'))<.0001,recoil_report
    evaluate(rig,action)
reload_action=None
reload_report=None
if settings.get('correct_reload'):
    finger_basis={n:m for n,m in pose.items() if n.startswith('SKEL_L_Finger')}
    hand_gun_rotation=gun_before.to_quaternion().inverted()@(rig.matrix_world@hand.matrix).to_quaternion()
    old_wrist_gun=gun_before.inverted()@old_hand_world.translation
    def corrected_reload(frame):
        sample,gun_matrix,original_left=reload_samples[frame-1]
        restore(rig,sample)
        # Keep the existing magazine/charging-handle path, but depart from and
        # return to the NEW support grip rather than the old floating fingers.
        t=max(0,1-(frame-1)/9) if frame<=10 else max(0,(frame-61)/6)
        weight=t*t*(3-2*t)
        target=original_left.translation+gun_matrix.to_3x3()@(wrist_gun-old_wrist_gun)*weight
        rotation=original_left.to_quaternion().slerp(gun_matrix.to_quaternion()@hand_gun_rotation,weight)
        place_left_arm(target,rotation)
        for name,matrix in finger_basis.items():
            rig.pose.bones[name].matrix_basis=sample[name].lerp(matrix,weight)
        bpy.context.view_layer.update()
    reload_action=curve_action(rig,'REVISAO_recarga_'+version,pose,corrected_reload,67)
    reload_report={'frames':67,'non_left_bone_error':0,'return_to_idle_error':0,'weapon_matrix_error':0}
    for frame in range(1,68):
        evaluate(rig,reload_action,frame)
        sample,gun_matrix,_=reload_samples[frame-1]
        reload_report['weapon_matrix_error']=max(reload_report['weapon_matrix_error'],max(abs(gun_matrix[i][j]-gun.matrix_world[i][j]) for i in range(4) for j in range(4)))
        for name,matrix in sample.items():
            if not name.startswith(('SKEL_L_UpperArm','SKEL_L_Forearm','SKEL_L_Hand','SKEL_L_Finger')):
                reload_report['non_left_bone_error']=max(reload_report['non_left_bone_error'],max(abs(matrix[i][j]-rig.pose.bones[name].matrix_basis[i][j]) for i in range(4) for j in range(4)))
        if frame in (1,67):
            reload_report['return_to_idle_error']=max(reload_report['return_to_idle_error'],max(abs(matrix[i][j]-rig.pose.bones[name].matrix_basis[i][j]) for name,matrix in pose.items() for i in range(4) for j in range(4)))
    assert max(reload_report[k] for k in ('non_left_bone_error','return_to_idle_error','weapon_matrix_error'))<.0001,reload_report
    evaluate(rig,action)
if settings.get('export_v6'):
    assert recoil_action and reload_action
    sys.path.insert(0,str(PIPE.parent/'work'))
    from export_orientation import forward_action
    from Sollumz.ycd.ycdimport import create_clip_dictionary_template,create_anim_obj
    from Sollumz.ycd import ycdexport
    from szio.gta5.cwxml import clipdictionary as ycdxml
    # The default minimum-delta quantizer can choose very coarse quanta for
    # fingers that move only during the short reload lead-in/out. Preserve the
    # authored floats in this export process; do not patch the installed addon.
    def contact_values_channel(values,unique):
        if len(unique)==1:
            channel=ycdxml.ChannelsList.StaticFloat();channel.value=values[0]
        else:
            channel=ycdxml.ChannelsList.RawFloat();channel.values=values
        return channel
    ycdexport.build_values_channel=contact_values_channel
    export_ycd=ycdexport.export_ycd
    from Sollumz.sollumz_properties import SollumType
    identifier=f'cidade_{posture}_v6_ak'
    actions=[('mira',action,30),('recuo',recoil_action,30),('recarga',reload_action,30)]
    if posture=='deitado':
        exit_original=bpy.data.actions['SAIDA_deitado_ak']
        exit_samples=[]
        for frame in range(1,92):
            evaluate(rig,exit_original,frame)
            exit_samples.append(snapshot(rig))
        def exit_corrected(frame):
            restore(rig,exit_samples[frame-1])
            if frame<=25:
                t=(frame-1)/24;t=t*t*(3-2*t)
                for name in finger_basis.keys()|{'SKEL_L_UpperArm','SKEL_L_Forearm','SKEL_L_Hand'}:
                    rig.pose.bones[name].matrix_basis=pose[name].lerp(exit_samples[frame-1][name],t)
        exit_action=curve_action(rig,'REVISAO_saida_'+version,pose,exit_corrected,91)
        actions.append(('levantar_deitado',exit_action,60))
    dictionary,clips,animations=create_clip_dictionary_template(identifier)
    for name,source,rate in actions:
        animation=create_anim_obj(SollumType.ANIMATION)
        animation.name=identifier+'_'+name+'_anim';animation.parent=animations
        animation.animation_properties.hash=animation.name
        animation.animation_properties.target_id=rig.data
        animation.animation_properties.action=forward_action(rig,source)
        clip=create_anim_obj(SollumType.CLIP);clip.name=name;clip.parent=clips
        clip.clip_properties.hash=name;clip.clip_properties.name=name
        last=int(source.frame_range[1]);clip.clip_properties.duration=(last-1)/rate
        binding=clip.clip_properties.animations.add();binding.animation=animation
        # Sollumz exports samples starting at time zero even when the Blender
        # action begins at frame 1. Do not request a time beyond its duration.
        binding.start_frame=0;binding.end_frame=last-1
    assert export_ycd(dictionary,str(output/(identifier+'.ycd.xml')))
    evaluate(rig,action)
scene.frame_start=1
scene.frame_end=30
scene.render.resolution_x=1400
scene.render.resolution_y=1000
scene.render.resolution_percentage=100
scene.cycles.samples=settings.get('samples',32)
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
focus = gun.matrix_world @ Vector((.19,0,.005))
# Both sides, barrel-facing, overhead, and a full-body pose.
views={
    '01_lado_esquerdo': (focus+Vector((.65,.04,.24)),focus,.55),
    '02_lado_direito': (focus+Vector((-.65,-.03,.20)),focus,.55),
    '03_frente': (focus+Vector((.08,-.65,.11)),focus,.55),
    '04_por_baixo': (focus+Vector((.36,-.2,-.105)),focus,.49),
    '05_de_cima': (focus+Vector((.12,-.10,.8)),focus,.64),
    '06_pose_completa': (Vector((2.5,-2.8,1.15 if posture=='deitado' else 1.7)),Vector((0,-.38,.24 if posture=='deitado' else .68)),2.2),
}
report={'source':f'{posture}_ak.blend','blend_file':f'{posture}_ak_mao_esquerda.blend','version':version,'game_deployed':False,'settings':settings,'reach_ratio':reach,'native_rest_preserved':True,'right_hand_and_weapon_preserved':True,'wrist_gun_local':list(gun.matrix_world.inverted()@(rig.matrix_world@hand.head)),'idle_action':action.name,'recoil_action':recoil_action.name if recoil_action else None,'recoil_validation':recoil_report}
report['reload_action']=reload_action.name if reload_action else None
report['reload_validation']=reload_report
report['left_hand_bones']={b.name:list(gun.matrix_world.inverted()@(rig.matrix_world@b.head)) for b in rig.pose.bones if b.name.startswith(('SKEL_L_Hand','SKEL_L_Finger'))}
(output/'ajuste.json').write_text(json.dumps(report,indent=2),encoding='utf8')
for label,(location,target,scale) in views.items():
    if settings.get('no_render'):
        continue
    if settings.get('views') and label not in settings['views']:
        continue
    scene.camera.location=location
    scene.camera.rotation_euler=(target-location).to_track_quat('-Z','Y').to_euler()
    scene.camera.data.type='ORTHO'
    scene.camera.data.ortho_scale=scale
    scene.camera.data.clip_start=.001
    scene.render.filepath=str(output/(label+'.png'))
    bpy.ops.render.render(write_still=True)
if recoil_action and not settings.get('no_render'):
    evaluate(rig,recoil_action,5)
    shot_focus=gun.matrix_world@Vector((.19,0,.005))
    scene.camera.location=shot_focus+Vector((-.65,-.03,.20))
    scene.camera.rotation_euler=(shot_focus-scene.camera.location).to_track_quat('-Z','Y').to_euler()
    scene.camera.data.ortho_scale=.55
    scene.render.filepath=str(output/'07_recuo.png')
    bpy.ops.render.render(write_still=True)
    evaluate(rig,action)
if reload_action and not settings.get('no_render'):
    evaluate(rig,reload_action,67)
    reload_focus=gun.matrix_world@Vector((.19,0,.005))
    scene.camera.location=reload_focus+Vector((-.65,-.03,.20))
    scene.camera.rotation_euler=(reload_focus-scene.camera.location).to_track_quat('-Z','Y').to_euler()
    scene.camera.data.ortho_scale=.55
    scene.render.filepath=str(output/'08_pos_recarga.png')
    bpy.ops.render.render(write_still=True)
    evaluate(rig,action)
scene.camera.location=views['01_lado_esquerdo'][0]
scene.camera.rotation_euler=(focus-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.camera.data.ortho_scale=.55
# Open the saved file in the edited pose, rather than an old action.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=.85
            area.spaces.active.region_3d.view_location=focus
            area.spaces.active.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion()
rig['revisao_mao_esquerda']='Copia para revisar apoio sob o cano; ainda nao aplicada no jogo'
bpy.ops.wm.save_as_mainfile(filepath=str(output/f'{posture}_ak_mao_esquerda.blend'))
print('LEFT_HAND_REVIEW_OK',version,report['wrist_gun_local'])
