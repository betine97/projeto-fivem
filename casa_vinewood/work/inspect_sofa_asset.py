import bpy,json
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(W/'source_assets/sofa_original.glb'))
objects=[o for o in bpy.data.objects if o.type=='MESH']
pts=[o.matrix_world@v.co for o in objects for v in o.data.vertices]
lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)])
for o in objects:
 o.data.calc_loop_triangles();print('SOFA_MESH',o.name,len(o.data.vertices),len(o.data.loop_triangles),flush=True)
print('BLENDER_BOUNDS',list(lo),list(hi),list(hi-lo),flush=True)
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH'
s.display.shading.light='STUDIO';s.display.shading.color_type='TEXTURE';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True
s.display.shading.cavity_type='BOTH';s.display.shading.background_type='WORLD'
s.world=bpy.data.worlds.new('Inspection world');s.world.color=(.16,.16,.16)
s.render.resolution_x=1100;s.render.resolution_y=850;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
center=(lo+hi)*.5
bpy.ops.object.camera_add(location=center+Vector((2.5,-3,2.2)));cam=bpy.context.object
cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.7;s.camera=cam
s.render.filepath=str(W/'sofa_inspecao_original.png');bpy.ops.render.render(write_still=True)
cam.location=center+Vector((0,0,4));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
s.render.filepath=str(W/'sofa_inspecao_superior.png');bpy.ops.render.render(write_still=True)
print('SOFA_INSPECTION_OK',flush=True)
