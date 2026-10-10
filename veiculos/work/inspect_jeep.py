import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent.parent
source=Path(r'C:\Users\erons\Downloads\Meshy_AI_WWII_U_S_Army_Jeep_1002142336_texture_fbx\Meshy_AI_WWII_U_S_Army_Jeep_1002142336_texture_fbx')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(next(source.glob('*.fbx'))))
for o in bpy.data.objects:
 if o.type=='MESH':print('MESH',o.name,'dimensions',list(o.dimensions),'verts',len(o.data.vertices),'faces',len(o.data.polygons),'bounds',[list(o.matrix_world@Vector(v)) for v in o.bound_box])
bpy.ops.wm.save_as_mainfile(filepath=str(root/'jeep_importado.blend'))
sc=bpy.context.scene
meshes=[o for o in bpy.data.objects if o.type=='MESH'];pts=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
center=sum(pts,Vector())/len(pts);size=max(max(v[i] for v in pts)-min(v[i] for v in pts) for i in range(3))
for name,offset in [('Key',(2,3,4)),('Fill',(-3,0,2))]:
 d=bpy.data.lights.new(name,'AREA');d.energy=1500;d.size=size*2;o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=center+Vector(offset)*size;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Review');o=bpy.data.objects.new('Review',d);sc.collection.objects.link(o);o.location=center+Vector((1.5,-2,1.2))*size;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=size*1.3;sc.camera=o
sc.render.engine='CYCLES';sc.cycles.samples=12;sc.render.resolution_x=1000;sc.render.resolution_y=800;sc.world=bpy.data.worlds.new('World');sc.world.color=(.3,.3,.3);sc.render.filepath=str(root/'jeep_importado.png');bpy.ops.render.render(write_still=True)
