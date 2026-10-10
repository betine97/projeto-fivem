"""Apply the supplied finishes and place an optimized copy of the supplied sofa."""
import bpy,bmesh,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps')]
import numpy as np
bpy.ops.wm.open_mainfile(filepath=str(W/'backup_antes_materiais_sofa/mansao_encaixada.blend'))
s=bpy.context.scene;config=json.loads((W/'materiais_sala.json').read_text())
cols={k:next(c for c in bpy.data.collections if c.name.startswith(p)) for k,p in [('outer','01_'),('ground','02_'),('upper','03_'),('slabs','04_'),('stairs','05_'),('ceil','06_')]}
def material(key):
 row=config[key];m=bpy.data.materials.new('Acabamento '+key);m.use_nodes=True;m['finish_family']=key;m['uv_tile_m']=row['tile_m']
 nodes=m.node_tree.nodes;links=m.node_tree.links;p=nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=row['roughness']
 tx=nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(row['diffuse'],check_existing=True);links.new(tx.outputs['Color'],p.inputs['Base Color'])
 tx=nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(row['normal'],check_existing=True);tx.image.colorspace_settings.name='Non-Color'
 inv=nodes.new('ShaderNodeRGBCurve');curve=inv.mapping.curves[1];curve.points[0].location=(0,1);curve.points[1].location=(1,0);inv.mapping.update()
 nm=nodes.new('ShaderNodeNormalMap');links.new(tx.outputs['Color'],inv.inputs['Color']);links.new(inv.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],p.inputs['Normal'])
 return m
mats={key:material(key) for key in ('marble','wall','brick','metal')};counts={k:0 for k in mats}
for key in ('outer','ground','upper'):
 for ob in cols[key].objects:
  if ob.type!='MESH' or ob.name.startswith(('Vidros','Caixilhos')):continue
  ob.data.materials.clear();ob.data.materials.append(mats['wall'])
  for p in ob.data.polygons:p.material_index=0
  counts['wall']+=1
for ob in cols['slabs'].objects:
 if ob.type=='MESH' and max((ob.matrix_world@v.co).z for v in ob.data.vertices)<0:
  ob.data.materials.clear();ob.data.materials.append(mats['marble'])
  for p in ob.data.polygons:p.material_index=0
  counts['marble']+=1
for ob in cols['stairs'].objects:
 if ob.type=='MESH' and any(t in ob.name for t in ('montante','travessa','corrimao')):
  ob.data.materials.clear();ob.data.materials.append(mats['metal'])
  for p in ob.data.polygons:p.material_index=0
  counts['metal']+=1
# The TV finish uses the inward-facing west wall of the double-height living
# room. Split at exact panel limits; existing window and door apertures remain.
tv=[]
for ob in cols['outer'].objects:
 if ob.name not in ('Revestimento continuo terreo 00 0','Revestimento continuo superior 00 0'):continue
 ob.data.materials.append(mats['brick']);bm=bmesh.new();bm.from_mesh(ob.data)
 for y in (-11.6,-6.1):
  bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,y,0),plane_no=(0,1,0),dist=1e-6,clear_inner=False,clear_outer=False)
 bm.normal_update()
 for f in bm.faces:
  center=f.calc_center_median()
  if f.normal.x>.9 and -11.60001<center.y<-6.09999:f.material_index=1
 assert all(e.is_manifold for e in bm.edges),ob.name
 bm.to_mesh(ob.data);bm.free();ob.data.update();tv.append(ob.name)
assert len(tv)==2,tv
counts['brick']=len(tv)
def project_uv(ob):
 mesh=ob.data;uv=mesh.uv_layers[0] if mesh.uv_layers else mesh.uv_layers.new(name='UVMap 0');uv.name='UVMap 0'
 for p in mesh.polygons:
  mat=mesh.materials[p.material_index] if mesh.materials else None;tile=mat.get('uv_tile_m',2.4) if mat else 2.4
  axis=max(range(3),key=lambda i:abs(p.normal[i]));axes=(0,1) if axis==2 else ((0,2) if axis==1 else (1,2))
  for i in p.loop_indices:
   v=ob.matrix_world@mesh.vertices[mesh.loops[i].vertex_index].co;uv.data[i].uv=(v[axes[0]]/tile,v[axes[1]]/tile)
for col in cols.values():
 for ob in col.objects:
  if ob.type=='MESH' and not ob.name.startswith(('Vidros','Caixilhos')):project_uv(ob)
