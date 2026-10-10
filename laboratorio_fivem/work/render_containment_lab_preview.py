import bpy
from mathutils import Vector
from pathlib import Path

root=Path(__file__).resolve().parents[2]
camera_data=bpy.data.cameras.new('Containment QA Camera')
camera=bpy.data.objects.new('Containment QA Camera',camera_data)
bpy.context.scene.collection.objects.link(camera)
camera.location=(.0,-3.8,1.85)
target=Vector((2.48,-.75,1.55))
camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
camera_data.type='ORTHO'
camera_data.ortho_scale=5.8
bpy.context.scene.camera=camera
lamp_data=bpy.data.lights.new('Containment QA Light','AREA')
lamp_data.energy=850
lamp_data.size=5
lamp=bpy.data.objects.new('Containment QA Light',lamp_data)
bpy.context.scene.collection.objects.link(lamp)
lamp.location=(.4,-2.4,3.15)
lamp.rotation_euler=(target-lamp.location).to_track_quat('-Z','Y').to_euler()
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=960
scene.render.resolution_y=600
scene.render.resolution_percentage=100
scene.render.filepath=str(root/'laboratorio_fivem/containment_source/containment_lab_preview.png')
bpy.ops.render.render(write_still=True)
print('LAB_PREVIEW_OK',scene.render.filepath,flush=True)
