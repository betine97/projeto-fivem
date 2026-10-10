import bpy
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_fivem_preparada.blend'))
s=bpy.context.scene
for c in bpy.data.collections:
 if c.name.startswith(('07_','09_','90_','91_')):c.hide_viewport=True
bpy.ops.object.camera_add(location=(3.8,-.5,.85));cam=bpy.context.object
cam.rotation_euler=(Vector((1.,4.,2.5))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=25
s.render.resolution_x=1120;s.render.resolution_y=800;s.render.resolution_percentage=100
bpy.context.view_layer.update()
frame=cam.data.view_frame(scene=s);xs=[v.x for v in frame];ys=[v.y for v in frame]
for ob in bpy.data.objects:
 if ob.name.startswith(('Escada chegada','Escada lance 2 degrau 20','Laje superior')):
  ps=[ob.matrix_world@v.co for v in ob.data.vertices]
  print('PART',ob.name,[min(p[i] for p in ps) for i in range(3)],[max(p[i] for p in ps) for i in range(3)],flush=True)
for x,y in [(400,259),(430,256),(377,265),(500,261),(562,287),(603,310)]:
 u=x/1120;v=1-y/800;p=Vector((min(xs)+(max(xs)-min(xs))*u,min(ys)+(max(ys)-min(ys))*v,frame[0].z))
 d=cam.matrix_world.to_3x3()@p.normalized();bpy.context.view_layer.update()
 hit,loc,n,ix,obj,_=s.ray_cast(bpy.context.evaluated_depsgraph_get(),cam.location,d,distance=50)
 if hit:
  poly=obj.data.polygons[ix];mat=obj.data.materials[poly.material_index] if obj.data.materials else None
  print('PREVIEW_RAY',x,y,obj.name,list(loc),list(n),ix,mat.name if mat else None,flush=True)
  if mat:
   print('TEXTURES',[(n.name,n.image.name if n.image else None, bool(n.image.packed_file) if n.image else None) for n in mat.node_tree.nodes if n.type=='TEX_IMAGE'],flush=True)
