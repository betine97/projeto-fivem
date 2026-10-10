import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent
spec=json.loads((P/'spec.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_piano_tapetes.blend'));s=bpy.context.scene
with bpy.data.libraries.load(str(P/'bar_parede_editavel.blend'),link=False) as (src,dst):dst.collections=['24_BAR_PAREDE_REFERENCIA']
c=dst.collections[0];s.collection.children.link(c)
tx=Matrix(((-1,0,0,spec['design_start_x']),(0,-1,0,spec['model_wall_y']),(0,0,1,spec['floor_z']),(0,0,0,1)))
for obj in c.objects:
 if obj.type=='MESH':obj.data.transform(tx);obj.data.update()
bear=bpy.data.objects.get('Instancia mansao_tapete_urso')
assert bear is not None
bear.scale=(1.5,1.5,1.5)
# Native floor underside is wood in game; repair the source preview material
# only, keeping every installed architectural asset unchanged.
wood=bpy.data.materials.get('bar_madeira')
for cc in bpy.data.collections:
 if cc.name.startswith('04_'):
  for obj in cc.objects:
   if obj.type!='MESH':continue
   obj.data.materials.append(wood);index=len(obj.data.materials)-1
   for poly in obj.data.polygons:
    if poly.normal.z<-.7 and abs((obj.matrix_world@poly.center).z-2.358)<.03:
     poly.material_index=index
     for li in poly.loop_indices:
      co=obj.matrix_world@obj.data.vertices[obj.data.loops[li].vertex_index].co
      obj.data.uv_layers[0].data[li].uv=(co.x/2.4,co.y/1.344)
# Source is independent of other ongoing work; never replace its Blender scenes.
for o in list(bpy.data.objects):
 if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
for c in bpy.data.collections:
 if c.name.startswith(('07_','09_','11_','13_','90_','91_','92_','93_','94_')):c.hide_render=True;c.hide_viewport=True
def area(pos,target,power,size,color=(1,.83,.61),size_y=None):
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();o.data.energy=power;o.data.size=size;o.data.color=color
 if size_y:o.data.shape='RECTANGLE';o.data.size_y=size_y
for z in [.785,1.39,2.248]:area((7.7,-13.83,z),(7.7,-14.18,z-.32),65,2.4,size_y=.04)
area((10.8,-14.05,2.24),(10.8,-14.20,.95),40,.78,size_y=.025)
area((7.7,-13.85,-.70),(7.7,-12.95,-.8),22,2.3,size_y=.02)
for y in [-8.1,-10.0,-11.8]:area((13.86,y,.833),(13.73,y,.10),40,1.0,size_y=.03)
for pos in [(10,-9,2.2),(11.9,-12.1,2.19),(7.9,-12,2.19)]:area(pos,(pos[0],pos[1],-.8),220,1.5)
area((7.8,-5.8,1.8),(10.4,-13.6,.8),260,4,(1,.91,.78))
if s.world is None:s.world=bpy.data.worlds.new('World')
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.18
bpy.ops.object.camera_add(location=(7.0,-6.9,1.24));cam=bpy.context.object;cam.rotation_euler=(Vector((10.35,-12.85,.72))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=24;cam.data.clip_start=.025;s.camera=cam
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True;s.render.resolution_x=1440;s.render.resolution_y=940;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'mansao_bar_tapete_150.blend'),compress=True)
s.render.filepath=str(P/'parede_bar_instalada.png');bpy.ops.render.render(write_still=True)
# A second view verifies the new rug proportion in the actual room.
cam.location=(.2,-5.2,1.6);cam.rotation_euler=(Vector((-.65,-8.2,-.68))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=28
area((-.65,-8.2,3.5),(-.65,-8.2,-.8),230,3.2)
s.render.filepath=str(P/'tapete_urso_150.png');bpy.ops.render.render(write_still=True)
print('BAR_AND_BEAR_PREVIEWS_READY',flush=True)
