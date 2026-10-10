import bpy,json,sys
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=r'C:\Users\erons\Downloads\Meshy_AI_pleated_beige_trouser_1005054816_image-to-3d-texture.glb')
o=next(o for o in bpy.data.objects if o.type=='MESH');print('PANTS',o.name,len(o.data.vertices),len(o.data.polygons),list(o.dimensions),list(o.matrix_world),flush=True)
for mat in o.data.materials:
 for n in mat.node_tree.nodes:
  if n.type=='TEX_IMAGE' and n.image:print('IMAGE',n.name,n.image.name,list(n.image.size),flush=True);n.image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(root/'CALCA_ORIGINAL.blend'))
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.render.resolution_x=700;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.world.color=(.3,.3,.3)
bpy.ops.object.camera_add(location=(0,-5,0));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.12;sc.camera=cam
for loc in [(-3,-4,3),(3,-3,2)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=450;l.data.size=3;l.rotation_euler=(Vector((0,0,0))-l.location).to_track_quat('-Z','Y').to_euler()
sc.render.filepath=str(root/'original_frente.png');bpy.ops.render.render(write_still=True)
cam.location=(3,-4,.1);cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(root/'original_perspectiva.png');bpy.ops.render.render(write_still=True)
