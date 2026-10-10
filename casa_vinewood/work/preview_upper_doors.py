"""Render the marked floor boundary and placed wooden door details."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_fivem_preparada.blend'));s=bpy.context.scene
for c in bpy.data.collections:
 c.hide_render=c.name.startswith(('07_','09_','11_','13_','90_','91_'))
 c.hide_viewport=c.name.startswith(('07_','09_','11_','13_','90_','91_'))
s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True
s.render.resolution_x=1200;s.render.resolution_y=950;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
for pos,power,size in [((2,-.8,6.2),600,6),((-6,.4,2.25),400,4),((-6.1,3.2,2.2),300,3)]:
 bpy.ops.object.light_add(type='AREA',location=pos);ob=bpy.context.object;ob.data.energy=power;ob.data.size=size;ob.data.color=(1,.87,.72)
 # Area light points down, spreading light naturally over the wall/floor.
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam
for name,pos,target,lens in [('piso_superior_mezanino',(1.8,2.05,4.5),(2,-2.2,3.1),23),('porta_madeira_detalhe',(-5.55,.35,1.05),(-6.1,2.35,.35),34)]:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
 s.render.filepath=str(W/(name+'.png'));bpy.ops.render.render(write_still=True)
print('UPPER_FLOOR_AND_DOOR_PREVIEWS_RENDERED',flush=True)
