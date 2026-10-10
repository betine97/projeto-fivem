import bpy
from pathlib import Path
from mathutils import Vector
base=Path(__file__).resolve().parent
path=str(base/'warehouse_stage12_plantas.blend')
bpy.ops.wm.open_mainfile(filepath=path)
s=bpy.context.scene
s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_denoising=True
s.render.resolution_x=1100;s.render.resolution_y=1400;s.render.resolution_percentage=100;s.render.use_compositing=False
prefix='PLACEHOLDER_LEFT_00_01'
pot=bpy.data.objects[prefix+'_POT'];center=Vector((pot.location.x,pot.location.y,1.03))
for o in bpy.data.objects:
    if o.type in ('MESH','CURVE','LIGHT'):o.hide_render=not o.name.startswith(prefix)
cam=bpy.data.objects['STAGE7_OVERVIEW'];s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.9
cam.location=center+Vector((2,-3,1.1));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
for name,offset,power,size in [('KEY',(2,-3,4),350,3),('FILL',(-2,-1,2),160,2),('RIM',(1,2,3),240,2)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.size=size
    o=bpy.data.objects.new(name,data);s.collection.objects.link(o);o.location=center+Vector(offset);o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.10,.10,.10,1)
s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45;s.view_settings.exposure=0
s.render.filepath=str(base/'warehouse_stage12_planta_detalhe.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.open_mainfile(filepath=path)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_denoising=True
s.render.resolution_x=1400;s.render.resolution_y=1200;s.render.resolution_percentage=100
s.camera=bpy.data.objects['STAGE7_OVERVIEW']
for o in bpy.data.objects:
    if any(x in o.name.upper() for x in ('ROOF','WALL_FRONT','CEILING_SLAB')):o.hide_render=True
data=bpy.data.lights.new('PREVIEW_FILL','AREA');data.energy=1400;data.size=8
o=bpy.data.objects.new(data.name,data);s.collection.objects.link(o);o.location=(0,0,7)
s.render.filepath=str(base/'warehouse_stage12_visao_geral.png');bpy.ops.render.render(write_still=True)
print('RENDER STAGE12 OK')
