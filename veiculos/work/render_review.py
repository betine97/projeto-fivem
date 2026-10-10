import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(root/'sertao_studio.blend'))
sc=bpy.context.scene;cam=sc.camera
sc.render.engine='CYCLES';sc.cycles.samples=16
sc.render.resolution_x=1120;sc.render.resolution_y=900;sc.render.resolution_percentage=100
folder=root/'review';folder.mkdir(exist_ok=True)
for name,power in [('Key',850),('Fill',600),('Rim',950)]:
    bpy.data.lights[name].energy=power
sc.view_settings.exposure=-.35
views={'FRONT_3Q':(-5.2,7,4.9),'REAR_3Q':(5,-7,4.4),'SIDE':(-8,0,2.3),'FRONT':(0,8,1.4),'REAR':(0,-8,1.4),'TOP':(0,0,9)}
for name,position in views.items():
    cam.location=position;target=Vector((0,0,.55))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO';cam.data.ortho_scale=6.45
    sc.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True)
print('SIX_VIEWS_COMPLETE')
cam.location=views['FRONT_3Q'];cam.rotation_euler=(Vector((0,0,.55))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(root/'sertao_studio.blend'))
