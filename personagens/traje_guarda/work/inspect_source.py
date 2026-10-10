import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=r'C:\Users\erons\Downloads\Meshy_AI_guard_character_3d_1005050026_image-to-3d-texture.glb')
o=next(o for o in bpy.data.objects if o.type=='MESH')
print('SOURCE',o.name,len(o.data.vertices),len(o.data.polygons),tuple(o.dimensions),flush=True)
for m in o.data.materials:
 print('MAT',m.name,[(n.name,n.image.name,list(n.image.size)) for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image],flush=True)
 for n in m.node_tree.nodes:
  if n.type=='TEX_IMAGE' and n.image:n.image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(root/'ORIGINAL_GUARDA.blend'))
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.render.resolution_x=700;sc.render.resolution_y=900;sc.render.resolution_percentage=100
sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.5
sc.render.film_transparent=True
bpy.ops.object.camera_add(location=(0,-4,.9));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,.9))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.05;sc.camera=cam
for p,e in [((-3,-4,4),400),((3,-3,2),250)]:
 bpy.ops.object.light_add(type='AREA',location=p);l=bpy.context.object;l.data.energy=e;l.data.size=3;l.rotation_euler=(Vector((0,0,1))-l.location).to_track_quat('-Z','Y').to_euler()
sc.render.filepath=str(root/'original_frente.png');bpy.ops.render.render(write_still=True)
cam.location=(3,-4,1.2);cam.rotation_euler=(Vector((0,0,.9))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(root/'original_perspectiva.png');bpy.ops.render.render(write_still=True)
