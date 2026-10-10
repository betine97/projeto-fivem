import bpy,math
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'vaso_planta_autoral.blend'));s=bpy.context.scene
ground=bpy.data.materials.new('Fundo estudio');ground.diffuse_color=(.13,.145,.155,1)
bpy.ops.mesh.primitive_plane_add(size=200);bpy.context.object.data.materials.append(ground)
for pos,power,size in [((2,-3,4),650,3),((-3,-1,2.5),420,2),((1,2,3.2),600,2)]:
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,1.1))-o.location).to_track_quat('-Z','Y').to_euler()
if s.world is None:s.world=bpy.data.worlds.new('Estudio')
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.25
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True;s.render.resolution_x=1000;s.render.resolution_y=1200;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
bpy.ops.object.camera_add(location=(2.9,-4.4,2.5));cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.7;cam.rotation_euler=(Vector((0,0,1.12))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(W/'vaso_planta_autoral_preview.png');bpy.ops.render.render(write_still=True)
print('CUSTOM_PLANT_PREVIEW_RENDERED',flush=True)
