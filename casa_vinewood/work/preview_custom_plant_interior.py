import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_vasos_autorais.blend'));s=bpy.context.scene
for c in bpy.data.collections:c.hide_render=c.name.startswith(('07_','09_','11_','13_','90_','91_'));c.hide_viewport=c.hide_render
for o in list(bpy.data.objects):
 if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
cfg=json.loads((W/'decoracao_iluminacao.json').read_text())
for q in cfg['spots']:
 bpy.ops.object.light_add(type='SPOT',location=q['position']);o=bpy.context.object;o.data.energy=(110 if q['distance']<4 else 250)*cfg['night_multiplier'];o.data.color=(1,.78,.52);o.data.spot_size=math.radians(100);o.data.spot_blend=.65;o.data.shadow_soft_size=.075
s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.resolution_x=1200;s.render.resolution_y=850;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.07;s.view_settings.view_transform='AgX'
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.lens=25;cam.data.clip_start=.05
for name,pos,target in [('vaso_autoral_sala_instalacao',(-3.2,-4.0,.8),(-7.1,-2.45,.50)),('vaso_autoral_escada_instalacao',(6.0,-.45,.95),(4.0,1.4,.4))]:
 if '--' in sys.argv and name not in sys.argv[sys.argv.index('--')+1:]:continue
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(W/(name+'.png'));bpy.ops.render.render(write_still=True)
print('CUSTOM_PLANT_INTERIOR_PREVIEW_RENDERED',flush=True)
