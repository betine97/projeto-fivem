"""Compensate native crawl pelvis motion while sampling authored rifle aim.

The native primary task still owns root/mover and legs. The secondary clip is
sampled on a pitch/stride grid and owns only the spine and its descendants.
"""
import bpy,sys,ast,json,math
from pathlib import Path
from mathutils import Matrix,Vector
HERE=Path(__file__).resolve().parent
DEPS=Path('C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps')
sys.path[:0]=[str(DEPS),str(DEPS.parent/'sollumz'),str(HERE.parent/'work')]
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
from szio.gta5.cwxml.clipdictionary import YCD
from Sollumz.ycd.ycdimport import combine_sequences_and_build_action_data,create_clip_dictionary_template,create_anim_obj
from Sollumz.sollumz_properties import SollumType
import Sollumz.ycd.ycdexport as exporter
from export_orientation import forward_action
old_channel=exporter.build_values_channel
def precise(values,uniq_values,indirect_percentage=.1):
    if len(uniq_values)==1:return old_channel(values,uniq_values,indirect_percentage)
    c=exporter.ycdxml.ChannelsList.RawFloat();c.values=values;return c
exporter.build_values_channel=precise
import xml.etree.ElementTree as ET
tree=ast.parse((HERE.parent/'pipeline_animacoes/build.py').read_text(encoding='utf8'))
helpers={'evaluate','snapshot','restore','key_all','curve_action'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in helpers],type_ignores=[]),'helpers','exec'),globals())
native=YCD.from_xml_file(str(HERE/'exports/native_move_crawl.xml'))
native_anims={a.hash:a for a in native.animations}
native_data={h:combine_sequences_and_build_action_data(a) for h,a in native_anims.items()}
report={'game_tested':False,'rows':{},'assets':{}}
for short in ('ar','ak'):
    bpy.ops.wm.open_mainfile(filepath=str(HERE/'sources'/f'deitado_{short}_mira_vertical.blend'))
    rig=bpy.data.objects['GTA_Personagem_Rig'];scene=bpy.context.scene
    gun=bpy.data.objects['w_ar_'+('carbinerifle' if short=='ar' else 'assaultrifle')]
    by_tag={b.bone.bone_properties.tag:b for b in rig.pose.bones}
    rest_inverse={t:((b.bone.parent.matrix_local.inverted()@b.bone.matrix_local) if b.parent else b.bone.matrix_local).inverted()
                  for t,b in by_tag.items()}
    converted=forward_action(rig,bpy.data.actions[f'MIRA_VERTICAL_deitado_{short}'])
    targets=[]
    for frame in range(1,45):
        evaluate(rig,converted,frame)
        targets.append({'basis':snapshot(rig),'spine':rig.pose.bones['SKEL_Spine0'].matrix.copy()})
    identifier=f'cidade_rastejar_v9_{short}'
    dictionary,clips,animations=create_clip_dictionary_template(identifier)
    records={}
    for direction in ('fwd','bwd'):
        clip=next(c for c in native.clips if c.name==f'pack:/onfront_{direction}.clip')
        rows=round(clip.duration*30)+1;report['rows'][direction]=rows
        parents=[]
        rig.animation_data.action=None
        for row in range(rows):
            for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
            for binding in clip.animations:
                anim=native_anims[binding.animation_hash];data=native_data[anim.hash]
                time=binding.start_time+(binding.end_time-binding.start_time)*row/(rows-1)
                frame=max(0,min(anim.frame_count-1,round(time/anim.duration*(anim.frame_count-1))))
                for tag,tracks in data.items():
                    if tag not in by_tag:continue
                    b=by_tag[tag];inverse=rest_inverse[tag]
                    if 0 in tracks:b.location=inverse@tracks[0][frame]
                    if 1 in tracks:b.rotation_mode='QUATERNION';b.rotation_quaternion=inverse.to_quaternion()@tracks[1][frame]
            bpy.context.view_layer.update()
            parents.append(rig.pose.bones['SKEL_Spine0'].parent.matrix.copy())
        # Insert precomputed curves in bulk. keyframe_insert on all 98 bones
        # repeatedly invalidates Blender's dependency graph for this long grid.
        spine=rig.pose.bones['SKEL_Spine0']
        rest_inverse_spine=(spine.bone.parent.matrix_local.inverted()@spine.bone.matrix_local).inverted()
        spine_frames=[(rest_inverse_spine@parent.inverted()@target['spine']).decompose() for parent in parents for target in targets]
        action_name=f'MIRA_RASTEJAR_{direction}_{short}'
        rig.animation_data.action=None;restore(rig,targets[0]['basis']);key_all(rig,1)
        action=rig.animation_data.action;action.name=action_name;action.use_fake_user=True
        bag=action.layers[0].strips[0].channelbags[0]
        decomposed={name:[t['basis'][name].decompose() for t in targets] for name in targets[0]['basis']}
        for curve in bag.fcurves:
            name=curve.group.name;part=1 if curve.data_path.endswith('rotation_quaternion') else 0
            values=[(spine_frames[i] if name=='SKEL_Spine0' else decomposed[name][i%44])[part][curve.array_index] for i in range(rows*44)]
            if max(values)-min(values)<1e-7:points=[(1,values[0]),(rows*44,values[0])]
            else:points=list(enumerate(values,1))
            curve.keyframe_points.clear();curve.keyframe_points.add(len(points))
            curve.keyframe_points.foreach_set('co',[v for point in points for v in point])
            for point in curve.keyframe_points:point.interpolation='LINEAR'
            curve.update()
        print('CRAWL_GRID_CURVES',identifier,direction,rows*44,flush=True)
        animation=create_anim_obj(SollumType.ANIMATION);animation.name=f'{identifier}_{direction}'
        animation.parent=animations;animation.animation_properties.hash=animation.name
        animation.animation_properties.target_id=rig.data;animation.animation_properties.action=action
        out_clip=create_anim_obj(SollumType.CLIP);out_clip.name=f'mira_rastejar_{direction}';out_clip.parent=clips
        out_clip.clip_properties.hash=out_clip.name;out_clip.clip_properties.name=out_clip.name
        out_clip.clip_properties.duration=(rows*44-1)/30
        binding=out_clip.clip_properties.animations.add();binding.animation=animation
        binding.start_frame=1;binding.end_frame=rows*44
        records[direction]={'rows':rows,'frames':rows*44,'action':action_name,'parents':[[list(r) for r in m] for m in parents]}
    out=HERE/'exports'/(identifier+'.ycd.xml')
    assert exporter.export_ycd(dictionary,str(out))
    xml=ET.parse(out)
    for item in xml.findall('./Clips/Item'):
        direction=item.find('Name').text.split('_')[-1]
        item.find('StartTime').set('value','0')
        item.find('EndTime').set('value',str((records[direction]['frames']-1)/30))
    xml.write(out,encoding='utf-8',xml_declaration=True)
    evaluate(rig,bpy.data.actions[f'MIRA_VERTICAL_deitado_{short}'],9)
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'sources'/f'rastejar_mira_{short}.blend'))
    report['assets'][identifier]=records
    print('CRAWL_AIM_BUILD_OK',identifier,{d:r['frames'] for d,r in records.items()},flush=True)
(HERE/'crawl_grid.json').write_text(json.dumps(report,indent=2),encoding='utf8')
