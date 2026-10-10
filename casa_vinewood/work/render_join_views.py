import bpy,sys
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
tag=args[0] if args else 'antes'
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_encaixada.blend'))
for c in bpy.data.collections:
 c.hide_render=c.name.startswith(('07_','09_','90_','91_'))
for o in bpy.data.objects:
 if o.name.startswith('Vidros'):o.hide_render=True
s=bpy.context.scene
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL'
s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH'
s.render.resolution_x=1300;s.render.resolution_y=950;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.display.shading.background_type='WORLD';s.world.color=(.35,.65,.9)
views=[((.2,-9,.6),(0,-1,3.5)),((1,-9,.55),(-9,-11,3.1)),((3,-9,1.0),(6.4,-11,3.4))]
for i,(pos,target) in enumerate(views):
 bpy.ops.object.camera_add(location=pos);cam=bpy.context.object;cam.data.lens=24
 cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam
 s.render.filepath=str(W/'work'/f'juntas_{tag}_{i}.png');bpy.ops.render.render(write_still=True)
print('JOIN_VIEWS_RENDERED',tag,flush=True)
