import bpy,math,json
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parent;W=P.parent
spec=json.loads((P/'spec.json').read_text());sx=spec['width_m']/1393;sz=spec['height_m']/871
X=lambda pixel:(pixel-27)*sx
Z=lambda pixel:(978-pixel)*sz
bpy.ops.wm.open_mainfile(filepath=str(P/'adega_vitrines_editavel.blend'))
s=bpy.context.scene
def area(name,pos,target,power,size,size_y=None,color=(1,.65,.27)):
 bpy.ops.object.light_add(type='AREA',location=pos);obj=bpy.context.object;obj.name=name
 obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler();obj.data.energy=power;obj.data.size=size;obj.data.color=color
 if size_y is not None:obj.data.shape='RECTANGLE';obj.data.size_y=size_y
 return obj
for k,(p0,p1) in enumerate([(45,219),(225,400),(1048,1224),(1228,1402)]):
 a=X(p0);b=X(p1)
 for j,x in enumerate([a+.078,b-.078]):area('LED lateral vitrine %d %d'%(k,j),(x,-.180,1.49),(x,-.038,1.49),5,.034,2.68)
for z in [Z(157),Z(334)-.008,Z(505)-.008]:area('LED nicho',(X(724),-.18,z),(X(724),-.04,z-.21),16,2.00,.027)
area('LED adega refrigerada',(X(510),-.480,.40),(X(510),-.120,.40),3,.18,.70)
area('Abajur quente',(X(967),-.28,Z(706)+.31),(X(967),-.24,Z(706)),9,.24)
area('Softbox frente',(2.357,-4.0,3.1),(2.35,-.2,1.5),130,4.5,None,(1,.86,.67))
area('Reflexo vidro esquerdo',(-.7,-2.7,1.7),(1,-.3,1.5),30,.16,2.4,(1,.83,.55))
area('Reflexo vidro direito',(5.4,-2.7,1.7),(3.8,-.3,1.5),30,.16,2.4,(1,.83,.55))
s.world=bpy.data.worlds.new('Adega studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.012,.011,.009,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.20
bpy.ops.object.camera_add(location=(2.3575,-7.2,1.48));camera=bpy.context.object
camera.rotation_euler=(Vector((2.3575,0,1.48))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=5.18;s.camera=camera
s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=True;s.cycles.max_bounces=24;s.cycles.transmission_bounces=24;s.render.resolution_x=1600;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
s.render.filepath=str(P/'adega_frontal_blender.png')
bpy.ops.render.render(write_still=True)

# Install into an independent copy of the current mansion scene. Existing
# source projects and all in-game asset placements remain unchanged.
lights=[o for o in s.objects if o.type=='LIGHT'];light_values=[(o.name,tuple(o.location),tuple(o.rotation_euler),o.data.energy,o.data.size,o.data.size_y,o.data.shape,tuple(o.data.color)) for o in lights]
bpy.ops.wm.open_mainfile(filepath=str(W/'bar_referencia_20261008/mansao_bar_tapete_150.blend'));s=bpy.context.scene
with bpy.data.libraries.load(str(P/'adega_vitrines_editavel.blend'),link=False) as (src,dst):dst.collections=[spec['collection']]
collection=dst.collections[0];s.collection.children.link(collection)
placement=Vector((spec['placement']['left_x'],spec['placement']['back_y'],spec['placement']['floor_z']));tx=Matrix.Translation(placement)
for obj in collection.objects:
 if obj.type=='MESH':obj.data.transform(tx);obj.data.update()
for name,pos,rotation,energy,size,size_y,shape,color in light_values:
 data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.size=size;data.shape=shape
 if shape=='RECTANGLE':data.size_y=size_y
 data.color=color
 obj=bpy.data.objects.new(name,data);s.collection.objects.link(obj);obj.location=Vector(pos)+placement;obj.rotation_euler=rotation
area('Cozinha luz ambiente',(11.7,-4.1,2.12),(11.7,-3.4,-.8),180,2.0,None,(1,.88,.72))
camera=s.camera;camera.data.type='PERSP';camera.data.lens=27;camera.location=(9.5,-7.1,1.26)
camera.rotation_euler=(Vector((11.3,-1.10,.57))-camera.location).to_track_quat('-Z','Y').to_euler()
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True;s.cycles.max_bounces=24;s.cycles.transmission_bounces=24;s.render.resolution_x=1440;s.render.resolution_y=940;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'mansao_com_adega.blend'),compress=True)
s.render.filepath=str(P/'adega_na_parede_blender.png');bpy.ops.render.render(write_still=True)
print('ADEGA_PREVIEWS_READY',flush=True)
