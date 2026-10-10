import bpy,sys,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(W/'work/pydeps'),str(R/'laboratorio_fivem/work/pydeps')]
from shapely.geometry import Polygon,LineString,Point,box
from shapely.ops import unary_union
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_iluminada.blend'));s=bpy.context.scene;spec=json.loads((W/'vaso_planta_autoral.json').read_text())
solids=[];floors=[]
for c in bpy.data.collections:
 if not c.name.startswith(('01_','02_','04_')):continue
 for o in c.objects:
  if o.type!='MESH':continue
  o.data.calc_loop_triangles()
  for tri in o.data.loop_triangles:
   p=[o.matrix_world@o.data.vertices[i].co for i in tri.vertices];n=(p[1]-p[0]).cross(p[2]-p[0])
   if c.name.startswith('04_') and n.z>0 and max(abs(x.z+.8) for x in p)<.01:floors.append(Polygon([(x.x,x.y) for x in p]))
   elif c.name.startswith(('01_','02_')) and abs(n.z)<n.length*.8 and max(x.z for x in p)>-.75 and min(x.z for x in p)<1.5:
    solids.append(LineString([(x.x,x.y) for x in p]).buffer(.015))
floor=unary_union(floors);walls=unary_union(solids);col=bpy.data.collections.new('21_VASOS_AUTORAIS');s.collection.children.link(col)
with bpy.data.libraries.load(str(W/'vaso_planta_autoral.blend'),link=False) as (src,dest):dest.objects=[n for n in src.objects]
sources=[o for o in dest.objects if o.type=='MESH']
for row in spec['instances']:
 root=bpy.data.objects.new(row['name'],None);col.objects.link(root);root.location=row['position'];root.rotation_euler.z=row['heading'];points=[]
 for src in sources:
  o=src.copy();o.data=src.data;col.objects.link(o);o.parent=root
 bpy.context.view_layer.update()
 for o in root.children:points.extend(o.matrix_world@v.co for v in o.data.vertices)
 footprint=Polygon([(p.x,p.y) for p in points]).convex_hull
 assert floor.buffer(.015).covers(footprint),('Crown outside floor',row['name'])
 assert not walls.intersects(footprint),('Crown intersects wall',row['name'])
 doors=json.loads((R/'server-data/resources/cidade_mansao/portas_madeira.json').read_text())['doors']
 for d in doors:assert footprint.distance(Point(*d['hinge'][:2]))>d['width_m']+.12,('Crown inside door swing',row['name'],d['name'])
 row['door_swing_clear']=True
 row['wall_clearance_m']=walls.distance(footprint);row['crown_footprint']=list(footprint.bounds)
 assert max(p.z for p in points)<2.25
for src in sources:bpy.data.objects.remove(src,do_unlink=True)
(W/'vaso_planta_autoral.json').write_text(json.dumps(spec,indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_vasos_autorais.blend'))
print('TWO_CUSTOM_PLANTS_PLACED_WITH_CROWN_CLEARANCE',flush=True)
