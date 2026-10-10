"""Bake stationary prone, directional crawls and fast crouch on the native rig.

Only copies of Blender sources are saved. Mover tracks are explicit, horizontal
and normalized; idle has no mover tracks. No skeleton names/rest poses change.
"""
import bpy,sys,math,json,ast
from pathlib import Path
from mathutils import Matrix,Vector
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
DEPS=Path('C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps')
sys.path[:0]=[str(DEPS),str(DEPS.parent/'sollumz')]
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
from szio.gta5.cwxml.clipdictionary import YCD
from Sollumz.ycd.ycdimport import combine_sequences_and_build_action_data,create_clip_dictionary_template,create_anim_obj
from Sollumz.sollumz_properties import SollumType
import Sollumz.ycd.ycdexport as exporter
import xml.etree.ElementTree as ET
old_channel=exporter.build_values_channel
def precise(values,uniq_values,indirect_percentage=.1):
    if len(uniq_values)==1:return old_channel(values,uniq_values,indirect_percentage)
    c=exporter.ycdxml.ChannelsList.RawFloat();c.values=values;return c
exporter.build_values_channel=precise
for folder in ('exports','sources','previews'):(HERE/folder).mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE/'sources/deitado_ar_mira_vertical.blend'))
rig=bpy.data.objects['GTA_Personagem_Rig'];scene=bpy.context.scene;scene.render.fps=30
signature=[(b.name,b.bone_properties.tag,b.parent.name if b.parent else None,[list(r) for r in b.matrix_local]) for b in rig.data.bones]
rig.animation_data.action=None
by_tag={b.bone.bone_properties.tag:b for b in rig.pose.bones}
inverse={t:((b.bone.parent.matrix_local.inverted()@b.bone.matrix_local) if b.parent else b.bone.matrix_local).inverted() for t,b in by_tag.items()}
upper={t for t,b in by_tag.items() if b.name=='SKEL_Spine0' or any(a.name=='SKEL_Spine0' for a in b.parent_recursive)}
root=by_tag[0]
def native(path):
    d=YCD.from_xml_file(str(path));a={v.hash:v for v in d.animations}
    return d,a,{h:combine_sequences_and_build_action_data(v) for h,v in a.items()}
crawl=native(BASE/'exports/native_move_crawl.xml')
crouch=native(HERE/'move_aim_strafe_crouch_2h.xml')
unarmed=native(HERE/'move_crouch_proto.xml')
def clipinfo(source,name):
    c=next(c for c in source[0].clips if c.name==f'pack:/{name}.clip')
    bindings=c.animations or [c]
    duration=c.duration if c.animations else c.end_time-c.start_time
    return c,bindings,duration
def apply(source,name,phase,mask=None,reset=True):
    if reset:
        for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
    _,bindings,duration=clipinfo(source,name)
    for binding in bindings:
        anim=source[1][binding.animation_hash];data=source[2][anim.hash]
        time=binding.start_time+(binding.end_time-binding.start_time)*phase
        f=max(0,min(anim.frame_count-1,round(time/anim.duration*(anim.frame_count-1))))
        for tag,tracks in data.items():
            if tag not in by_tag or (mask is not None and tag not in mask):continue
            b=by_tag[tag];inv=inverse[tag];b.rotation_mode='QUATERNION'
            if 0 in tracks:b.location=inv@tracks[0][f]
            if 1 in tracks:b.rotation_quaternion=inv.to_quaternion()@tracks[1][f]
            b.scale=(1,1,1)
    bpy.context.view_layer.update()
    return duration
def key(frame,mover=None):
    for b in rig.pose.bones:
        b.keyframe_insert(data_path='location',frame=frame,group=b.name)
        b.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=b.name)
    if mover is not None:
        root.animation_tracks_mover_location=(*mover,1.0)
        root.animation_tracks_mover_rotation=(1,0,0,0)
        root.keyframe_insert(data_path='animation_tracks_mover_location',frame=frame,group=root.name)
        root.keyframe_insert(data_path='animation_tracks_mover_rotation',frame=frame,group=root.name)
