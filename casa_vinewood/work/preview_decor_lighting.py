import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_iluminada.blend'));s=bpy.context.scene
for c in bpy.data.collections:
 c.hide_render=c.name.startswith(('07_','09_','11_','13_','90_','91_'));c.hide_viewport=c.hide_render
for o in list(bpy.data.objects):
 if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
cfg=json.loads((W/'decoracao_iluminacao.json').read_text())
for row in cfg['spots']:
 bpy.ops.object.light_add(type='SPOT',location=row['position']);o=bpy.context.object;o.data.energy=(110 if row['distance']<4 else 250)*cfg.get('night_multiplier',1);o.data.color=(1,.78,.52);o.data.spot_size=math.radians(100);o.data.spot_blend=.65;o.data.shadow_soft_size=.075
for row in cfg['stairs']:
 bpy.ops.object.light_add(type='AREA',location=row['position']);o=bpy.context.object;o.data.energy=4;o.data.color=(1,.70,.38);o.data.shape='RECTANGLE';o.data.size=row['length_m'];o.data.size_y=.025
for row in json.loads((W/'luzes_pendentes.json').read_text())['lights']:
 bpy.ops.object.light_add(type='AREA',location=row['position']);o=bpy.context.object;o.data.energy=22;o.data.color=(1,.78,.48);o.data.size=.12
s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True
s.render.resolution_x=1280;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.07
s.view_settings.view_transform='AgX'
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam
for name,pos,target,lens in [('noite_tapete_sala',(.8,-3.1,1.15),(-4,-8.9,1.15),20),('noite_quadros_hall',(-1.5,.3,1.0),(-6.4,2.25,.85),18)]:
 if '--' in sys.argv and name not in sys.argv[sys.argv.index('--')+1:]:continue
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;cam.data.clip_start=.05
 s.render.filepath=str(W/(name+'.png'));bpy.ops.render.render(write_still=True)
print('DECOR_PREVIEW_RENDERED',flush=True)
