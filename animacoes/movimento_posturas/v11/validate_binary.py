"""Decode installed-format clips; verify actual mover tracks and rifle mask.

No simulated physics claim: these checks measure the binary animation data.
"""
import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
DEPS=Path('C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps')
sys.path[:0]=[str(DEPS),str(DEPS.parent/'sollumz')]
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
from szio.gta5.cwxml.clipdictionary import YCD
from Sollumz.ycd.ycdimport import combine_sequences_and_build_action_data
bpy.ops.wm.open_mainfile(filepath=str(HERE/'sources/posturas_direcionais_v11.blend'))
rig=bpy.data.objects['GTA_Personagem_Rig'];scene=bpy.context.scene
by_tag={b.bone_properties.tag:b for b in rig.data.bones}
ordered=[]
def visit(b):
    ordered.append(b)
    for child in b.children:visit(child)
visit(rig.data.bones['SKEL_ROOT'])
upper=[b for b in ordered if b.name=='SKEL_Spine0' or any(a.name=='SKEL_Spine0' for a in b.parent_recursive)]
def local(data,b,f):
    tracks=data[b.bone_properties.tag]
    return Matrix.LocRotScale(tracks[0][f],tracks[1][f],Vector((1,1,1)))
def matrices(data,f):
    out={}
    for b in ordered:out[b.name]=(out[b.parent.name] if b.parent else Matrix.Identity(4))@local(data,b,f)
    return out
clips={};report={'game_tested':False,'assets':{},'rifle_mask':{}}
for identifier in ('cidade_deitado_move_v11','cidade_agachado_move_v11'):
    binary=YCD.from_xml_file(str(HERE/'exports'/(identifier+'.roundtrip.xml')))
    original=YCD.from_xml_file(str(HERE/'exports'/(identifier+'.ycd.xml')))
    source={a.hash:combine_sequences_and_build_action_data(a) for a in original.animations}
    decoded={a.hash:a for a in binary.animations};result={}
    for clip in binary.clips:
        name=clip.name.removeprefix('pack:/');a=decoded[clip.animation_hash]
        data=combine_sequences_and_build_action_data(a);clips[name]=(data,a.frame_count)
        assert set(data)==set(by_tag) and abs(clip.start_time)<1e-7 and abs(clip.end_time-a.duration)<1e-5
        error=0.0
        for tag,tracks in data.items():
            for track,values in tracks.items():
                for frame,v in enumerate(values):
                    assert all(math.isfinite(x) for x in v)
                    error=max(error,max(abs(x-y) for x,y in zip(v,source[a.hash][tag][track][frame])))
        assert error<.002,(name,error)
        if name=='parado':
            assert 5 not in data[0] and 6 not in data[0],'Idle contains mover extraction data'
            variation=max(max(abs(x-y) for x,y in zip(values[f],values[0])) for tracks in data.values() for values in tracks.values() for f in range(a.frame_count))
            assert variation<1e-7,'Idle still animates a crawl'
            result[name]={'frames':a.frame_count,'mover_tracks':False,'maximum_bone_variation':variation}
        else:
            mover=data[0][5];rotation=data[0][6];delta=mover[-1]-mover[0]
            axis={'fwd':Vector((0,1,0)),'bwd':Vector((0,-1,0)),
                  'left':Vector((-1,0,0)),'right':Vector((1,0,0))}[name.split('_')[-1]]
            assert delta.dot(axis)>.1 and (delta-axis*delta.dot(axis)).length<1e-5
            assert all(abs(v.z-1)<1e-6 for v in mover)
            assert all(abs(q.w-1)<1e-6 and abs(q.x)+abs(q.y)+abs(q.z)<1e-6 for q in rotation)
            expected=.48 if name=='rastejar_bwd' else (.42 if name in ('rastejar_left','rastejar_right') else .65) if name.startswith('rastejar') else (1.75 if name.endswith('fwd') else 1.4)
            speed=delta.length/a.duration;assert abs(speed-expected)<.001
            result[name]={'frames':a.frame_count,'displacement_m':list(delta),'speed_m_s':speed,'max_channel_error':error}
    report['assets'][identifier]={'clips':result,'sha256':hashlib.sha256((HERE/'exports'/(identifier+'.ycd')).read_bytes()).hexdigest()}
