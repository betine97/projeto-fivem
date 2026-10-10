import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'castelo_rockford.blend'))
assert bpy.context.scene.unit_settings.scale_length==1
assert all(im.packed_file for im in bpy.data.images if im.source=='FILE')
deps=bpy.context.evaluated_depsgraph_get();vs=[];fs=[];ranges=[];triangles=0
for o in bpy.data.objects:
 if o.type!='MESH':continue
 e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();triangles+=len(m.loop_triangles)
 if any(c.name.startswith(('01_','02_','03_')) for c in o.users_collection):
  start=len(vs);before=len(fs);vs.extend(e.matrix_world@v.co for v in m.vertices)
  fs.extend(tuple(start+i for i in t.vertices) for t in m.loop_triangles);ranges.append((before,len(fs),o.name))
 e.to_mesh_clear()
bvh=BVHTree.FromPolygons(vs,fs,all_triangles=True)
routes=[
 ('entrada principal',(0,-14,1.6),(0,2,1.6)),
 ('foyer para festas',(-3,-2,1.6),(-5.5,-2,1.6)),
 ('foyer para cozinha',(3,-3,1.6),(5.5,-3,1.6)),
 ('foyer para apoio',(3,4,1.6),(5.5,4,1.6)),
 ('quarto funcionarios',(0,-2,5.8),(0,-4,5.8)),
 ('suite frontal esquerda',(-3,-2,5.8),(-5.5,-2,5.8)),
 ('suite frontal direita',(3,-2,5.8),(5.5,-2,5.8)),
 ('suite fundos esquerda',(-3,3,5.8),(-5.5,3,5.8)),
 ('suite fundos direita',(3,3,5.8),(5.5,3,5.8)),
 ('acesso sala reuniao',(0,3,10),(0,1.9,10)),
]
checks=[]
for name,a,b in routes:
 a=Vector(a);d=Vector(b)-a;lateral=Vector((-d.y,d.x,0)).normalized();ray_count=0
 for side in [-.3,0,.3]:
  for dz in [0,.9]:
   hit=bvh.ray_cast(a+lateral*side+Vector((0,0,dz)),d.normalized(),d.length)
   obj=next((n for lo,hi,n in ranges if hit[2] is not None and lo<=hit[2]<hi),None)
   assert hit[0] is None,(name,obj,hit[0]);ray_count+=1
 checks.append({'route':name,'clear':True,'body_width_m':.6,'head_height_above_floor_m':1.8,'rays':ray_count})
floor_checks=[]
for name,point,height in [('terreo',(0,0,3),.7),('primeiro',(0,-1.5,7),4.9),('ultimo',(11,-7,11),9.1)]:
 hit=bvh.ray_cast(Vector(point),Vector((0,0,-1)),4)
 assert hit[0] is not None and abs(hit[0].z-height)<.005 and hit[1].z>.9,(name,hit)
 floor_checks.append({'floor':name,'height_m':hit[0].z,'normal_up':True})
for floor_name,base in [('01_TERREO',.7),('02_SUITES',4.9)]:
 heights=[]
 for o in bpy.data.collections[floor_name].objects:
  if o.name.startswith(('Escada lance subida','Escada lance retorno')):
   heights.append(max((o.matrix_world@v.co).z for v in o.data.vertices))
 heights.sort();assert len(heights)==24
 assert all(abs(h-(base+(j+1)*.175))<.005 for j,h in enumerate(heights)),heights
results={'blend_reopened':True,'textures_packed':True,'metric_scale':True,'evaluated_triangles_with_bevels':triangles,'passage_checks':checks,'floor_checks':floor_checks,'actual_stair_risers_verified':48,'in_game_verified':False}
(OUT/'verificacao_blender.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(results,ensure_ascii=False),flush=True)
