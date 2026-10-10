import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parent;W=P.parent
spec=json.loads((P/'spec.json').read_text());tx=Matrix(((0,1,0,14.168),(-1,0,0,-.98),(0,0,1,-.8),(0,0,0,1)))
bpy.ops.wm.open_mainfile(filepath=str(W/'adega_referencia_20261008/mansao_com_adega.blend'));s=bpy.context.scene
with bpy.data.libraries.load(str(P/'parede_aparador_editavel.blend'),link=False) as (src,dst):dst.collections=[spec['collection']]
c=dst.collections[0];s.collection.children.link(c)
for o in c.objects:
    if o.type=='MESH':o.data.transform(tx);o.data.update()
for o in list(bpy.data.objects):
    if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
for cc in bpy.data.collections:
    if cc.name.startswith(('07_','09_','11_','13_','90_','91_','92_','93_','94_')):cc.hide_render=True
def area(name,design,target,power,width,height=None,color=(1,.83,.58)):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.size=width;data.color=color
    if height is not None:data.shape='RECTANGLE';data.size_y=height
    o=bpy.data.objects.new(name,data);s.collection.objects.link(o);o.location=tx@Vector(design);o.rotation_euler=(tx@Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
panel_s=(3.42-.72)/(3.42-.15)
for i,u in enumerate([1.075,2.505]):
    u=.72+(u-.15)*panel_s
    area('Luz quadro '+str(i),(u,-.18,2.90),(u,0,2.10),9,.52,.028)
area('Luz sob aparador',(2.075,-.23,.34),(2.075,-.33,0),12,2.40,.025)
area('Ambiente parede',(2.8,-3,2.8),(2.8,-.1,1.4),190,4.0,None,(1,.94,.85))
area('Preenchimento cozinha',(6.8,-3.7,2.9),(5.3,-1,1.3),130,3.0,None,(1,.93,.83))
if s.world is None:s.world=bpy.data.worlds.new('Ambiente')
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.17
bpy.ops.object.camera_add(location=(8.8,-5.15,1.11));cam=bpy.context.object
cam.rotation_euler=(Vector((14.0,-3.65,.65))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=28;cam.data.clip_start=.03;s.camera=cam
s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True;s.cycles.max_bounces=16;s.cycles.transmission_bounces=16
s.render.resolution_x=1440;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'mansao_parede_aparador.blend'),compress=True)
s.render.filepath=str(P/'parede_instalada_blender.png');bpy.ops.render.render(write_still=True)
cam.location=(9.6,-4.05,.84);cam.rotation_euler=(Vector((14.05,-3.85,.82))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=32
s.render.resolution_x=1500;s.render.resolution_y=1100
s.render.filepath=str(P/'parede_frontal_blender.png');bpy.ops.render.render(write_still=True)
print('APARADOR_PREVIEWS_READY',flush=True)
