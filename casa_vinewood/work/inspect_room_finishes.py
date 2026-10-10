"""Inspect saved GTA materials/UVs and render the finished room without saving."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_fivem_preparada.blend'))
s=bpy.context.scene
rows=[]
for c in bpy.data.collections:
 if not c.name.startswith(('01_','02_','03_','04_','05_','06_','10_','11_','12_','13_')):continue
 for ob in c.objects:
  if ob.type!='MESH':continue
  ps=[ob.matrix_world@v.co for v in ob.data.vertices]
  lo=[min(p[i] for p in ps) for i in range(3)];hi=[max(p[i] for p in ps) for i in range(3)]
  faces={}
  for p in ob.data.polygons:
   family=ob.data.materials[p.material_index].get('finish_family','other') if ob.data.materials else 'collider'
   faces[family]=faces.get(family,0)+1
  row=dict(name=ob.name,collection=c.name,lo=lo,hi=hi,face_materials=faces)
  if any(k in faces for k in ('marble','wall','brick','metal')):
   ob.data.calc_loop_triangles()
   row['material_probes']=[dict(position=list(ob.matrix_world@t.center),family=ob.data.materials[t.material_index].get('finish_family','other')) for t in ob.data.loop_triangles]
  if ob.get('preserve_source_uv'):
   uv=ob.data.uv_layers[0];step=max(1,len(ob.data.loops)//256)
   row['uv_probes']=[dict(position=list(ob.matrix_world@ob.data.vertices[ob.data.loops[i].vertex_index].co),uv=list(uv.data[i].uv)) for i in range(0,len(ob.data.loops),step)]
   row['uv_min']=[min(t.uv[i] for t in uv.data) for i in (0,1)];row['uv_max']=[max(t.uv[i] for t in uv.data) for i in (0,1)]
  rows.append(row)
(W/'inspecao_materiais_blender.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
if '--probe-only' in __import__('sys').argv:
 print('ROOM_MATERIAL_PROBES_SAVED',flush=True)
 __import__('sys').exit(0)
for c in bpy.data.collections:
 if c.name.startswith(('07_','09_','11_','13_','90_','91_')):c.hide_render=True
 else:c.hide_render=False
s.render.engine='CYCLES';s.cycles.samples=20;s.cycles.use_denoising=True
s.render.resolution_x=1280;s.render.resolution_y=960;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
s.world.use_nodes=True;s.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.30,.34,.40,1)
s.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.35
# Preview illumination only; these lights are neither saved nor exported.
for pos,target,power,size in [((-4,-9,5.8),(-4,-9,-.8),750,5),((-8.4,-8,2.2),(-4,-8,.1),380,3),((-4,-14,3.4),(-4,-6,.5),900,5),((1,-2,5.8),(0,-1,-.8),500,4)]:
 bpy.ops.object.light_add(type='AREA',location=pos);lamp=bpy.context.object;lamp.data.energy=power;lamp.data.shape='DISK';lamp.data.size=size;lamp.data.color=(1,.85,.68)
 lamp.rotation_euler=(Vector(target)-lamp.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam
views=[('sala_materiais_visao_geral',(-.3,-5.2,3.8),(-5.8,-9.1,.7),24),('sala_sofa_frente',(-7.6,-11.6,1.05),(-3.9,-8.6,-.1),25)]
for name,pos,target,lens in views:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
 s.render.filepath=str(W/(name+'.png'));bpy.ops.render.render(write_still=True);print('ROOM_VIEW_RENDERED',name,flush=True)
print('ROOM_QA_PREVIEWS_COMPLETE',flush=True)
