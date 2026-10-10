"""Edit the accepted Blender scene, preserving structural solids and apertures."""
import bpy,bmesh,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps')]
import numpy as np
bpy.ops.wm.open_mainfile(filepath=str(W/'backup_antes_piso_tv_portas/mansao_encaixada.blend'))
s=bpy.context.scene;cfg=json.loads((W/'materiais_sala.json').read_text())
cols={k:next(c for c in bpy.data.collections if c.name.startswith(p)) for k,p in [('outer','01_'),('ground','02_'),('upper','03_'),('slabs','04_'),('furniture','10_'),('physics','11_')]}
mats={k:next(m for m in bpy.data.materials if m.get('finish_family')==k) for k in ('marble','wall')}
# The continuous central hall/mezzanine and stair landing keep wood. Rooms
# across its thresholds receive marble. Bisecting retains a closed 45cm slab.
slab=next(o for o in cols['slabs'].objects if o.name=='Laje superior contorno nativo')
slab.data.materials.append(mats['marble']);marbleidx=len(slab.data.materials)-1
bm=bmesh.new();bm.from_mesh(slab.data)
hall=[-.8,6.4,-3.85,7.525]
for axis,values in [(0,hall[:2]),(1,hall[2:])]:
 for value in values:
  p=[0,0,0];n=[0,0,0];p[axis]=value;n[axis]=1
  bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=p,plane_no=n,dist=1e-6,clear_inner=False,clear_outer=False)
bm.normal_update();areas={'wood':0.,'marble':0.}
for f in bm.faces:
 c=f.calc_center_median();inside=hall[0]-1e-6<c.x<hall[1]+1e-6 and hall[2]-1e-6<c.y<hall[3]+1e-6
 if f.normal.z>.9 and not inside:f.material_index=marbleidx
 if f.normal.z>.9:areas['wood' if inside else 'marble']+=f.calc_area()
assert all(e.is_manifold for e in bm.edges),'Slab must remain closed'
bm.to_mesh(slab.data);bm.free();slab.data.update()
# Upper room partitions are the identical plaster material already used below.
upper_count=0
for ob in cols['upper'].objects:
 if ob.type=='MESH':
  ob.data.materials.clear();ob.data.materials.append(mats['wall'])
  for p in ob.data.polygons:p.material_index=0
  upper_count+=1
for col in (cols['furniture'],cols['physics']):
 for o in list(col.objects):bpy.data.objects.remove(o,do_unlink=True)
def import_closed(filename,family,name,target_tris):
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(W/'source_assets'/filename))
 imported=[o for o in bpy.data.objects if o not in before];ob=next(o for o in imported if o.type=='MESH');ob.name=name
 ob.data.transform(ob.matrix_world);ob.matrix_world=Matrix.Identity(4)
 for c in list(ob.users_collection):c.objects.unlink(ob)
 cols['furniture'].objects.link(ob)
 bm=bmesh.new();bm.from_mesh(ob.data);before_edges=sum(e.is_boundary for e in bm.edges)
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000002)
 assert all(e.is_manifold for e in bm.edges),(name,'Original welded model is not closed')
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
 if ob.data.has_custom_normals:ob.data.normals_split_custom_set([(0.,0.,0.)]*len(ob.data.loops))
 ob.data.calc_loop_triangles();original=len(ob.data.loop_triangles)
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 mod=ob.modifiers.new('Malha unida antes de reduzir','DECIMATE');mod.ratio=target_tris/original;mod.use_collapse_triangulate=True
 bpy.ops.object.modifier_apply(modifier=mod.name)
 bm=bmesh.new();bm.from_mesh(ob.data);boundary=sum(e.is_boundary for e in bm.edges)
 assert boundary==0,(name,boundary)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
 for p in ob.data.polygons:p.use_smooth=True
 ob['preserve_source_uv']=True;ob['finish_family']=family
 for m in ob.data.materials:m['finish_family']=family
 ob.data.calc_loop_triangles()
 print('WELDED_ASSET',family,'original',original,'export',len(ob.data.loop_triangles),'boundary',boundary,flush=True)
 return ob,dict(original_triangles=original,game_triangles=len(ob.data.loop_triangles),boundary_edges_before_welding=before_edges,boundary_edges_after_optimization=boundary)
