"""Build copied native rigs, reachable rifle contacts, reloads and versioned YCD XML.

Run in Blender background. Original blend files and GTA archives are read only.
No server restart and no ped/skeleton replacement are performed.
"""
import bpy, sys, math, json, hashlib
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEPS = Path(r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
sys.path[:0] = [str(DEPS), str(DEPS.parent / 'sollumz'), str(ROOT / 'work')]
import addon_utils
addon_utils.enable('Sollumz', default_set=True)
from Sollumz.ycd.ycdimport import create_clip_dictionary_template, create_anim_obj
from Sollumz.ycd.ycdexport import export_ycd
from Sollumz.sollumz_properties import SollumType
from szio.gta5.cwxml.clipdictionary import YCD
from export_orientation import forward_action

for directory in ('sources', 'exports', 'previews', 'reports'):
    (HERE / directory).mkdir(parents=True, exist_ok=True)
report = {'game_tested': False, 'sources': {}, 'clips': {}, 'contacts': {}}
mounts = {}

def evaluate(rig, action, frame=1):
    rig.animation_data.action = action
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()

def snapshot(rig):
    return {b.name: b.matrix_basis.copy() for b in rig.pose.bones}

def restore(rig, values):
    for b in rig.pose.bones:
        b.matrix_basis = values[b.name]
        b.rotation_mode = 'QUATERNION'
    bpy.context.view_layer.update()

def orient(rig, name, direction):
    b = rig.pose.bones[name]
    child_name = {'Thigh': 'Calf', 'Calf': 'Foot', 'UpperArm': 'Forearm', 'Forearm': 'Hand', 'Foot': 'Toe0'}
    child = rig.pose.bones[name.rsplit('_', 1)[0] + '_' + child_name[name.split('_')[-1]]]
    rotation = (child.head - b.head).normalized().rotation_difference(Vector(direction).normalized()) @ b.matrix.to_quaternion()
    b.matrix = Matrix.Translation(b.head) @ rotation.to_matrix().to_4x4()
    bpy.context.view_layer.update()

def chain(rig, side, target, pole, leg=False):
    parts = ('Thigh', 'Calf', 'Foot') if leg else ('UpperArm', 'Forearm', 'Hand')
    a, b, end = [rig.pose.bones[f'SKEL_{side}_{part}'] for part in parts]
    target = rig.matrix_world.inverted() @ Vector(target)
    pole = rig.matrix_world.inverted() @ Vector(pole)
    l1 = (b.bone.head_local - a.bone.head_local).length
    l2 = (end.bone.head_local - b.bone.head_local).length
    delta = target - a.head
    reach = delta.length / (l1 + l2)
    assert .05 < reach < .99, ('Unreachable contact', side, target[:], reach)
    axis = delta.normalized()
    normal = pole - a.head
    normal = (normal - axis * normal.dot(axis)).normalized()
    along = (l1*l1 - l2*l2 + delta.length*delta.length) / (2*delta.length)
    joint = a.head + axis*along + normal*math.sqrt(max(0, l1*l1 - along*along))
    orient(rig, a.name, joint - a.head)
    orient(rig, b.name, target - b.head)
    return reach

def key_all(rig, frame):
    for b in rig.pose.bones:
        b.keyframe_insert(data_path='location', frame=frame, group=b.name)
        b.keyframe_insert(data_path='rotation_quaternion', frame=frame, group=b.name)

def curve_action(rig, name, baseline, apply, frames):
    rig.animation_data.action = None
    for frame in range(1, frames + 1):
        restore(rig, baseline)
        apply(frame)
        key_all(rig, frame)
    action = rig.animation_data.action
    action.name = name
    action.use_fake_user = True
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'LINEAR'
    return action

def local_signature(rig):
    return [{'name': b.name, 'tag': b.bone_properties.tag,
        'parent': b.parent.name if b.parent else None,
        'rest': [list(row) for row in b.matrix_local]} for b in rig.data.bones]

def smooth_path(frame, keys):
    for (fa, a), (fb, b) in zip(keys, keys[1:]):
        if fa <= frame <= fb:
            t = (frame - fa) / (fb - fa)
            t = t*t*(3 - 2*t)
            return a.lerp(b, t)
    return keys[-1][1]

for posture in ('ajoelhado', 'deitado', 'sentado'):
    source = ROOT / ('deitado_tiro.blend' if posture == 'deitado' else 'ajoelhado_refinado.blend')
    for weapon, short in [('carbinerifle', 'ar'), ('assaultrifle', 'ak')]:
        bpy.ops.wm.open_mainfile(filepath=str(source))
        sc = bpy.context.scene
        rig = bpy.data.objects['GTA_Personagem_Rig']
        original_signature = local_signature(rig)
        evaluate(rig, bpy.data.actions['DEITADO_mira' if posture == 'deitado' else 'ESTUDO_ajoelhar_mira'])
        baseline = snapshot(rig)
        handq = {s: rig.pose.bones[f'SKEL_{s}_Hand'].matrix.to_quaternion().copy() for s in ('L', 'R')}
        rig.animation_data.action = None
        restore(rig, baseline)
        if posture == 'sentado':
            # A seated-on-ground posture. It does not assume a chair's location.
            root_bone = rig.pose.bones['SKEL_ROOT']
            matrix = root_bone.matrix.copy()
            matrix.translation.z -= .33
            root_bone.matrix = matrix
            bpy.context.view_layer.update()
            for side, sign in [('L', 1), ('R', -1)]:
                chain(rig, side, (sign*.26, -.59, .075), (sign*.34, -.32, .32), leg=True)
                orient(rig, f'SKEL_{side}_Foot', (sign*.15, -1, -.10))
        # Bring the support shoulder forward rather than stretch the left arm.
        clav = rig.pose.bones['SKEL_L_Clavicle']
        upper = rig.pose.bones['SKEL_L_UpperArm']
        old = (upper.head - clav.head).normalized()
        direction = (.09, -.16, -.005) if posture == 'deitado' else (.17, -.06, -.015)
        q = old.rotation_difference(Vector(direction).normalized()) @ clav.matrix.to_quaternion()
        clav.matrix = Matrix.Translation(clav.head) @ q.to_matrix().to_4x4()
        bpy.context.view_layer.update()
        baseline = snapshot(rig)
        if weapon == 'assaultrifle':
            bpy.ops.sollumz.import_assets(directory=str(HERE / 'assets'), files=[{'name': 'w_ar_assaultrifle.ydr'}], use_custom_settings=True)
            oldgun = bpy.data.objects['w_ar_carbinerifle']
            for obj in [oldgun, *oldgun.children_recursive]:
                obj.hide_render = True
                obj.hide_set(True)
        gun = bpy.data.objects['w_ar_' + weapon]
        gun.constraints.clear()
        gun.rotation_mode = 'QUATERNION'
        gun.rotation_quaternion = Matrix((Vector((0,-1,0)), Vector((1,0,0)), Vector((0,0,1)))).transposed().to_quaternion()
        gripr = gun.data.bones['Gun_GripR'].head_local.copy()
        gripl = gun.data.bones['Gun_GripL'].head_local.copy()
        # Contact on the rear handguard, within reach for both rifle lengths.
        gripl.x -= .055 if weapon == 'carbinerifle' else .08
        right_target = Vector((-.20, -.78, .235) if posture == 'deitado' else (-.22, -.36, .60 if posture == 'sentado' else .93))
        gun.location = right_target - gun.rotation_quaternion @ gripr
        bpy.context.view_layer.update()
        left_target = gun.matrix_world @ gripl
        poles = {'R': Vector((-.35,-.59,.06) if posture == 'deitado' else (-.38,-.12,.43 if posture == 'sentado' else .76)),
                 'L': Vector((.14,-.77,.04) if posture == 'deitado' else (.24,-.26,.43 if posture == 'sentado' else .76))}
        def hands(r, l):
            reaches = {}
            for side, target in [('R', r), ('L', l)]:
                reaches[side] = chain(rig, side, target, poles[side])
                hand = rig.pose.bones[f'SKEL_{side}_Hand']
                hand.matrix = Matrix.Translation(hand.head) @ handq[side].to_matrix().to_4x4()
                bpy.context.view_layer.update()
            return reaches
        hands(right_target, left_target)
        idlebase = snapshot(rig)
        handworld = rig.matrix_world @ rig.pose.bones['SKEL_R_Hand'].matrix
        local = handworld.inverted() @ gun.matrix_world
        mount = {'position': list(local.translation), 'basis': [list(local.to_3x3().col[i]) for i in range(3)]}
        if weapon in mounts:
            assert max(abs(mount['position'][i] - mounts[weapon]['position'][i]) for i in range(3)) < 1e-5
        mounts[weapon] = mount
        c = gun.constraints.new('CHILD_OF')
        c.target = rig
        c.subtarget = 'SKEL_R_Hand'
        c.inverse_matrix = handworld.inverted()
        # Consistent studio materials for the newly imported weapon.
        if weapon == 'assaultrifle':
            material = bpy.data.materials.get('Estudo - carabina')
            for obj in gun.children_recursive:
                if obj.type == 'MESH':
                    for i in range(len(obj.data.materials)):
                        obj.data.materials[i] = material
        idle = curve_action(rig, 'MIRA_' + posture + '_' + short, idlebase, lambda f: None, 30)
        def recoil_apply(frame):
            back = .009*math.sin(math.pi*(frame-1)/9) if frame <= 10 else 0
            hands(right_target + Vector((0,back,0)), left_target + Vector((0,back,0)))
        recoil = curve_action(rig, 'RECUO_' + posture + '_' + short, idlebase, recoil_apply, 30)
        evaluate(rig, idle)
        magazine = gun.matrix_world @ gun.data.bones['WAPClip'].head_local + Vector((0,.01,-.045))
        cock = gun.matrix_world @ gun.data.bones['Gun_Cock1'].head_local
        # Reach to a low supply point, remove/reinsert magazine, work the action.
        supply = Vector((.03,-.48,.15) if posture == 'deitado' else (.02,-.12,.46 if posture == 'sentado' else .68))
        pull = magazine + Vector((.025,.025,-.07))
        keys = [(1,left_target), (10,magazine), (16,pull), (28,supply), (40,magazine), (47,magazine), (55,cock), (61,cock), (67,left_target)]
        def reload_apply(frame):
            hands(right_target, smooth_path(frame, keys))
        reload_action = curve_action(rig, 'RECARGA_' + posture + '_' + short, idlebase, reload_apply, 67)
        actions = [('mira', idle, 30), ('recuo', recoil, 30), ('recarga', reload_action, 30)]
        if posture == 'deitado':
            original_exit = bpy.data.actions['DEITADO_levantar']
            exit_samples = []
            for frame in range(1,92):
                evaluate(rig, original_exit, frame)
                exit_samples.append(snapshot(rig))
            changed = [name for name in idlebase if max(abs(idlebase[name][i][j]-exit_samples[0][name][i][j]) for i in range(4) for j in range(4)) > .0001]
            def exit_apply(frame):
                restore(rig, exit_samples[frame-1])
                if frame <= 25:
                    t=(frame-1)/24
                    t=t*t*(3-2*t)
                    for name in changed:
                        rig.pose.bones[name].matrix_basis=idlebase[name].lerp(exit_samples[frame-1][name],t)
            exit_action=curve_action(rig, 'SAIDA_' + posture + '_' + short, idlebase, exit_apply, 91)
            evaluate(rig, exit_action, 1)
            assert max(abs(rig.pose.bones[name].matrix_basis[i][j]-idlebase[name][i][j]) for name in idlebase for i in range(4) for j in range(4)) < .0001, 'Exit snaps away from the new prone grip'
            actions.append(('levantar_deitado', exit_action, 60))
        # Body/root/feet cannot drift while reloading, and wrist/gun must return exactly.
        contact_report = {'frames': 67, 'lower_body_drift_m': 0, 'right_grip_error_m': 0, 'return_error_m': 0, 'max_arm_reach_ratio': 0}
        evaluate(rig, idle)
        feet = {b.name: b.matrix.copy() for b in rig.pose.bones if any(t in b.name for t in ('Thigh','Calf','Foot','Toe','Pelvis')) or b.name == 'SKEL_ROOT'}
        for frame in range(1,68):
            evaluate(rig, reload_action, frame)
            for name, matrix in feet.items():
                error = max(abs(matrix[i][j] - rig.pose.bones[name].matrix[i][j]) for i in range(4) for j in range(4))
                contact_report['lower_body_drift_m'] = max(contact_report['lower_body_drift_m'], error)
                assert error < .0001, ('Reload moves legs/root', posture, name, frame)
            wrist = rig.matrix_world @ rig.pose.bones['SKEL_R_Hand'].head
            error = (wrist - gun.matrix_world @ gripr).length
            contact_report['right_grip_error_m'] = max(contact_report['right_grip_error_m'], error)
            assert error < .0001, ('Rifle lost right hand', posture, frame)
            for side in ('L','R'):
                a,b,end = [rig.pose.bones[f'SKEL_{side}_{p}'].head for p in ('UpperArm','Forearm','Hand')]
                reach = (end-a).length / ((b-a).length + (end-b).length)
                contact_report['max_arm_reach_ratio'] = max(contact_report['max_arm_reach_ratio'], reach)
                assert reach < .99
        for frame in (1,67):
            evaluate(rig, reload_action, frame)
            for b in rig.pose.bones:
                error = max(abs(b.matrix_basis[i][j]-idlebase[b.name][i][j]) for i in range(4) for j in range(4))
                contact_report['return_error_m'] = max(contact_report['return_error_m'], error)
                assert error < .0001, ('Reload discontinuity', posture, b.name, frame, error)
        assert local_signature(rig) == original_signature, 'Native rest skeleton was modified'
        report['contacts'][posture + '_' + short] = contact_report
        identifier = 'cidade_' + posture + '_v5_' + short
        dictionary, clips, animations = create_clip_dictionary_template(identifier)
        for name, action, rate in actions:
            animation = create_anim_obj(SollumType.ANIMATION)
            animation.name = identifier + '_' + name + '_anim'
            animation.parent = animations
            animation.animation_properties.hash = animation.name
            animation.animation_properties.target_id = rig.data
            animation.animation_properties.action = forward_action(rig, action)
            clip = create_anim_obj(SollumType.CLIP)
            clip.name = name
            clip.parent = clips
            clip.clip_properties.hash = name
            clip.clip_properties.name = name
            last = int(action.frame_range[1])
            clip.clip_properties.duration = (last - 1) / rate
            item = clip.clip_properties.animations.add()
            item.animation = animation
            item.start_frame = 1
            item.end_frame = last
        xml = HERE / 'exports' / (identifier + '.ycd.xml')
        assert export_ycd(dictionary, str(xml))
        result = YCD.from_xml_file(str(xml))
        assert len(result.clips) == len(actions)
        report['clips'][identifier] = {'count': len(actions), 'xml_roundtrip': True, 'binary_roundtrip': False, 'reload_seconds': 2.2}
        # Keep the source pose editable, with export collections hidden in viewport.
        evaluate(rig, idle)
        rig['status'] = 'v5 - copied native rest skeleton; awaiting FiveM visual validation'
        rig.show_in_front = True
        sc.frame_start = 1
        sc.frame_end = 67
        sc.render.resolution_x = 1100
        sc.render.resolution_y = 750
        sc.render.resolution_percentage = 100
        sc.cycles.samples = 16
        focus = Vector((0,-.38,.24 if posture == 'deitado' else .46 if posture == 'sentado' else .68))
        sc.camera.location = (2.5,-2.8,1.15 if posture == 'deitado' else 1.7)
        sc.camera.rotation_euler = (focus-sc.camera.location).to_track_quat('-Z','Y').to_euler()
        sc.camera.data.ortho_scale = 2.2
        bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 'sources' / (posture + '_' + short + '.blend')))
        report['sources'][posture + '_' + short] = {'original': str(source), 'original_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'native_bones': len(original_signature), 'rest_and_tags_preserved': True}
        if short == 'ak' and '--render' in sys.argv:
            sc.render.filepath = str(HERE / 'previews' / (posture + '_mira.png'))
            bpy.ops.render.render(write_still=True)
            evaluate(rig, reload_action, 40)
            sc.render.filepath = str(HERE / 'previews' / (posture + '_recarga.png'))
            bpy.ops.render.render(write_still=True)

(HERE / 'reports' / 'build.json').write_text(json.dumps(report,indent=2),encoding='utf8')
(HERE / 'exports' / 'weapon_mounts.json').write_text(json.dumps(mounts,indent=2),encoding='utf8')
lua = '-- Generated from the copied native rigs; do not hand-edit.\nCidadeCombatMounts={\n'
for weapon, data in mounts.items():
    lua += ' [joaat("WEAPON_' + weapon.upper() + '")]={position={' + ','.join(f'{x:.9f}' for x in data['position']) + '},basis={\n'
    lua += ',\n'.join('  {' + ','.join(f'{x:.9f}' for x in basis) + '}' for basis in data['basis']) + '\n }},\n'
lua += '}\n'
(HERE / 'exports' / 'combat_mounts.lua').write_text(lua,encoding='utf8')
print('PIPELINE_V5_BUILD_OK')
