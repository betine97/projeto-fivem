import bpy, sys, json, math
from pathlib import Path
from mathutils import Vector
job=Path(sys.argv[sys.argv.index('--')+1])
cfg=json.loads((job.parents[2]/'settings.json').read_text())
sys.path.insert(0,cfg['sollumz'])
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
bpy.ops.wm.open_mainfile(filepath=str(job/'work/variacao.blend'))
scene=bpy.context.scene
objects=bpy.data.collections['10_VARIACAO_TRABALHO'].objects
rig=next(o for o in objects if o.type=='ARMATURE')
action=bpy.data.actions.get('QA_FLEXAO_'+rig.name)
if not action:raise RuntimeError('Ação de teste do rig ausente')
rig.animation_data_create();rig.animation_data.action=action
scene.frame_set(15);bpy.context.view_layer.update()
camera=scene.camera
for name,angle in [('pose_front',0),('pose_side',math.pi/2)]:
 camera.location=(2*math.sin(angle),-2*math.cos(angle),.28)
 camera.rotation_euler=(Vector((0,0,.25))-camera.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(job/'qa'/f'{name}.png');bpy.ops.render.render(write_still=True)
(job/'qa/pose.json').write_text(json.dumps({'action':action.name,'frame':15,'bones':len(rig.data.bones),'views':['pose_front','pose_side'],'visual_review':'pending','in_game_motion':'pending'},indent=2))
print('POSE_RENDERED')