report={'game_tested':False,'skeleton_unchanged':True,'assets':{},'clips':{}}
def newclip(dictionary,clips,animations,name,frames,build,motion=False):
    rig.animation_data.action=None
    for frame in range(frames):
        phase=frame/(frames-1)
        mover=build(phase)
        key(frame+1,mover if motion else None)
    action=rig.animation_data.action;action.name=name;action.use_fake_user=True
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for p in curve.keyframe_points:p.interpolation='LINEAR'
    a=create_anim_obj(SollumType.ANIMATION);a.name=dictionary.name+'_'+name;a.parent=animations
    a.animation_properties.hash=a.name;a.animation_properties.target_id=rig.data;a.animation_properties.action=action
    c=create_anim_obj(SollumType.CLIP);c.name=name;c.parent=clips
    c.clip_properties.hash=name;c.clip_properties.name=name;c.clip_properties.duration=(frames-1)/30
    binding=c.clip_properties.animations.add();binding.animation=a;binding.start_frame=1;binding.end_frame=frames
    report['clips'][name]={'frames':frames,'duration':(frames-1)/30,'mover':motion}
    return action
def export(d):
    out=HERE/'exports'/(d.name+'.ycd.xml');assert exporter.export_ycd(d,str(out))
    xml=ET.parse(out)
    for c in xml.findall('./Clips/Item'):
        c.find('StartTime').set('value','0')
        c.find('EndTime').set('value',str(report['clips'][c.findtext('Name').removeprefix('pack:/')]['duration']))
    xml.write(out,encoding='utf8',xml_declaration=True)
    report['assets'][d.name]=[c.name for c in d.children[0].children]
    print('LOCOMOTION_XML_OK',d.name,flush=True)
d,clips,anims=create_clip_dictionary_template('cidade_deitado_move_v11')
def idle(phase):apply(crawl,'onfront_fwd',.1)
newclip(d,clips,anims,'parado',31,idle)
for name,axis in [('fwd',(0,1)),('bwd',(0,-1)),('left',(-1,0)),('right',(1,0))]:
    source='onfront_bwd' if name=='bwd' else 'onfront_fwd'
    frames=32 if name=='bwd' else 28;duration=(frames-1)/30
    speed=.48 if name=='bwd' else (.42 if name in ('left','right') else .65)
    def build(phase,name=name,source=source,axis=axis,duration=duration,speed=speed):
        apply(crawl,source,phase)
        if name in ('left','right'):
            # Reach outward with alternating knee/forearm support while the
            # pelvis keeps the same native stride for the rifle aim mask.
            sign=axis[0]
            for side,offset in [('L',0),('R',math.pi)]:
                swing=math.sin(phase*2*math.pi+offset)
                for part,amount in [('Thigh',.14),('UpperArm',.12)]:
                    b=rig.pose.bones[f'SKEL_{side}_{part}']
                    b.rotation_quaternion=b.rotation_quaternion@Matrix.Rotation(sign*amount*swing,4,'Y').to_quaternion()
            bpy.context.view_layer.update()
        return (axis[0]*duration*speed*phase,axis[1]*duration*speed*phase)
    newclip(d,clips,anims,'rastejar_'+name,frames,build,True)
export(d)
mapping={'fwd':'run_fwd_0_loop','bwd':'run_bwd_180_loop','left':'run_bwd_-90_loop','right':'run_fwd_90_loop'}
axes={'fwd':(0,1),'bwd':(0,-1),'left':(-1,0),'right':(1,0)}
d,clips,anims=create_clip_dictionary_template('cidade_agachado_move_v11')
for armed in (False,True):
    for direction,source in mapping.items():
        _,_,duration=clipinfo(crouch,source);frames=round(duration*30)+1;duration=(frames-1)/30
        speed=1.75 if direction=='fwd' else 1.4;axis=axes[direction]
        name='rapido_'+('armado_' if armed else 'livre_')+direction
        def build(phase,source=source,armed=armed,axis=axis,duration=duration,speed=speed):
            apply(crouch,source,phase)
            if not armed:apply(unarmed,'run',phase,upper,False)
            return (axis[0]*duration*speed*phase,axis[1]*duration*speed*phase)
        newclip(d,clips,anims,name,frames,build,True)
export(d)
assert signature==[(b.name,b.bone_properties.tag,b.parent.name if b.parent else None,[list(r) for r in b.matrix_local]) for b in rig.data.bones]
rig.animation_data.action=bpy.data.actions['parado'];scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'sources/posturas_direcionais_v11.blend'))
(HERE/'build_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('LOCOMOTION_BUILD_OK',len(report['clips']),flush=True)
