"""Render the empty lower room for visual material review."""
from pathlib import Path
import bpy
from mathutils import Vector

root=Path(__file__).resolve().parents[2]
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=18
scene.render.resolution_x=1200
scene.render.resolution_y=760
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'

camera_data=bpy.data.cameras.new('Basement QA camera')
camera=bpy.data.objects.new('Basement QA camera',camera_data)
scene.collection.objects.link(camera)
camera.location=(-1.2,-4.75,-6.20)
target=Vector((0,5.45,-6.35))
camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
camera_data.lens=24
scene.camera=camera

light_data=bpy.data.lights.new('Basement QA area','AREA')
light_data.energy=1400
light_data.shape='DISK';light_data.size=5
light=bpy.data.objects.new('Basement QA area',light_data)
scene.collection.objects.link(light)
light.location=(0,-1,-4.6)

scene.render.filepath=str(root/'laboratorio_fivem/elevator_source/elevator_sublevel_room_preview.png')
bpy.ops.render.render(write_still=True)
print('BASEMENT_ROOM_RENDER_OK',flush=True)