collection=bpy.data.collections.new('10_MOBILIA_SALA');s.collection.children.link(collection)
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(W/'source_assets/sofa_original.glb'))
imported=[o for o in bpy.data.objects if o not in before];meshes=[o for o in imported if o.type=='MESH'];assert len(meshes)==1
sofa=meshes[0];sofa.name='Sofa e mesa de centro Meshy'
for c in list(sofa.users_collection):c.objects.unlink(sofa)
collection.objects.link(sofa);sofa.data.transform(sofa.matrix_world);sofa.matrix_world=Matrix.Identity(4)
sofa.data.calc_loop_triangles();original_count=len(sofa.data.loop_triangles)
bpy.context.view_layer.objects.active=sofa;sofa.select_set(True)
mod=sofa.modifiers.new('Otimizar malha para GTA','DECIMATE');mod.ratio=45000/original_count;mod.use_collapse_triangulate=True
print('OPTIMIZING_SOFA',original_count,'triangles',flush=True);bpy.ops.object.modifier_apply(modifier=mod.name)
sofa.data.calc_loop_triangles();new_count=len(sofa.data.loop_triangles);assert new_count<=55000,new_count
# Clear inherited split normals after topology changes, keeping smooth cushions.
if sofa.data.has_custom_normals:sofa.data.normals_split_custom_set([(0.,0.,0.)]*len(sofa.data.loops))
for p in sofa.data.polygons:p.use_smooth=True
ps=np.array([v.co for v in sofa.data.vertices]);lo=ps.min(0);hi=ps.max(0);scale=float(4.4/(hi[0]-lo[0]));center=(lo+hi)*.5
rotation=Matrix.Rotation(-math.pi/2,4,'Z');offset=Vector((-4.,-8.8,-.795))
for v in sofa.data.vertices:
 q=Vector(((v.co.x-center[0])*scale,(v.co.y-center[1])*scale,(v.co.z-lo[2])*scale));v.co=rotation@q+offset
sofa['preserve_source_uv']=True;sofa['finish_family']='sofa';sofa['uniform_scale']=scale;sofa['source_glb']=str(W/'source_assets/sofa_original.glb')
for m in sofa.data.materials:m['finish_family']='sofa'
# Compact colliders follow the sofa body, chaise and round table separately.
# The open area between the sofa and table remains traversable.
physics=bpy.data.collections.new('11_MOBILIA_COLISAO (oculta)');s.collection.children.link(physics)
def transform(p):return rotation@Vector(((p[0]-center[0])*scale,(p[1]-center[1])*scale,(p[2]-lo[2])*scale))+offset
def collider_box(name,a,b,kind):
 vs=[transform((x,y,z)) for x,y,z in [(a[0],a[1],a[2]),(b[0],a[1],a[2]),(b[0],b[1],a[2]),(a[0],b[1],a[2]),(a[0],a[1],b[2]),(b[0],a[1],b[2]),(b[0],b[1],b[2]),(a[0],b[1],b[2])]]
 fs=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new(name,me);physics.objects.link(ob);ob['collision_material']=kind
collider_box('Colisao sofa principal',(-.94,.12,lo[2]),(.94,.626,.155),'CLOTH')
collider_box('Colisao chaise',(.37,-.34,lo[2]),(.89,.15,-.022),'CLOTH')
bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=.24,depth=.16,location=(0,0,0));ob=bpy.context.object;ob.name='Colisao mesa centro'
for c in list(ob.users_collection):c.objects.unlink(ob)
physics.objects.link(ob)
for v in ob.data.vertices:v.co=transform((v.co.x-.375,v.co.y-.39,v.co.z+lo[2]+.08))
ob['collision_material']='WOOD_SOLID_POLISHED';physics.hide_viewport=True;physics.hide_render=True
points=np.array([v.co for v in sofa.data.vertices]);bounds=dict(lo=points.min(0).tolist(),hi=points.max(0).tolist(),dimensions=(points.max(0)-points.min(0)).tolist())
report=dict(revision='materiais-sofa-2026-10-07',finish_objects=counts,tv_wall_objects=tv,tv_wall_axis='X',tv_wall_plane=-9.056,tv_wall_y_range=[-11.6,-6.1],sofa_original_triangles=original_count,sofa_game_triangles=new_count,sofa_uniform_scale=scale,sofa_rotation_z_degrees=-90,sofa_bounds=bounds,sofa_includes_coffee_table=True,source_uv_preserved=True,physics_components=3,structural_dimensions_preserved=True,in_game_verified=False)
(W/'aplicacao_materiais_sofa.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
for im in bpy.data.images:
 if im.has_data:
  try:im.pack()
  except Exception:pass
s['status']='Texturas fornecidas: marmore terreo, reboco paredes, tijolo painel TV e preto corrimaos; sofa Meshy redimensionado e otimizado.'
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_encaixada.blend'));print('ROOM_FINISHES_AND_SOFA_SAVED',new_count,bounds,flush=True)
