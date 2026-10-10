import bpy
from mathutils import Vector
from pathlib import Path

root = Path(__file__).resolve().parents[2]
bpy.ops.import_scene.gltf(filepath=r'C:\Users\erons\Downloads\Meshy_AI_cleanroom_containment_1004173529_image-to-3d-texture.glb')
bpy.data.objects['Cube'].hide_render = True
camera_data = bpy.data.cameras.new('Inspection Camera')
camera = bpy.data.objects.new('Inspection Camera', camera_data)
bpy.context.collection.objects.link(camera)
camera.location = (2.8, -3.2, 1.8)
direction = Vector((0, 0, 0)) - camera.location
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
camera_data.type = 'ORTHO'
camera_data.ortho_scale = 2.7
bpy.context.scene.camera = camera
for location, power, size in [((1,-2,4),500,4),((-2,1,2),300,3)]:
    data = bpy.data.lights.new('Inspection Light', 'AREA')
    data.energy = power
    data.shape = 'DISK'
    data.size = size
    obj = bpy.data.objects.new('Inspection Light', data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector((0,0,0)) - obj.location).to_track_quat('-Z','Y').to_euler()
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 960
scene.render.resolution_y = 600
scene.render.resolution_percentage = 100
scene.world.color = (.15,.15,.15)
scene.render.filepath = str(root / 'laboratorio_fivem/work/containment_glb_preview.png')
bpy.ops.render.render(write_still=True)
print('PREVIEW_OK',scene.render.filepath,flush=True)
