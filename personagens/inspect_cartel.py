import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent
source=Path(r'C:\Users\erons\Downloads\Meshy_AI_The_Cartel_King_1002154146_texture_fbx')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=str(next(source.rglob('*.fbx'))))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in bpy.context.scene.objects:
 print('OBJECT',o.name,o.type,tuple(o.dimensions),len(o.data.vertices) if o.type=='MESH' else '',len(o.data.bones) if o.type=='ARMATURE' else '',[g.name for g in o.vertex_groups] if o.type=='MESH' else '')
coords=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
low=Vector(tuple(min(c[k] for c in coords) for k in range(3)));high=Vector(tuple(max(c[k] for c in coords) for k in range(3)))
print('BOUNDS',list(low),list(high))
target=(low+high)/2
for idx,delta in enumerate([(0,-5,1),(0,5,1)]):
 d=bpy.data.cameras.new('cam');cam=bpy.data.objects.new('cam',d);bpy.context.collection.objects.link(cam);cam.location=target+Vector(delta);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=max(high-low)*1.2
 for loc in [(-3,-4,5),(3,3,4)]:
  ld=bpy.data.lights.new('soft','AREA');lo=bpy.data.objects.new('soft',ld);bpy.context.collection.objects.link(lo);lo.location=target+Vector(loc);ld.energy=500;ld.size=4;lo.rotation_euler=(target-lo.location).to_track_quat('-Z','Y').to_euler()
 sc=bpy.context.scene;sc.camera=cam;sc.render.engine='CYCLES';sc.cycles.samples=16;sc.render.resolution_x=700;sc.render.resolution_y=850;sc.render.resolution_percentage=100;sc.render.filepath=str(root/('source_'+str(idx)+'.png'));bpy.ops.render.render(write_still=True)
