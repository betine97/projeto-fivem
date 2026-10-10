"""Preview the placed furnished room, using the actual exported materials."""
import bpy,json
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_fivem_preparada.blend'));s=bpy.context.scene
for c in bpy.data.collections:
 c.hide_render=c.name.startswith(('07_','09_','11_','13_','90_','91_'))
 c.hide_viewport=c.hide_render
s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True
s.render.resolution_x=1500;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
for pos,power,size in [((2.7,-8.3,5.8),450,5),((10,-9,2.12),140,3),((-4,-9,5.8),450,5)]:
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.data.color=(1,.83,.64)
for lamp in json.loads((W/'luzes_pendentes.json').read_text())['lights']:
 bpy.ops.object.light_add(type='AREA',location=lamp['position']);o=bpy.context.object;o.data.energy=25;o.data.size=.16;o.data.color=(1,.75,.43)
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam
for name,pos,target,lens in [
 ('jantar_cozinha_visao_geral',(3.3,-2.9,1.35),(3.8,-8.8,.7),18),
 ('mesa_jantar_detalhe',(.15,-11.85,1.15),(2.65,-8.3,.25),27),
 ('ilha_cozinha_detalhe',(7.05,-10.65,1.05),(10.15,-9,.35),25)]:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
 s.render.filepath=str(W/(name+'.png'));bpy.ops.render.render(write_still=True)
print('DINING_KITCHEN_PREVIEWS_RENDERED',flush=True)
