import bpy
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_fivem_preparada.blend'))
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16
s.render.resolution_x=1120;s.render.resolution_y=800;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
bpy.ops.object.camera_add(location=(3.8,-.5,.85));cam=bpy.context.object;cam.data.lens=25
views=[('acabamento_escada',(3.8,-.5,.85),(1.0,4,2.5)),('acabamento_janela',(-6.3,.3,3.75),(-9.0,1.25,4.65))]
for name,pos,target in views:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam
 s.render.filepath=str(W/(name+'.png'));bpy.ops.render.render(write_still=True)
print('FINISHING_PREVIEWS_OK',flush=True)
