import bpy,bmesh,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_encaixada.blend'))
sofa=next(o for o in bpy.data.objects if o.name=='Sofa e mesa de centro Meshy')
bm=bmesh.new();bm.from_mesh(sofa.data)
print('SOFA_DEFECTS',dict(verts=len(bm.verts),faces=len(bm.faces),boundary_edges=sum(e.is_boundary for e in bm.edges),nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),zero_area_faces=sum(f.calc_area()<1e-12 for f in bm.faces)),flush=True)
bm.free()
for c in bpy.data.collections:
 if c.name.startswith(('02_','04_')):
  for ob in c.objects:
   if ob.type=='MESH':
    ps=[ob.matrix_world@v.co for v in ob.data.vertices]
    print('ROOM_OBJECT',ob.name,[min(p[i] for p in ps) for i in range(3)],[max(p[i] for p in ps) for i in range(3)],flush=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(W/'source_assets/sofa_original.glb'))
ob=next(o for o in bpy.data.objects if o.type=='MESH');bm=bmesh.new();bm.from_mesh(ob.data)
print('ORIGINAL_BEFORE_WELD',len(bm.verts),len(bm.faces),sum(e.is_boundary for e in bm.edges),flush=True)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000002)
print('ORIGINAL_AFTER_WELD',len(bm.verts),len(bm.faces),sum(e.is_boundary for e in bm.edges),sum(not e.is_manifold for e in bm.edges),flush=True)
bm.free()
