"""Add vertical rifle aim to COPIES of the approved native Blender rigs.

Original v5/v6 poses, reloads, mounts and skeletons are preserved. The game
samples this short animation by pitch; it is not a stand-up or body rotation.
"""
import ast
import bpy
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from mathutils import Matrix, Quaternion, Vector

HERE = Path(__file__).resolve().parent
PIPE = HERE.parent / 'pipeline_animacoes'
DEPS = Path('C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps')
sys.path[:0] = [str(DEPS), str(DEPS.parent / 'sollumz'), str(HERE.parent / 'work')]
import addon_utils
addon_utils.enable('Sollumz', default_set=True)
from Sollumz.ycd.ycdimport import create_clip_dictionary_template, create_anim_obj
from Sollumz.ycd.ycdexport import export_ycd
import Sollumz.ycd.ycdexport as ycd_exporter
from Sollumz.sollumz_properties import SollumType
from export_orientation import forward_action

# QuantizeFloat's automatic step loses up to 0.35 degrees on these wrist
# curves after CodeWalker packing. Store changing channels as native RawFloat;
# leave constant channels compressed. This override lives only in this build.
_compressed_channel=ycd_exporter.build_values_channel
def precise_channel(values,uniq_values,indirect_percentage=0.1):
    if len(uniq_values)==1:
        return _compressed_channel(values,uniq_values,indirect_percentage)
    channel=ycd_exporter.ycdxml.ChannelsList.RawFloat()
    channel.values=values
    return channel
ycd_exporter.build_values_channel=precise_channel

tree = ast.parse((PIPE / 'build.py').read_text(encoding='utf8'))
helpers = {'evaluate', 'snapshot', 'restore', 'orient', 'chain', 'key_all', 'curve_action', 'local_signature'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in helpers],
                        type_ignores=[]), str(PIPE / 'build.py'), 'exec'), globals())
(HERE / 'sources').mkdir(exist_ok=True)
(HERE / 'exports').mkdir(exist_ok=True)
report = {'game_tested': False, 'assets': {}}

for posture, limits in [('deitado', (-8, 35)), ('ajoelhado', (-45, 45))]:
    for short, weapon in [('ar', 'carbinerifle'), ('ak', 'assaultrifle')]:
        source = (PIPE / 'sources' / f'{posture}_{short}.blend' if short == 'ar' else
                  PIPE / 'revisao_mao_esquerda' / f'{posture}_v6' / f'{posture}_ak_mao_esquerda.blend')
        bpy.ops.wm.open_mainfile(filepath=str(source))
        rig = bpy.data.objects['GTA_Personagem_Rig']
        gun = bpy.data.objects['w_ar_' + weapon]
        idle = bpy.data.actions[f'MIRA_{posture}_{short}' if short == 'ar' else
                               f'REVISAO_apoio_esquerdo_{posture}_v6']
        evaluate(rig, idle)
        signature = local_signature(rig)
        base = snapshot(rig)
        hands = {s: (rig.matrix_world @ rig.pose.bones[f'SKEL_{s}_Hand'].matrix).copy() for s in ('R', 'L')}
        poles = {s: rig.matrix_world @ rig.pose.bones[f'SKEL_{s}_Forearm'].head for s in ('R', 'L')}
        pivot = hands['R'].translation.copy()
        gun_base = gun.matrix_world.copy()
        min_pitch, max_pitch = limits
        checks = {'max_arm_reach_ratio': 0, 'max_pitch_error_degrees': 0,
                  'max_hand_contact_error_m': 0, 'lower_body_drift_m': 0}
        lower = {b.name: b.matrix.copy() for b in rig.pose.bones
                 if any(t in b.name for t in ('Thigh', 'Calf', 'Foot', 'Toe', 'Pelvis')) or b.name == 'SKEL_ROOT'}
        def apply(frame):
            degrees = min_pitch + frame - 1
            rotation = Quaternion((1, 0, 0), -math.radians(degrees))
            transform = Matrix.Translation(pivot) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-pivot)
            for side in ('R', 'L'):
                expected = transform @ hands[side]
                reach = chain(rig, side, expected.translation, poles[side])
                checks['max_arm_reach_ratio'] = max(checks['max_arm_reach_ratio'], reach)
                rig.pose.bones[f'SKEL_{side}_Hand'].matrix = rig.matrix_world.inverted() @ expected
                bpy.context.view_layer.update()
                actual = rig.matrix_world @ rig.pose.bones[f'SKEL_{side}_Hand'].matrix
                checks['max_hand_contact_error_m'] = max(checks['max_hand_contact_error_m'],
                                                        (actual.translation - expected.translation).length)
            axis = (gun.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
            actual_pitch = math.degrees(math.asin(max(-1, min(1, axis.z))))
            checks['max_pitch_error_degrees'] = max(checks['max_pitch_error_degrees'], abs(actual_pitch - degrees))
            for name, matrix in lower.items():
                checks['lower_body_drift_m'] = max(checks['lower_body_drift_m'],
                                                  (rig.pose.bones[name].matrix.translation - matrix.translation).length)
        action = curve_action(rig, f'MIRA_VERTICAL_{posture}_{short}', base, apply, max_pitch - min_pitch + 1)
        assert signature == local_signature(rig), 'Changed native rest skeleton'
        assert checks['max_pitch_error_degrees'] < .01, checks
        assert checks['lower_body_drift_m'] < .00001 and checks['max_hand_contact_error_m'] < .00001, checks
        identifier = f'cidade_mira_v9_{posture}_{short}'
        converted = forward_action(rig, action)
        dictionary, clips, animations = create_clip_dictionary_template(identifier)
        animation = create_anim_obj(SollumType.ANIMATION)
        animation.name = identifier + '_pitch'; animation.parent = animations
        animation.animation_properties.hash = animation.name
        animation.animation_properties.target_id = rig.data
        animation.animation_properties.action = converted
        clip = create_anim_obj(SollumType.CLIP)
        clip.name = 'mira_vertical'; clip.parent = clips
        clip.clip_properties.hash = clip.name; clip.clip_properties.name = clip.name
        clip.clip_properties.duration = (max_pitch - min_pitch) / 30
        binding = clip.clip_properties.animations.add()
        binding.animation = animation; binding.start_frame = 1; binding.end_frame = max_pitch - min_pitch + 1
        out = HERE / 'exports' / (identifier + '.ycd.xml')
        assert export_ycd(dictionary, str(out))
        # Exported tracks start at their first key. Sollumz otherwise writes
        # Blender's frame 1 as a 1/30 s clip offset and ends past the animation.
        xml = ET.parse(out)
        for item in xml.findall('./Clips/Item'):
            item.find('StartTime').set('value', '0')
            item.find('EndTime').set('value', str((max_pitch-min_pitch)/30))
        xml.write(out,encoding='utf-8',xml_declaration=True)
        evaluate(rig, action, 1 - min_pitch)
        bpy.context.scene.frame_start = 1
        bpy.context.scene.frame_end = max_pitch - min_pitch + 1
        bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 'sources' / f'{posture}_{short}_mira_vertical.blend'))
        report['assets'][identifier] = dict(checks, min_pitch=min_pitch, max_pitch=max_pitch,
                                          frames=max_pitch-min_pitch+1, native_bones=len(signature), source=str(source))
        print('PITCH_ASSET_OK', identifier, json.dumps(checks), flush=True)
(HERE / 'pitch_build.json').write_text(json.dumps(report, indent=2), encoding='utf8')
print('PITCH_BUILD_OK', flush=True)
