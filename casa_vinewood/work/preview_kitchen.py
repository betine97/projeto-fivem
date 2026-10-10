import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1];interior='--interior' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(W/('mansao_cozinha_completa.blend' if interior else 'cozinha_completa.blend')));s=bpy.context.scene
if s.world is None:s.world=bpy.data.worlds.new('World')
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.14 if interior else .18
for o in list(bpy.data.objects):
 if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
def area(pos,target,power,size,color=(1,.8,.59),shape='DISK',size_y=None):
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();o.data.energy=power;o.data.size=size;o.data.color=color;o.data.shape=shape
 if size_y is not None:o.data.size_y=size_y
if interior:
 for c in bpy.data.collections:
  if c.name.startswith(('07_','09_','11_','13_','90_','91_','92_','93_')):c.hide_render=True
 # Warm worktop lighting corresponds to the actual strip and existing ceiling sources.
 for u in [1.14,2.18,3.22,4.26,5.05]:area((13.91,-6.6-u,.835),(13.70,-6.6-u,.12),35,.48,shape='RECTANGLE',size_y=.025)
 for pos in [(10.1,-8.9,2.18),(11.9,-12.1,2.19),(11.9,-6.5,2.19)]:area(pos,(pos[0],pos[1],-.8),210,1.1)
 area((8,-5.3,1.8),(13.6,-9,.9),210,4,(1,.91,.8))
 bpy.ops.object.camera_add(location=(8.45,-5.70,1.12));cam=bpy.context.object;target=(13.4,-9.90,.68);cam.data.lens=24;name='cozinha_completa_instalada'
else:
 bpy.ops.mesh.primitive_plane_add(size=200,location=(3,0,-.01));floor=bpy.context.object;mat=bpy.data.materials.new('Piso neutro studio');mat.diffuse_color=(.20,.17,.13,1);floor.data.materials.append(mat)
 area((3,-3,6),(3,0,1.2),950,6);area((-.5,-2,3.5),(2,0,1.2),500,3,(1,.91,.8));area((7,-1,4),(5,0,1.4),450,3)
 for u in [1.14,2.18,3.22,4.26,5.05]:area((u,.32,1.636),(u,.35,.92),23,.65,shape='RECTANGLE',size_y=.025)
 bpy.ops.object.camera_add(location=(8.1,-10.5,4.4));cam=bpy.context.object;target=(3.25,.25,1.46);cam.data.lens=47;name='cozinha_completa_preview'
cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.clip_start=.04;s.camera=cam
s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True;s.render.resolution_x=1350;s.render.resolution_y=850;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.render.filepath=str(W/(name+'.png'));bpy.ops.render.render(write_still=True);print('KITCHEN_PREVIEW_RENDERED',name,flush=True)
