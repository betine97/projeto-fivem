"""Additive lighting/plant layer; leave the installed architecture untouched."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(W/'work/pydeps'),str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz']
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import unary_union
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_encaixada.blend'))
s=bpy.context.scene
col=bpy.data.collections.new('18_SPOTS_E_LED_ESCADA');s.collection.children.link(col)
plantscol=bpy.data.collections.new('19_VASOS_NATIVOS');s.collection.children.link(plantscol)
origin=json.loads((W/'medidas_estudo.json').read_text())['native_origin']
cfg=dict(revision='plantas-spots-2026-10-08',origin=origin,spots=[],stairs=[],plants=[],in_game_verified=False)
def mat(name,color,emit=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.5
 if emit:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emit
 m['decor_family']='led' if emit else 'trim';return m
led=mat('LED quente 3000 K',(1,.75,.43),3);trim=mat('Aro spot branco fosco',(.75,.72,.65))
def move(o,name,material):
 o.name=name
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.data.materials.clear();o.data.materials.append(material)
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 return o
def cuboid(name,lo,hi,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=[(lo[i]+hi[i])/2 for i in range(3)]);o=bpy.context.object;o.dimensions=[hi[i]-lo[i] for i in range(3)];return move(o,name,material)
collections={p:next(c for c in bpy.data.collections if c.name.startswith(p)) for p in ('01_','02_','03_','04_','05_','06_','10_','15_','16_')}
walls=[];floors=[];ceilings=[]
for prefix,c in collections.items():
 for o in c.objects:
  if o.type!='MESH':continue
  o.data.calc_loop_triangles()
  for t in o.data.loop_triangles:
   pts=[o.matrix_world@o.data.vertices[i].co for i in t.vertices];normal=(pts[1]-pts[0]).cross(pts[2]-pts[0])
   if prefix in ('04_','06_') and normal.z<-.00001:ceilings.append(pts)
   if prefix=='04_' and normal.z>.00001:floors.append(pts)
   if prefix in ('01_','02_','03_') and abs(normal.z)<normal.length*.8:walls.append(pts)
vs=[v for t in ceilings for v in t];bvh=BVHTree.FromPolygons(vs,[tuple(range(i,i+3)) for i in range(0,len(vs),3)],all_triangles=True)
floorpoly={};wallpoly={}
for z in (-.8,2.808):
 floorpoly[z]=unary_union([Polygon([(p.x,p.y) for p in t]) for t in floors if max(abs(p.z-z) for p in t)<.01])
 solids=[]
 for t in walls:
  if max(p.z for p in t)<z+.15 or min(p.z for p in t)>z+1.95:continue
  q=Polygon([(p.x,p.y) for p in t])
  solids.append(q.buffer(.015) if q.area>.00001 else LineString([(p.x,p.y) for p in t]).buffer(.015))
 wallpoly[z]=unary_union(solids)
 # Exclude furniture and the stair well from plant placement.
 for prefix in ('10_','15_','16_'):
  for o in collections[prefix].objects:
   if o.type!='MESH':continue
   pts=[o.matrix_world@v.co for v in o.data.vertices];lo=[min(v[i] for v in pts) for i in range(3)];hi=[max(v[i] for v in pts) for i in range(3)]
   if lo[2]<z+1.95 and hi[2]>z+.05:wallpoly[z]=wallpoly[z].union(box(lo[0],lo[1],hi[0],hi[1]).buffer(.12))
 if z<0:wallpoly[z]=wallpoly[z].union(box(-.5,1.3,2.7,5.85))
doors=json.loads((R/'server-data/resources/cidade_mansao/portas_madeira.json').read_text())['doors']
for d in doors:
 x,y,_=d['hinge'];wallpoly[-.8]=wallpoly[-.8].union(Point(x,y).buffer(d['width_m']+.18))
# Two regular grids, fitted by ray cast to the actual ceiling/lower slab.
for z in (-.8,2.808):
 for x in [-7.6,-5.1,-2.,1.3,4.3,7.7,10.8,12.9]:
  for y in [-14.4,-11.1,-8.1,-5.3,-2.3,.6,4.1,6.6,8.3]:
   p=Point(x,y)
   if not floorpoly[z].buffer(-.30).covers(p) or wallpoly[z].distance(p)<.22:continue
   # Ceiling spots can sit above furniture; exclude only walls here.
   hit,normal,face,dist=bvh.ray_cast(Vector((x,y,z+.1)),Vector((0,0,1)),10.)
   if hit is None or hit.z<z+2.2:continue
   # Ground level uses the tall ceiling only over the actual double-height void.
   if z>0 and hit.z<5:continue
   if z<0 and hit.z>5 and y>-3.75:continue
   # Preserve space occupied by the existing pendant mounts.
   if (abs(x-2.65)<.9 and abs(y+8.3)<1.6) or (abs(x-10.45)<.6 and abs(y+9)<1.7):continue
   if any(abs(q['position'][0]-x)<.01 and abs(q['position'][1]-y)<.01 and abs(q['ceiling_z']-hit.z)<.01 for q in cfg['spots']):continue
   n=len(cfg['spots'])+1;h=hit.z
   # A narrow ring and recessed diffuser: 14 cm opening, below the ceiling by 2 mm.
   bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=6,major_radius=.065,minor_radius=.007,location=(x,y,h-.002));move(bpy.context.object,f'Spot {n:03} aro embutido',trim)
   bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.059,depth=.012,location=(x,y,h+.001));move(bpy.context.object,f'Spot {n:03} difusor LED',led)
   cfg['spots'].append(dict(id=n,position=[x,y,h-.023],ceiling_z=h,level='terreo' if z<0 else 'superior',rgb=[255,214,166],distance=h-z+.1,brightness=1.5 if h-z<4 else 2.1,radius=2.6,falloff=1.0))
# Continuous visible LED strips beneath all 18 treads and the two landings.
for o in list(collections['05_'].objects):
 if 'degrau' not in o.name and 'patamar intermediario' not in o.name and 'chegada superior' not in o.name:continue
 pts=[o.matrix_world@v.co for v in o.data.vertices];lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
 y=lo[1]+.008 if 'lance 1' in o.name else hi[1]-.008
 if 'patamar' in o.name:y=lo[1]+.008
 z=hi[2]-.026
 cuboid('Perfil aluminio LED '+o.name,[lo[0]+.045,y-.013,z-.012],[hi[0]-.045,y+.013,z+.012],trim)
 cuboid('Fita LED '+o.name,[lo[0]+.052,y-.014,z-.007],[hi[0]-.052,y+.014,z+.007],led)
 cfg['stairs'].append(dict(name=o.name,position=[(lo[0]+hi[0])/2,y,z-.02],rgb=[255,200,130],range=.72,intensity=.42,length_m=hi[0]-lo[0]-.104))
# Mixed native pots; large ones by glass/walls, slender ones in smaller rooms.
native=json.loads((W/'work/decor_plant_bounds.json').read_text())
requested=[('Sala vidro',-7.25,-11.7,-.8,'prop_plant_int_02a',1),('Sala lateral',-7.4,-5.95,-.8,'prop_pot_plant_02b',.85),('Sala canto',-.2,-11,-.8,'prop_pot_plant_02a',.85),('Jantar fachada',4.9,-10.95,-.8,'prop_plant_int_02a',1),('Cozinha canto',12.95,-10.9,-.8,'prop_pot_plant_02b',.85),('Hall entrada',11.1,.8,-.8,'prop_plant_int_02a',1),('Escada hall',3.2,1.,-.8,'prop_plant_int_02a',1),('Escritorio',-8.35,7.8,-.8,'prop_plant_int_02a',.8),('Sala jogos',9.6,4.8,-.8,'prop_pot_plant_02a',.75),('Suite master',-7.65,8.5,2.808,'prop_pot_plant_02b',.85),('Closet',-8.1,-2.8,2.808,'prop_plant_int_02a',.7),('Banheiro suite',-3.7,-2.7,2.808,'prop_plant_int_02a',.7),('Mezanino',5.6,-3.1,2.808,'prop_plant_int_02a',1),('Leitura',4.7,4.7,2.808,'prop_pot_plant_02a',.85),('Quarto 2',12.8,-13.2,2.808,'prop_pot_plant_02b',.85),('Quarto 3',12.8,5.3,2.808,'prop_plant_int_02a',1),('Banheiro social',12.9,.3,2.808,'prop_plant_int_02a',.7)]
requested=[(label,x,-4.85,z,model,scale) if label=='Sala lateral' else (label,x,-11.7,z,'prop_plant_int_02a',1) if label=='Sala canto' else (label,5.4,y,z,model,scale) if label=='Jantar fachada' else (label,x,y,z,model,scale) for label,x,y,z,model,scale in requested]
for label,x,y,z,model,scale in requested:
 b=native[model];lo=b['lo'];hi=b['hi'];found=None
 offsets=sorted([(dx*.2,dy*.2) for dx in range(-5,6) for dy in range(-5,6)],key=lambda a:a[0]**2+a[1]**2)
 for dx,dy in offsets:
  px,py=x+dx,y+dy;foot=box(px+lo[0]*scale,py+lo[1]*scale,px+hi[0]*scale,py+hi[1]*scale)
  if not floorpoly[z].buffer(-.13).covers(foot) or wallpoly[z].buffer(.13).intersects(foot):continue
  if any(foot.buffer(.1).intersects(box(*p['footprint'])) for p in cfg['plants'] if p['floor_z']==z):continue
  found=(px,py,foot);break
 assert found is not None,('No safe placement',label)
 px,py,foot=found
 cfg['plants'].append(dict(name=label,model=model,position=[px,py,z-lo[2]*scale],floor_z=z,scale=scale,heading=0,footprint=list(foot.bounds),height_m=b['height']*scale))
# Native plants in Blender are a preview only; the game uses its original models/textures.
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
from szio.gta5 import try_load_asset,AssetTarget,AssetFormat,AssetVersion
from Sollumz.ydr.ydrimport import create_drawable
from Sollumz.iecontext import ImportContext,ImportSettings,import_context_scope
for q in cfg['plants']:
 f=W/'work/decor_native'/(q['model']+'.ydr');a=try_load_asset(f)
 with import_context_scope(ImportContext(f.stem,AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),f.parent,ImportSettings(False,False,False,False))):root=create_drawable(a,name=q['name'])
 root.location=q['position'];root.scale=(q['scale'],)*3
 for o in [root,*root.children_recursive]:
  for c in list(o.users_collection):c.objects.unlink(o)
  plantscol.objects.link(o)
  if o.type=='MESH' and 'bound' in str(o.sollum_type).lower():o.hide_render=True
for m in bpy.data.materials:
 if not m.use_nodes:continue
 for n in m.node_tree.nodes:
  if n.type!='TEX_IMAGE' or not n.image:continue
  name=Path(n.image.filepath.replace('//','')).stem.lower()
  for directory in (W/'work/decor_native',W/'work/textures'):
   path=directory/(name+'.dds')
   if path.exists():n.image=bpy.data.images.load(str(path),check_existing=False);break
cfg['fixture_objects']=len(col.objects)
(W/'decoracao_iluminacao.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
for im in bpy.data.images:
 if im.has_data:
  try:im.pack()
  except Exception:pass
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_iluminada.blend'))
print('DECOR_BUILT',len(cfg['spots']),'spots',len(cfg['stairs']),'stairs',len(cfg['plants']),'plants',flush=True)
