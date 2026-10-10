import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1];mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'piano';interior=mode in ('sala','hall','bear_sala')
bpy.ops.wm.open_mainfile(filepath=str(W/('mansao_piano_tapetes.blend' if interior else 'piano_tapetes_autorais.blend')));s=bpy.context.scene
if not interior:
 for c in bpy.data.collections:
  if c.name.startswith('Modelo '):c.hide_render=c.name!='Modelo '+mode
 for o in list(bpy.data.objects):
  if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
if s.world is None:s.world=bpy.data.worlds.new('World')
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.08 if interior else .17
def area(pos,target,power,size,color=(1,.86,.68),sy=None):
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();o.data.energy=power;o.data.size=size;o.data.color=color
 if sy:o.data.shape='RECTANGLE';o.data.size_y=sy
# Preview uses the authored colour/normal maps and lacquer/brass responses.
for m in bpy.data.materials:
 if not m.name.startswith('piano_tapetes_'):continue
 family=m.name.split('piano_tapetes_',1)[1].split('.')[0]
 bsdf=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if bsdf is None:continue
 for field,value in [('Roughness',.12 if family=='black' else .22 if family=='gold' else .4 if family in ('ivory','nose') else .83),('Metallic',.85 if family=='gold' else 0),('Coat Weight',.35 if family=='black' else 0)]:
  socket=bsdf.inputs.get(field)
  if socket:
   for link in list(socket.links):m.node_tree.links.remove(link)
   socket.default_value=value
if interior:
 for c in bpy.data.collections:
  if c.name.startswith(('07_','09_','11_','13_','90_','91_','92_')):c.hide_render=True
 if mode=='sala':
  area((-5.1,-4.9,2.1),(-5.1,-4.9,-.8),110,2)
  area((-7.8,-5.3,1.7),(-5,-4.3,.1),160,2,(.86,.92,1))
  area((-3.5,-8.5,4),(-3,-7,-.8),200,3)
  pos=(-7.8,-7.0,1.25);target=(-4.0,-5.15,.35);lens=24;name='piano_sala_instalado'
 elif mode=='bear_sala':
  area((-.65,-8.2,3.5),(-.65,-8.2,-.8),200,2.5)
  pos=(.1,-5.5,1.3);target=(-.65,-8.2,-.74);lens=30;name='tapete_urso_sala'
 else:
  area((7.5,.1,2.2),(7.5,.1,-.8),160,2)
  pos=(5.7,.4,1.15);target=(7.4,.6,-.8);lens=24;name='tapete_classico_hall'
else:
 bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.001));o=bpy.context.object;m=bpy.data.materials.new('Fundo studio');m.diffuse_color=(.17,.14,.11,1);o.data.materials.append(m)
 area((-.5,-2.8,4),(0,.5,.8),900,3,sy=1);area((3,1.3,3.5),(0,.7,1),650,3,(.83,.9,1),sy=.65);area((-3,1.8,3),(0,.9,1),650,3,sy=.55)
 if mode=='piano':pos=(3.5,-4.5,2.8);target=(0,.6,.90);lens=43;name='piano_cauda_preview'
 elif mode=='bear':pos=(1.6,-2.2,2.5);target=(0,0,.025);lens=48;name='tapete_urso_preview'
 else:pos=(1.4,-2.5,3.0);target=(0,0,0);lens=48;name='tapete_classico_preview'
bpy.ops.object.camera_add(location=pos);cam=bpy.context.object;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;cam.data.clip_start=.03;s.camera=cam
s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True;s.render.resolution_x=1300;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.render.filepath=str(W/(name+'.png'));bpy.ops.render.render(write_still=True);print('PIANO_RUG_PREVIEW',name,flush=True)
