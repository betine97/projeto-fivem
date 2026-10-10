import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r'C:\Users\erons\Downloads\Meshy_AI_retro_pattern_shirt_3_1005054809_image-to-3d-texture.glb')
meshes=[o for o in bpy.data.objects if o.type=='MESH']
for o in meshes:
 print('MESH',o.name,len(o.data.vertices),len(o.data.polygons),list(o.dimensions),[list(v) for v in o.bound_box],flush=True)
 for m in o.data.materials:
  for n in m.node_tree.nodes:
   if n.type=='TEX_IMAGE':print('TEXTURE',n.image.name,list(n.image.size),flush=True)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=16;sc.render.resolution_x=800;sc.render.resolution_y=800;sc.render.resolution_percentage=100
sc.world=bpy.data.worlds.new('World');sc.world.color=(.3,.3,.3)
def aim(o,p,t):o.location=p;o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=2.7;aim(cam,(0,-5,0),(0,0,0));sc.camera=cam
for p in [(-3,-4,4),(3,-2,2)]:
 bpy.ops.object.light_add(type='AREA');o=bpy.context.object;o.data.energy=450;o.data.shape='DISK';o.data.size=4;aim(o,p,(0,0,0))
bpy.ops.wm.save_as_mainfile(filepath=str(root/'CAMISA_ORIGINAL.blend'))
sc.render.filepath=str(root/'original.png');bpy.ops.render.render(write_still=True)

