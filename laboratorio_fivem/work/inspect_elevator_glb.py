from pathlib import Path
import bpy
from mathutils import Vector

root=Path(__file__).resolve().parents[2]
source=Path(r'C:\Users\erons\Downloads\Meshy_AI_industrial_elevator_c_1004184824_image-to-3d-texture.glb')
bpy.ops.import_scene.gltf(filepath=str(source))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
print('ELEVATOR_OBJECTS',len(meshes),flush=True)
for obj in meshes:
    corners=[obj.matrix_world@Vector(corner) for corner in obj.bound_box]
    lo=[min(p[i] for p in corners) for i in range(3)]
    hi=[max(p[i] for p in corners) for i in range(3)]
    print('OBJECT',obj.name,'faces',len(obj.data.polygons),'verts',len(obj.data.vertices),
          'bounds',lo,hi,'materials',[m.name for m in obj.data.materials],flush=True)
    if obj.name=='Cube':obj.hide_render=True
print('IMAGES',[(i.name,tuple(i.size),i.channels) for i in bpy.data.images],flush=True)
print('COLLECTIONS',[c.name for c in bpy.data.collections],flush=True)

# Contact sheet from four sides, enough to locate the doors and cabin in model coordinates.
world=bpy.context.scene.world or bpy.data.worlds.new('Elevator preview')
bpy.context.scene.world=world
world.color=(.4,.4,.4)
for name,location in [('KEY',(3,-4,7)),('FILL',(-4,3,5))]:
    data=bpy.data.lights.new(name,'AREA')
    data.energy=1500;data.shape='DISK';data.size=5
    light=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(light)
    light.location=location
    light.rotation_euler=(Vector((0,0,1.5))-light.location).to_track_quat('-Z','Y').to_euler()
camera_data=bpy.data.cameras.new('Preview camera')
camera=bpy.data.objects.new('Preview camera',camera_data)
bpy.context.scene.collection.objects.link(camera)
scene=bpy.context.scene
scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.samples=24
scene.render.resolution_x=900;scene.render.resolution_y=700;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
for label,position in [('front',(0,-6,1.7))]:
    camera.location=position
    camera.rotation_euler=(Vector((0,0,1.3))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera_data.type='ORTHO';camera_data.ortho_scale=5.4
    scene.render.filepath=str(root/f'laboratorio_fivem/work/elevator_{label}.png')
    bpy.ops.render.render(write_still=True)
print('ELEVATOR_INSPECTION_DONE',flush=True)
