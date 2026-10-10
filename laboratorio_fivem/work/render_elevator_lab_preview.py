from pathlib import Path
import bpy
from mathutils import Vector

root=Path(__file__).resolve().parents[2]
scene=bpy.context.scene
camera_data=bpy.data.cameras.new('Elevator QA camera')
camera=bpy.data.objects.new('Elevator QA camera',camera_data)
scene.collection.objects.link(camera)
scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.samples=20
scene.render.resolution_x=1200;scene.render.resolution_y=800
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
camera_data.lens=38
light_data=bpy.data.lights.new('Elevator QA basement light','AREA')
light_data.energy=1500
light_data.shape='DISK';light_data.size=5
light=bpy.data.objects.new('Elevator QA basement light',light_data)
scene.collection.objects.link(light)
light.location=(0,0,-4.55)
for name,loc,target in (
 ('lab',(0,-.6,1.7),(0,5.15,1.35)),
 ('sublevel',(0,-.6,-6.3),(0,5.15,-6.65)),
):
    light.hide_render=(name=='lab')
    camera.location=loc
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(root/f'laboratorio_fivem/elevator_source/elevator_{name}_preview.png')
    bpy.ops.render.render(write_still=True)
    if name=='lab':
        for suffix in ('L','R'):
            bpy.data.objects[f'LAB_ELEVATOR_DOOR_0_{suffix}'].hide_render=True
        scene.render.filepath=str(root/'laboratorio_fivem/elevator_source/elevator_lab_open_preview.png')
        bpy.ops.render.render(write_still=True)
print('ELEVATOR_PREVIEWS_OK',flush=True)
