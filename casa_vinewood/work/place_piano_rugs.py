import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(W/'work/pydeps'),str(R/'laboratorio_fivem/work/pydeps')]
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union
# Preserve the newer spot/art scene, then append only the kitchen authored here.
base=W/'mansao_spots_quadros.blend'
if not base.exists():base=W/'mansao_cozinha_completa.blend'
bpy.ops.wm.open_mainfile(filepath=str(base));s=bpy.context.scene
if '22_COZINHA_COMPLETA' not in bpy.data.collections:
 with bpy.data.libraries.load(str(W/'mansao_cozinha_completa.blend'),link=False) as (src,dst):dst.collections=['22_COZINHA_COMPLETA']
 for c in dst.collections:s.collection.children.link(c)
 for o in bpy.data.objects:
  if o.name=='Cozinha canto':o.location=json.loads((W/'cozinha_completa.json').read_text())['plant_relocation']['new']
spec=json.loads((W/'piano_tapetes.json').read_text());col=bpy.data.collections.new('23_PIANO_TAPETES');s.collection.children.link(col)
with bpy.data.libraries.load(str(W/'piano_tapetes_autorais.blend'),link=False) as (src,dst):dst.collections=['Modelo piano','Modelo bear','Modelo carpet']
for family,c in zip(('piano','bear','carpet'),dst.collections):
 s.collection.children.link(c);row=spec['models'][family];root=bpy.data.objects.new('Instancia '+row['name'],None);col.objects.link(root);root.location=row['position'];root.rotation_euler.z=row['heading']
 for o in c.objects:o.parent=root
bpy.context.view_layer.update();solids=[];floors=[]
for c in bpy.data.collections:
 if not c.name.startswith(('01_','02_','04_')):continue
 for o in c.objects:
  if o.type!='MESH':continue
  o.data.calc_loop_triangles()
  for t in o.data.loop_triangles:
   p=[o.matrix_world@o.data.vertices[i].co for i in t.vertices];n=(p[1]-p[0]).cross(p[2]-p[0])
   if c.name.startswith('04_') and n.z>0 and max(abs(v.z+.8) for v in p)<.01:floors.append(Polygon([(v.x,v.y) for v in p]))
   elif c.name.startswith(('01_','02_')) and abs(n.z)<n.length*.8 and max(v.z for v in p)>-.7 and min(v.z for v in p)<1.5:solids.append(LineString([(v.x,v.y) for v in p]).buffer(.005))
floor=unary_union(floors);walls=unary_union(solids)
for family,row in spec['models'].items():
 root=bpy.data.objects['Instancia '+row['name']];points=[o.matrix_world@v.co for o in root.children for v in o.data.vertices];foot=Polygon([(v.x,v.y) for v in points]).convex_hull
 assert floor.buffer(.01).covers(foot),('Outside floor',family);assert not walls.intersects(foot),('Intersects wall',family)
 row['world_footprint']=list(foot.bounds);row['wall_clearance_m']=walls.distance(foot)
 if family=='piano':assert max(v.z for v in points)<2.25
for c in bpy.data.collections:
 if c.name.startswith(('07_','09_','11_','13_','90_','91_','92_')):c.hide_render=True;c.hide_viewport=True
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_piano_tapetes.blend'));(W/'piano_tapetes.json').write_text(json.dumps(spec,indent=2),encoding='utf-8');print('PIANO_AND_BOTH_RUGS_PLACED',flush=True)
