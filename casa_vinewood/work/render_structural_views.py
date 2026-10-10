"""Inspect the real wall caps and slab depth, without altering the saved scene."""
import bpy
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_fivem_preparada.blend'))
for c in bpy.data.collections:
 if c.name.startswith(('07_','09_','90_','91_')):c.hide_render=True
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=20
s.cycles.use_denoising=True
s.render.resolution_x=1120;s.render.resolution_y=800;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
bpy.ops.object.camera_add(location=(3.8,-.5,.85));cam=bpy.context.object;cam.data.lens=25
# Broad interior lights make the end caps easy to inspect with the native
# materials. These preview-only objects are never saved or exported.
for pos,target,power in [((2.,.2,2.),(1.,4.,1.6),350),((-3.,.2,2.),(-4.,2.8,.7),280)]:
 bpy.ops.object.light_add(type='AREA',location=pos);lamp=bpy.context.object
 lamp.data.energy=power;lamp.data.shape='DISK';lamp.data.size=3
 lamp.rotation_euler=(Vector(target)-lamp.location).to_track_quat('-Z','Y').to_euler()
views=[('espessura_escada',(3.8,-.5,.85),(1.0,4,2.5)),('espessura_paredes',(-5.3,.1,.6),(-1.7,3.3,.6))]
for name,pos,target in views:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam
 s.render.filepath=str(W/(name+'.png'));bpy.ops.render.render(write_still=True)
print('STRUCTURAL_PREVIEWS_OK',flush=True)
