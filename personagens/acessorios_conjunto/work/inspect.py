import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.world=bpy.data.worlds.new('World');sc.world.color=(.3,.3,.3)
for name,file in [('sapatos','Meshy_AI_brown_leather_loafers_1005054801_image-to-3d-texture.glb'),('relogio','Meshy_AI_gold_luxury_watch_3d_1005054634_image-to-3d-texture.glb')]:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(Path(r'C:\Users\erons\Downloads')/file))
 objects=list(set(bpy.data.objects)-before)
 for o in objects:
  if o.type=='MESH':print(name,o.name,len(o.data.vertices),len(o.data.polygons),list(o.dimensions),[list(v) for v in o.bound_box],flush=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(root/(name+'_original.blend')))
 sc.render.engine='CYCLES';sc.cycles.samples=12;sc.render.resolution_x=700;sc.render.resolution_y=700;sc.render.resolution_percentage=100
 def aim(o,p):o.location=p;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=2.8;aim(cam,(3,-4,3));sc.camera=cam
 lamps=[]
 for p in [(-3,-4,4),(3,-2,2)]:
  bpy.ops.object.light_add(type='AREA');o=bpy.context.object;o.data.energy=450;o.data.size=4;aim(o,p);lamps.append(o)
 sc.render.filepath=str(root/(name+'_original.png'));bpy.ops.render.render(write_still=True)
 for o in objects+lamps+[cam]:bpy.data.objects.remove(o,do_unlink=True)
