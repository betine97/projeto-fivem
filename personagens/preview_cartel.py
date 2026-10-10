exec(compile((__import__('pathlib').Path(__file__).parent/'probe_rig.py').read_text().split("bpy.ops.object.select_all")[0],__file__,'exec'))
from mathutils import Vector
import math
root=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(root/'cartelking.blend'))
for o in bpy.data.objects:
 if o.type=='MESH' and o.name not in ['SKEL_ROOT','SKEL_ROOT.003','SKEL_ROOT.005']:o.hide_render=True
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=16;sc.render.resolution_x=800;sc.render.resolution_y=900;sc.render.resolution_percentage=100
d=bpy.data.cameras.new('Preview');cam=bpy.data.objects.new('Preview',d);sc.collection.objects.link(cam);cam.location=(2,-5,1.1);target=Vector((0,0,-.1));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=2.2;sc.camera=cam
for loc in [(-3,-4,4),(3,-2,2)]:
 ld=bpy.data.lights.new('Soft','AREA');lo=bpy.data.objects.new('Soft',ld);sc.collection.objects.link(lo);lo.location=loc;lo.rotation_euler=(target-lo.location).to_track_quat('-Z','Y').to_euler();ld.energy=450;ld.size=4
sc.render.filepath=str(root/'cartelking_preview.png');bpy.ops.render.render(write_still=True)
for o in bpy.data.objects:
 if o.type=='ARMATURE':
  for name,angle in [('SKEL_L_Calf',.65),('SKEL_R_Thigh',-.35),('SKEL_L_Forearm',-.8),('SKEL_R_Forearm',-.8)]:
   b=o.pose.bones.get(name)
   if b:b.rotation_mode='XYZ';b.rotation_euler.y=angle
sc.render.filepath=str(root/'cartelking_pose_test.png');bpy.ops.render.render(write_still=True)
