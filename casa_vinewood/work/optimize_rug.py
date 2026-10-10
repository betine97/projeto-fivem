import bpy,bmesh,json,sys
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];spec=json.loads((W/'tapete_sala.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=spec['local_source'])
o=next(o for o in bpy.data.objects if o.type=='MESH');o.data.transform(o.matrix_world);o.matrix_world.identity();o.name='Tapete tecido Meshy sob sofa'
me=o.data;me.calc_loop_triangles();original=len(me.loop_triangles)
print('RUG_IMPORTED',len(me.vertices),'verts',original,'triangles',flush=True)
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000002);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
bpy.context.view_layer.objects.active=o;o.select_set(True)
mod=o.modifiers.new('Otimizar tapete preservando UV','DECIMATE');mod.ratio=min(1.,45000/original);mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name)
me.calc_loop_triangles();ps=np.zeros(len(me.vertices)*3,dtype=np.float32);me.vertices.foreach_get('co',ps);ps=ps.reshape(-1,3);lo=ps.min(0);hi=ps.max(0)
print('RUG_OPTIMIZED',len(me.loop_triangles),'dimensions',hi-lo,flush=True)
# The longest rug side follows the 5.2 m length of the sectional.
horizontal=sorted(range(3),key=lambda i:hi[i]-lo[i],reverse=True)[:2];vertical=next(i for i in range(3) if i not in horizontal);long,short=horizontal
center=(lo+hi)/2;scale=6.2/(hi[long]-lo[long]);new=np.zeros_like(ps)
new[:,1]=-8.8+(ps[:,long]-center[long])*scale
new[:,0]=-5.5+(ps[:,short]-center[short])*scale
new[:,2]=-.797+(ps[:,vertical]-lo[vertical])*min(scale,.016/(hi[vertical]-lo[vertical]))
# X/y remapping may reflect the original orientation; recompute all normals.
me.vertices.foreach_set('co',new.reshape(-1));me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
if me.has_custom_normals:me.normals_split_custom_set([(0,0,0)]*len(me.loops))
for p in me.polygons:p.use_smooth=True
o['preserve_source_uv']=True;o['component_family']='rug'
for m in me.materials:m['finish_family']='rug'
spec.update(object=o.name,original_triangles=original,triangles=len(me.loop_triangles),lo=new.min(0).tolist(),hi=new.max(0).tolist(),dimensions=(new.max(0)-new.min(0)).tolist(),base_floor_z=-.8,uniform_xy_scale=float(scale),uv_preserved=True,thickness_adjusted_for_game=True)
(W/'tapete_sala.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
for im in bpy.data.images:
 try:im.pack()
 except Exception:pass
bpy.ops.wm.save_as_mainfile(filepath=str(W/'work/tapete_otimizado.blend'))
print('RUG_SAVED',flush=True)
