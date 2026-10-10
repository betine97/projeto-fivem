"""Place supplied dining/island assemblies and fit the pendant suspension cables."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_encaixada.blend'))
spec=json.loads((W/'componentes_jantar_cozinha.json').read_text());s=bpy.context.scene
collections={}
for k,n in [('dining','15_JANTAR_MESHY'),('island','16_ILHA_COZINHA_MESHY'),('lights','17_PENDENTES_MESHY')]:
 c=bpy.data.collections.get(n)
 if c:
  for ob in list(c.objects):bpy.data.objects.remove(ob,do_unlink=True)
 else:c=bpy.data.collections.new(n);s.collection.children.link(c)
 c.hide_render=False;c.hide_viewport=False;collections[k]=c
physics=next(c for c in bpy.data.collections if c.name.startswith('11_'))
for ob in list(physics.objects):
 if ob.get('dining_revision'):bpy.data.objects.remove(ob,do_unlink=True)
led=bpy.data.materials.new('Luz LED quente pendentes');led['finish_family']='led';led.use_nodes=True
p=led.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(1.,.65,.29,1);p.inputs['Emission Color'].default_value=(1.,.65,.29,1);p.inputs['Emission Strength'].default_value=3.
targets={'dining':100000,'island':65000,'cylinder':24000,'linear':16000};names={'dining':'Mesa jantar oito cadeiras Meshy','island':'Ilha cozinha quatro banquetas Meshy','cylinder':'Pendente cilindros sala jantar Meshy','linear':'Pendente linear ilha cozinha Meshy'}
transforms={};light_points=[];meshes={}
def box(name,a,b,xf,group,kind):
 points=[xf((x,y,z)) for x,y,z in [(a[0],a[1],a[2]),(b[0],a[1],a[2]),(b[0],b[1],a[2]),(a[0],b[1],a[2]),(a[0],a[1],b[2]),(b[0],a[1],b[2]),(b[0],b[1],b[2]),(a[0],b[1],b[2])]]
 me=bpy.data.meshes.new(name);me.from_pydata(points,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);me.update()
 ob=bpy.data.objects.new(name,me);physics.objects.link(ob);ob['collision_material']=kind;ob['collision_group']=group;ob['dining_revision']=True
for family,row in spec['assets'].items():
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=row['local_source']);objects=[o for o in bpy.data.objects if o not in before];ob=next(o for o in objects if o.type=='MESH');me=ob.data
 me.transform(ob.matrix_world);ob.matrix_world=Matrix.Identity(4);ob.name=names[family]
 for c in list(ob.users_collection):c.objects.unlink(ob)
 collections[family if family in collections else 'lights'].objects.link(ob)
 for other in objects:
  if other!=ob:bpy.data.objects.remove(other,do_unlink=True)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000002)
 assert all(e.is_manifold for e in bm.edges),family
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 if me.has_custom_normals:me.normals_split_custom_set([(0.,0.,0.)]*len(me.loops))
 me.calc_loop_triangles();original=len(me.loop_triangles)
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 mod=ob.modifiers.new('Unir costuras antes de otimizar','DECIMATE');mod.ratio=targets[family]/original;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name)
 bm=bmesh.new();bm.from_mesh(me);assert all(e.is_manifold for e in bm.edges),family;bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
 ps=np.array([v.co for v in me.vertices]);lo=ps.min(0);hi=ps.max(0);center=(hi+lo)*.5
 for m in me.materials:m['finish_family']=family
 ob['preserve_source_uv']=True;ob['component_family']=family;ob['source_glb']=row['local_source']
 luminous=[]
 if family in ('cylinder','linear'):
  me.materials.append(led)
  for face in me.polygons:
   if face.normal.z<-.85 and face.center.z<(lo[2]+.09 if family=='linear' else .37):face.material_index=len(me.materials)-1;luminous.append(face.index)
  assert luminous,family
 if family=='dining':scale=3.9/(hi[1]-lo[1]);angle=0.;xy=(2.65,-8.3)
 elif family=='island':scale=3./(hi[0]-lo[0]);angle=-math.pi/2;xy=(10.1,-9.)
 elif family=='cylinder':scale=2.4/(hi[0]-lo[0]);angle=math.pi/2;xy=(2.65,-8.3)
 else:scale=2.5/(hi[0]-lo[0]);angle=-math.pi/2;xy=(10.45,-9.)
 rot=Matrix.Rotation(angle,4,'Z')
 def xf(q,scale=scale,rot=rot,xy=xy,lo=lo.copy(),hi=hi.copy(),center=center.copy(),family=family):
  pt=rot@Vector(((q[0]-center[0])*scale,(q[1]-center[1])*scale,0))
  if family in ('dining','island'):z=-.795+(q[2]-lo[2])*scale
  else:
   bottom,top=(1.5,6.448) if family=='cylinder' else (1.35,2.356)
   cutlow=.37 if family=='cylinder' else lo[2]+.09;cuthi=hi[2]-.07
   zl=bottom+(cutlow-lo[2])*scale;zh=top-(hi[2]-cuthi)*scale
   if q[2]<=cutlow:z=bottom+(q[2]-lo[2])*scale
   elif q[2]>=cuthi:z=top-(hi[2]-q[2])*scale
   else:z=zl+(q[2]-cutlow)/(cuthi-cutlow)*(zh-zl)
  return Vector((pt.x+xy[0],pt.y+xy[1],z))
 transforms[family]=xf
 # Measure main horizontal surfaces before transforming the model.
 levels={}
 for f in me.polygons:
  c=f.center
  inside=abs(c.x)<(.40 if family=='dining' else .88) and abs(c.y)<(.73 if family=='dining' else .44)
  if family in ('dining','island') and f.normal.z>.9 and inside and c.z>lo[2]+.2:
   z=round(float(c.z),2);levels[z]=levels.get(z,0)+f.area
 topz=max(levels,key=levels.get) if levels else None
 if family=='dining':
  box('Fisica tampo jantar',(-.395,-.76,topz-.032),(.395,.76,topz+.003),xf,'mansao_jantar','WOOD_SOLID_POLISHED')
  for x in (-.32,.32):
   for y in (-.64,.64):box('Fisica pe mesa', (x-.035,y-.035,lo[2]),(x+.035,y+.035,topz-.035),xf,'mansao_jantar','WOOD_SOLID_POLISHED')
  chairs=[(x,y) for x in (-.52,.52) for y in (-.57,0,.57)]+[(0,y) for y in (-.865,.865)]
  for i,(x,y) in enumerate(chairs):
   box('Fisica cadeira jantar '+str(i), (x-.09,y-.10,lo[2]),(x+.09,y+.10,lo[2]+.37),xf,'mansao_jantar','CLOTH')
 elif family=='island':
  box('Fisica corpo ilha',(-.94,-.145,lo[2]),(.94,.43,topz+.002),xf,'mansao_ilha','MARBLE')
  for i,x in enumerate((-.67,-.22,.22,.67)):box('Fisica banqueta '+str(i),(x-.105,-.435,lo[2]),(x+.105,-.23,lo[2]+.48),xf,'mansao_ilha','CLOTH')
 for v in me.vertices:v.co=xf(v.co)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
 for f in me.polygons:f.use_smooth=True
 me.calc_loop_triangles();ps=np.array([v.co for v in me.vertices]);row.update(object=ob.name,original_triangles=original,triangles=len(me.loop_triangles),scale=float(scale),rotation_z_degrees=math.degrees(angle),lo=ps.min(0).tolist(),hi=ps.max(0).tolist(),dimensions=(ps.max(0)-ps.min(0)).tolist(),boundary_edges=0,led_faces=len(luminous),body_scale_uniform=True,cables_adjusted=family in ('cylinder','linear'))
 if topz is not None:row['surface_height_above_floor_m']=float(xf((0,0,topz)).z+.8)
 # Downward-facing light positions measured from the actual emissive mesh caps.
 if family=='cylinder':
  caps=[me.polygons[i] for i in luminous];bins={}
  for f in caps:
   y=int(np.clip(round((float(f.center.y)+9.3)/.4),0,5));bins.setdefault(y,[]).append(f)
  for y,faces in bins.items():
   if sum(f.area for f in faces)<.0005:continue
   area=sum(f.area for f in faces);co=sum((f.center*f.area for f in faces),Vector())/area
   light_points.append(dict(position=[co.x,co.y,co.z-.04],rgb=[255,207,145],range=3.8,intensity=.7))
 elif family=='linear':
  for y in (-9.75,-9.,-8.25):light_points.append(dict(position=[10.45,y,1.30],rgb=[255,207,145],range=3.,intensity=.8))
 print('PLACED_COMPONENT',family,row,flush=True)
physics.hide_render=True;physics.hide_viewport=True
for im in bpy.data.images:
 if im.has_data:
  try:im.pack()
  except Exception:pass
spec['lights']=light_points;spec['floor_z']=-.8;spec['in_game_verified']=False
(W/'componentes_jantar_cozinha.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
(W/'luzes_pendentes.json').write_text(json.dumps(dict(origin=json.loads((W/'medidas_estudo.json').read_text())['native_origin'],lights=light_points),indent=2))
old=json.loads((W/'aplicacao_materiais_sofa.json').read_text());old['revision']=spec['revision'];(W/'aplicacao_materiais_sofa.json').write_text(json.dumps(old,indent=2),encoding='utf-8')
s['status']='Mesa com oito cadeiras, ilha com quatro banquetas e dois pendentes posicionados; exportacao FiveM pendente.'
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_encaixada.blend'));print('DINING_KITCHEN_BLENDER_SAVED',flush=True)
