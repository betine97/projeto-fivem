"""Decode the packaged YCD back onto native rest bones and compare all frames.

Optional --render produces previews of DECODED game assets, without live FiveM.
"""
import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
HERE=Path(__file__).resolve().parent
DEPS=Path(r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps')
sys.path[:0]=[str(DEPS),str(DEPS.parent/'sollumz')]
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
from szio.gta5.cwxml.clipdictionary import YCD
from Sollumz.ycd.ycdimport import combine_sequences_and_build_action_data
from mathutils.bvhtree import BVHTree
posture=sys.argv[sys.argv.index('--')+1]
folder=HERE/(posture+'_v6')
report=json.loads((folder/'ajuste.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(folder/report['blend_file']))
rig=bpy.data.objects['GTA_Personagem_Rig'];gun=bpy.data.objects['w_ar_assaultrifle'];scene=bpy.context.scene
identifier=f'cidade_{posture}_v6_ak'
source=YCD.from_xml_file(str(folder/(identifier+'.ycd.xml')))
binary=YCD.from_xml_file(str(folder/(identifier+'.roundtrip.xml')))
def clips_by_name(dictionary):
    anims={anim.hash:anim for anim in dictionary.animations}
    return {clip.name.split('/')[-1]:(clip,anims[clip.animation_hash]) for clip in dictionary.clips}
original=clips_by_name(source);decoded=clips_by_name(binary)
assert set(original)==set(decoded)
by_tag={b.bone.bone_properties.tag:b for b in rig.pose.bones}
native=json.loads((HERE.parent/'reports/skeleton.json').read_text())['native_bones']
assert len(by_tag)==len(native)==98
for expected in native:
    b=rig.data.bones[expected['name']]
    assert b.bone_properties.tag==expected['tag']
    assert (b.parent.name if b.parent else None)==expected['parent']
    assert max(abs(b.matrix_local[i][j]-expected['rest'][i][j]) for i in range(4) for j in range(4))<1e-5
rest_inverse={tag:(bone.bone.parent.matrix_local.inverted()@bone.bone.matrix_local if bone.parent else bone.bone.matrix_local).inverted() for tag,bone in by_tag.items()}
def apply_data(data,frame):
    rig.animation_data.action=None
    for tag,tracks in data.items():
        bone=by_tag[tag];inverse=rest_inverse[tag]
        bone.location=inverse@tracks[0][frame]
        bone.rotation_mode='QUATERNION'
        bone.rotation_quaternion=inverse.to_quaternion()@tracks[1][frame]
        bone.scale=(1,1,1)
    bpy.context.view_layer.update()
    # Bring GTA's facing conversion back into the Blender studio for comparison.
    root=rig.pose.bones['SKEL_ROOT'];root.matrix=Matrix.Rotation(-math.pi,4,'Z')@root.matrix
    bpy.context.view_layer.update()
def snap():return {b.name:b.matrix.copy() for b in rig.pose.bones}
idle=bpy.data.actions[report['idle_action']]
rig.animation_data.action=idle;scene.frame_set(1);bpy.context.view_layer.update()
idle_matrices=snap();idle_gun=gun.matrix_world.copy()
checks={'game_tested':False,'binary_decode':True,'native_rest_preserved':True,'clips':{},'max_pose_matrix_error':0,'max_binary_channel_error':0,'endpoint_pose_error':0,'max_barrel_vertical_component':0}
for name,(clip,anim) in decoded.items():
    original_clip,original_anim=original[name]
    assert anim.frame_count==original_anim.frame_count
    assert abs(clip.start_time)<1e-7 and abs(clip.end_time-anim.duration)<1e-6
    assert 0<clip.end_time and abs(clip.rate-original_clip.rate)<1e-5
    data=combine_sequences_and_build_action_data(anim)
    original_data=combine_sequences_and_build_action_data(original_anim)
    assert set(data)==set(by_tag)==set(original_data)
    for tag,tracks in data.items():
        assert set(tracks)=={0,1}
        for frame in range(anim.frame_count):
            assert all(math.isfinite(x) for x in tracks[0][frame]) and all(math.isfinite(x) for x in tracks[1][frame])
            assert abs(tracks[1][frame].magnitude-1)<.002,(name,tag,by_tag[tag].name,frame,list(tracks[1][frame]),list(original_data[tag][1][frame]))
            position_error=(tracks[0][frame]-original_data[tag][0][frame]).length
            q1,q2=tracks[1][frame],original_data[tag][1][frame]
            rotation_error=min((Vector(q1)-Vector(q2)).length,(Vector(q1)+Vector(q2)).length)
            checks['max_binary_channel_error']=max(checks['max_binary_channel_error'],position_error,rotation_error)
    action_name={'mira':report['idle_action'],'recuo':report['recoil_action'],'recarga':report['reload_action'],'levantar_deitado':f'REVISAO_saida_{posture}_v6'}[name]
    action=bpy.data.actions[action_name]
    for frame in range(anim.frame_count):
        rig.animation_data.action=action;scene.frame_set(frame+1);bpy.context.view_layer.update();expected=snap()
        apply_data(data,frame)
        error=max(abs(b.matrix[i][j]-expected[b.name][i][j]) for b in rig.pose.bones for i in range(4) for j in range(4))
        checks['max_pose_matrix_error']=max(checks['max_pose_matrix_error'],error)
        if name!='levantar_deitado':
            forward=gun.matrix_world.to_3x3()@Vector((1,0,0))
            checks['max_barrel_vertical_component']=max(checks['max_barrel_vertical_component'],abs(forward.normalized().z))
            if frame in (0,anim.frame_count-1):
                checks['endpoint_pose_error']=max(checks['endpoint_pose_error'],max(abs(b.matrix[i][j]-idle_matrices[b.name][i][j]) for b in rig.pose.bones for i in range(4) for j in range(4)))
    checks['clips'][name]={'frames':anim.frame_count,'starts_at_zero':True,'ends_inside_animation':True}
assert checks['max_pose_matrix_error']<.002 and checks['max_binary_channel_error']<.002,checks
assert checks['endpoint_pose_error']<.002 and checks['max_barrel_vertical_component']<.002,checks

def crossing_check():
    dep=bpy.context.evaluated_depsgraph_get();verts=[];faces=[]
    for obj in gun.children_recursive:
        if obj.type!='MESH' or obj.hide_render:continue
        ev=obj.evaluated_get(dep);mesh=ev.to_mesh();mesh.calc_loop_triangles();start=len(verts)
        verts.extend(ev.matrix_world@v.co for v in mesh.vertices)
        faces.extend(tuple(start+i for i in tri.vertices) for tri in mesh.loop_triangles);ev.to_mesh_clear()
    weapon_bvh=BVHTree.FromPolygons(verts,faces,all_triangles=True);count=0
    for obj in bpy.data.objects:
        if obj.type!='MESH' or not obj.vertex_groups or obj.hide_render:continue
        ev=obj.evaluated_get(dep);mesh=ev.to_mesh();mesh.calc_loop_triangles()
        selected={v.index for v in mesh.vertices if sum(g.weight for g in v.groups if obj.vertex_groups[g.group].name.startswith(('SKEL_L_Hand','SKEL_L_Finger')))>.5}
        hand_faces=[tuple(tri.vertices) for tri in mesh.loop_triangles if all(i in selected for i in tri.vertices)]
        if hand_faces:
            hand_bvh=BVHTree.FromPolygons([ev.matrix_world@v.co for v in mesh.vertices],hand_faces,all_triangles=True)
            count+=len(weapon_bvh.overlap(hand_bvh))
        ev.to_mesh_clear()
    return count
checks['hand_crossings']={}
for name,frames in [('mira',[0]),('recuo',[4,9,29]),('recarga',[66])]:
    data=combine_sequences_and_build_action_data(decoded[name][1])
    for frame in frames:
        apply_data(data,frame);crossings=crossing_check()
        checks['hand_crossings'][f'{name}_{frame+1}']=crossings
        assert crossings==0,(posture,name,frame,crossings)
checks['binary_sha256']=hashlib.sha256((folder/(identifier+'.ycd')).read_bytes()).hexdigest()
checks['source_xml_sha256']=hashlib.sha256((folder/(identifier+'.ycd.xml')).read_bytes()).hexdigest()
(folder/'binary_validation.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
if '--render' in sys.argv:
    scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.cycles.samples=32;scene.render.image_settings.file_format='PNG'
    previews=[('01_apoio_lateral','mira',0,Vector((-.65,-.03,.20)),.55),
              ('02_apoio_frente','mira',0,Vector((.08,-.65,.11)),.55),
              ('03_apos_recarga','recarga',66,Vector((.65,.04,.24)),.55),
              ('04_durante_tiro','recuo',4,Vector((-.65,-.03,.20)),.55)]
    for label,name,frame,offset,scale in previews:
        apply_data(combine_sequences_and_build_action_data(decoded[name][1]),frame)
        focus=gun.matrix_world@Vector((.19,0,.005))
        scene.camera.location=focus+offset
        scene.camera.rotation_euler=(focus-scene.camera.location).to_track_quat('-Z','Y').to_euler()
        scene.camera.data.type='ORTHO';scene.camera.data.ortho_scale=scale;scene.camera.data.clip_start=.001
        scene.render.filepath=str(folder/(label+'.png'));bpy.ops.render.render(write_still=True)
print('V6_BINARY_NATIVE_POSES_OK',posture,json.dumps(checks))
