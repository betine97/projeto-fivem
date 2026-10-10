import bpy,math
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_fivem_preparada.blend'))
s=bpy.context.scene
for o in list(bpy.data.objects):
 if o.type in ['CAMERA','LIGHT']:bpy.data.objects.remove(o,do_unlink=True)
for c in bpy.data.collections:
 if c.name.startswith(('06_','07_','09_','90_')):c.hide_render=True
for o in bpy.data.objects:
 if o.name.startswith('Vidros'):o.hide_render=True
bpy.ops.object.camera_add(location=(36,-45,40));cam=bpy.context.object;cam.rotation_euler=(Vector((2,-2,2.5))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=40;s.camera=cam
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH';s.display.shading.background_type='WORLD';s.world.color=(.16,.17,.19)
s.render.resolution_x=1400;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(W/'interior_encaixe_revisado.png')
bpy.ops.render.render(write_still=True)
print('REVISED_PREVIEW_OK')
