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
 graph=bpy.context.evaluated_depsgraph_get()
 bounds=[o.evaluated_get(graph).matrix_world @ Vector(c) for o in objects if o.type=='MESH' for c in o.evaluated_get(graph).bound_box]
 center=sum(bounds,Vector())/len(bounds)
 camera.location=center+Vector((3*math.sin(angle),-3*math.cos(angle),0))
 camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
 view=camera.rotation_euler.to_matrix().transposed()
 projected=[view @ (point-center) for point in bounds]
 xmin,xmax=min(v.x for v in projected),max(v.x for v in projected)
 ymin,ymax=min(v.y for v in projected),max(v.y for v in projected)
 offset=camera.rotation_euler.to_matrix() @ Vector(((xmin+xmax)/2,(ymin+ymax)/2,0))
 camera.location+=offset
 camera.data.ortho_scale=max((xmax-xmin)/(scene.render.resolution_x/scene.render.resolution_y),ymax-ymin)*1.18
 scene.render.filepath=str(job/'qa'/f'{name}.png');bpy.ops.render.render(write_still=True)
(job/'qa/pose.json').write_text(json.dumps({'action':action.name,'frame':15,'bones':len(rig.data.bones),'views':['pose_front','pose_side'],'visual_review':'pending','in_game_motion':'pending'},indent=2))
print('POSE_RENDERED')
