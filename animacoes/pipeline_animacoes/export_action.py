"""Export an animator's action through an isolated visual bake of the native rig.

Example: blender -b --python-exit-code 1 --python export_action.py --
  --source sources/ajoelhado_ar.blend --action MIRA_ajoelhado_ar
  --dictionary cidade_nova_anim --clip mira --start 1 --end 30
No source blend or running resource is modified.
"""
import bpy, sys, json, math, argparse
from pathlib import Path
from mathutils import Matrix

HERE=Path(__file__).resolve().parent
DEPS=Path(r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
sys.path[:0]=[str(DEPS),str(DEPS.parent/'sollumz')]
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
from Sollumz.ycd.ycdimport import create_clip_dictionary_template,create_anim_obj
from Sollumz.ycd.ycdexport import export_ycd
from Sollumz.sollumz_properties import SollumType
from szio.gta5.cwxml.clipdictionary import YCD

parser=argparse.ArgumentParser()
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--action',required=True)
parser.add_argument('--dictionary',required=True)
parser.add_argument('--clip',required=True)
parser.add_argument('--start',type=int,default=1)
parser.add_argument('--end',type=int,required=True)
parser.add_argument('--fps',type=int,default=30)
parser.add_argument('--turn-z',type=float,default=180,help='Native facing conversion used by the current studies')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
assert args.end>args.start and args.fps>0
assert all(name.replace('_','').isalnum() for name in (args.dictionary,args.clip)), 'Use letters, digits and underscore'
source=args.source if args.source.is_absolute() else HERE/args.source
bpy.ops.wm.open_mainfile(filepath=str(source.resolve()))
rig=bpy.data.objects['GTA_Personagem_Rig']
reference=json.loads((HERE/'reports/skeleton.json').read_text())['native_bones']
assert len(rig.data.bones)==len(reference), 'Native bone count changed'
for expected in reference:
    bone=rig.data.bones.get(expected['name'])
    assert bone and bone.bone_properties.tag==expected['tag'], 'Native name/tag mismatch'
    assert (bone.parent.name if bone.parent else None)==expected['parent'], 'Native parent mismatch'
    assert max(abs(bone.matrix_local[i][j]-expected['rest'][i][j]) for i in range(4) for j in range(4))<1e-5, 'Native rest pose changed'
assert max(abs(x-1) for x in rig.scale)<1e-5, 'Do not scale the export rig'
action=bpy.data.actions[args.action]
rig.animation_data_create();rig.animation_data.action=action
scene=bpy.context.scene;scene.render.fps=args.fps
baked=rig.copy();baked.data=rig.data.copy();baked.name='EXPORT_RIG_BAKED'
bpy.context.collection.objects.link(baked)
baked.animation_data_clear()
for bone in baked.pose.bones:
    for constraint in list(bone.constraints):
        bone.constraints.remove(constraint)
    bone.rotation_mode='QUATERNION'
for constraint in list(baked.constraints):
    baked.constraints.remove(constraint)
turn=Matrix.Rotation(math.radians(args.turn_z),4,'Z')
for output_frame,source_frame in enumerate(range(args.start,args.end+1),1):
    scene.frame_set(source_frame);bpy.context.view_layer.update()
    evaluated=rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
    for bone in baked.pose.bones:
        matrix=evaluated.pose.bones[bone.name].matrix.copy()
        # Turning the root also rotates all children; applying to every evaluated
        # bone preserves local rotations rather than counter-rotating the arms.
        bone.matrix=turn@matrix
        bpy.context.view_layer.update()
        assert all(math.isfinite(v) for row in bone.matrix for v in row), 'Nonfinite pose matrix'
        assert max(abs(v-1) for v in bone.scale)<.001, 'Bone scaling/stretching is not allowed'
        bone.keyframe_insert(data_path='location',frame=output_frame,group=bone.name)
        bone.keyframe_insert(data_path='rotation_quaternion',frame=output_frame,group=bone.name)
bake_action=baked.animation_data.action
dictionary,clips,animations=create_clip_dictionary_template(args.dictionary)
animation=create_anim_obj(SollumType.ANIMATION);animation.name=args.clip+'_baked';animation.parent=animations
animation.animation_properties.hash=animation.name
animation.animation_properties.target_id=baked.data
animation.animation_properties.action=bake_action
clip=create_anim_obj(SollumType.CLIP);clip.name=args.clip;clip.parent=clips
clip.clip_properties.hash=args.clip;clip.clip_properties.name=args.clip
clip.clip_properties.duration=(args.end-args.start)/args.fps
binding=clip.clip_properties.animations.add();binding.animation=animation;binding.start_frame=1;binding.end_frame=args.end-args.start+1
out=HERE/'exports'/(args.dictionary+'.ycd.xml')
assert export_ycd(dictionary,str(out))
assert len(YCD.from_xml_file(str(out)).clips)==1
print('VISUAL_BAKE_EXPORT_OK',out)