# Recompose rifle upper-body samples over EVERY decoded lateral/crawl frame.
# The forward grid applies to lateral motion: lateral reach changes limbs, not
# the pelvis/root transforms; those remain the forward parent's native stride.
for short in ('ar','ak'):
    reference=YCD.from_xml_file(str(BASE/'exports'/f'cidade_mira_v9_deitado_{short}.roundtrip.xml'))
    ref=combine_sequences_and_build_action_data(reference.animations[0])
    expected=[matrices(ref,f) for f in range(44)]
    grid=YCD.from_xml_file(str(BASE/'exports'/f'cidade_rastejar_v9_{short}.roundtrip.xml'))
    gd={a.hash:combine_sequences_and_build_action_data(a) for a in grid.animations}
    gc={c.name.removeprefix('pack:/'):gd[c.animation_hash] for c in grid.clips}
    error=0.0;samples=0
    for direction in ('fwd','bwd','left','right'):
        data,frames=clips['rastejar_'+direction]
        overlay=gc['mira_rastejar_'+('bwd' if direction=='bwd' else 'fwd')]
        for f in range(frames):
            parent=matrices(data,f)[rig.data.bones['SKEL_Spine0'].parent.name]
            for column in range(44):
                out={}
                for b in upper:
                    prior=parent if b.name=='SKEL_Spine0' else out[b.parent.name]
                    out[b.name]=prior@local(overlay,b,f*44+column)
                for hand in ('SKEL_R_Hand','SKEL_L_Hand'):
                    error=max(error,(out[hand].translation-expected[column][hand].translation).length)
                samples+=1
    assert error<.0001,(short,error)
    report['rifle_mask'][short]={'samples':samples,'max_hand_error_m':error}
(HERE/'binary_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('V11_BINARY_OK',json.dumps(report),flush=True)
if '--render' in sys.argv:
    rig.animation_data.action=None
    for obj in bpy.data.objects:
        if obj.name.startswith('w_ar_'):
            for child in [obj,*obj.children_recursive]:child.hide_render=True
    # The ped's world root is one metre above the ground in GTA. Move only the
    # preview rig; source skeleton/rest transforms are untouched.
    rig.location.z+=1
    scene.render.engine='CYCLES';scene.cycles.samples=8
    scene.render.resolution_x=850;scene.render.resolution_y=650;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    def apply(data,f):
        for b in rig.pose.bones:
            bone=b.bone;inverse=((bone.parent.matrix_local.inverted()@bone.matrix_local) if bone.parent else bone.matrix_local).inverted()
            tracks=data[bone.bone_properties.tag];b.location=inverse@tracks[0][f]
            b.rotation_mode='QUATERNION';b.rotation_quaternion=inverse.to_quaternion()@tracks[1][f]
        bpy.context.view_layer.update()
    for name in ('parado','rastejar_left','rapido_livre_fwd','rapido_armado_left'):
        data,frames=clips[name];apply(data,frames//2)
        points=[rig.matrix_world@b.head for b in rig.pose.bones if b.name in ('SKEL_Head','SKEL_L_Foot','SKEL_R_Foot','SKEL_Pelvis')]
        focus=sum(points,Vector())/len(points)
        scene.camera.location=focus+Vector((2.6,-3.2,1.8))
        scene.camera.rotation_euler=(focus-scene.camera.location).to_track_quat('-Z','Y').to_euler()
        scene.camera.data.type='ORTHO';scene.camera.data.ortho_scale=2.9
        scene.render.filepath=str(HERE/'previews'/(name+'.png'))
        bpy.ops.render.render(write_still=True)