sofa,sofa_report=import_closed('sofa_original.glb','sofa','Sofa e mesa de centro Meshy',120000)
ps=np.array([v.co for v in sofa.data.vertices]);lo=ps.min(0);hi=ps.max(0);center=(lo+hi)*.5
scale=float(5.2/(hi[0]-lo[0]));rot=Matrix.Rotation(-math.pi/2,4,'Z');offset=Vector((-4.,-8.8,-.795))
def transform(p):return rot@Vector(((p[0]-center[0])*scale,(p[1]-center[1])*scale,(p[2]-lo[2])*scale))+offset
for v in sofa.data.vertices:v.co=transform(v.co)
sofa['uniform_scale']=scale;sofa['source_glb']=str(W/'source_assets/sofa_original.glb')
def collider_box(name,a,b,kind,xf=lambda p:Vector(p)):
 vs=[xf((x,y,z)) for x,y,z in [(a[0],a[1],a[2]),(b[0],a[1],a[2]),(b[0],b[1],a[2]),(a[0],b[1],a[2]),(a[0],a[1],b[2]),(b[0],a[1],b[2]),(b[0],b[1],b[2]),(a[0],b[1],b[2])]]
 fs=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new(name,me);cols['physics'].objects.link(ob);ob['collision_material']=kind
collider_box('Colisao sofa principal',(-.94,.12,lo[2]),(.94,.626,.155),'CLOTH',transform)
collider_box('Colisao chaise',(.37,-.34,lo[2]),(.89,.15,-.022),'CLOTH',transform)
bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.24,depth=.16,location=(0,0,0));ob=bpy.context.object;ob.name='Colisao mesa centro'
for c in list(ob.users_collection):c.objects.unlink(ob)
cols['physics'].objects.link(ob)
for v in ob.data.vertices:v.co=transform((v.co.x-.375,v.co.y-.39,v.co.z+lo[2]+.08))
ob['collision_material']='WOOD_SOLID_POLISHED'
def bounds(ob):
 p=np.array([ob.matrix_world@v.co for v in ob.data.vertices]);return dict(lo=p.min(0).tolist(),hi=p.max(0).tolist(),dimensions=(p.max(0)-p.min(0)).tolist())
sofa_report.update(bounds=bounds(sofa),uniform_scale=scale)
tv,tv_report=import_closed('tv_console_original.glb','tv','Painel TV rack e decoracao Meshy',100000)
ps=np.array([v.co for v in tv.data.vertices]);lo=ps.min(0);hi=ps.max(0);center=(lo+hi)*.5
tvscale=float(4.6/(hi[0]-lo[0]));tvrot=Matrix.Rotation(math.pi/2,4,'Z');tvoffset=Vector((-9.026+hi[1]*tvscale,-8.8,-.795))
def tvtransform(p):return tvrot@Vector(((p[0]-center[0])*tvscale,p[1]*tvscale,(p[2]-lo[2])*tvscale))+tvoffset
for v in tv.data.vertices:v.co=tvtransform(v.co)
tv['uniform_scale']=tvscale;tv['source_glb']=str(W/'source_assets/tv_console_original.glb')
tv_report.update(bounds=bounds(tv),uniform_scale=tvscale,facing_positive_x=True)
# Flat backing and cabinet only: decorations keep a simple physical outline.
bb=tv_report['bounds'];a=bb['lo'];b=bb['hi']
collider_box('Colisao rack TV',(a[0],a[1],a[2]),(b[0],b[1],a[2]+.65),'WOOD_SOLID_POLISHED')
collider_box('Colisao painel TV',(a[0],a[1],a[2]+.65),(a[0]+.12,b[1],b[2]),'WOOD_SOLID_POLISHED')
cols['physics'].hide_viewport=True;cols['physics'].hide_render=True
report=json.loads((W/'backup_antes_piso_tv_portas/aplicacao_materiais_sofa.json').read_text())
report.update(revision='piso-tv-portas-2026-10-07',sofa_game_triangles=sofa_report['game_triangles'],sofa_uniform_scale=scale,sofa_bounds=sofa_report['bounds'],physics_components=5,sofa_quality=sofa_report,tv=tv_report,upper_wood_hall_bounds=hall,upper_floor_surface_m2=areas,upper_wall_objects=upper_count,in_game_verified=False)
(W/'aplicacao_materiais_sofa.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
for im in bpy.data.images:
 if im.has_data:
  try:im.pack()
  except Exception:pass
s['status']='Hall superior em madeira; quartos em marmore; sofa ampliado e sem frestas; painel TV importado.'
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_encaixada.blend'))
print('UPPER_TV_SOFA_SAVED',areas,sofa_report,tv_report,flush=True)
