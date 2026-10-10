import bpy,json,bmesh,sys
from pathlib import Path
from mathutils import Vector
import numpy as np
W=Path(__file__).resolve().parents[1];spec=json.loads((W/'componentes_jantar_cozinha.json').read_text());rows={}
for key,row in spec['assets'].items():
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=row['local_source'])
 objects=[o for o in bpy.data.objects if o.type=='MESH'];ps=np.array([o.matrix_world@v.co for o in objects for v in o.data.vertices]);lo=ps.min(0);hi=ps.max(0)
 stats=[]
 for o in objects:
  o.data.calc_loop_triangles();bm=bmesh.new();bm.from_mesh(o.data);before=sum(e.is_boundary for e in bm.edges);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000002);bm.normal_update()
  stats.append(dict(name=o.name,triangles=len(o.data.loop_triangles),boundary_before=before,boundary_welded=sum(e.is_boundary for e in bm.edges),nonmanifold_welded=sum(not e.is_manifold for e in bm.edges)));bm.free()
 rows[key]=dict(lo=lo.tolist(),hi=hi.tolist(),dimensions=(hi-lo).tolist(),objects=stats)
 s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='TEXTURE';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True
 bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;center=Vector((lo+hi)*.5);distance=float(max(hi-lo));cam.location=center+Vector((distance*1.15,-distance*1.5,distance*.9));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=distance*1.55
 s.render.resolution_x=1100;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(W/(key+'_original_inspecao.png'));bpy.ops.render.render(write_still=True)
 print('INPUT_INSPECTED',key,rows[key],flush=True)
(W/'work/inspecao_componentes_originais.json').write_text(json.dumps(rows,indent=2))
