import sys,json,bpy,addon_utils,math,hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
from szio.gta5 import try_load_asset,AssetTarget,AssetFormat,AssetVersion
from Sollumz.ydr.ydrimport import create_drawable
from Sollumz.iecontext import ImportContext,ImportSettings,import_context_scope
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
rows=json.loads((HERE/'entities.json').read_text())
main=next(e for e in rows if e['name']=='ch2_09b_hs05');origin=Vector(main['pos'])
texture_dir=HERE/'textures';texture_dir.mkdir(exist_ok=True)
for f in (HERE/'native').glob('*.ytd'):
 try:
  for name,tex in try_load_asset(f).textures.items():
   path=texture_dir/(name+'.dds')
   if not path.exists():path.write_bytes(tex.data.read_bytes())
 except Exception:pass
col=bpy.data.collections.new('00_FACHADA_NATIVA_REFERENCIA');bpy.context.scene.collection.children.link(col)
report={'entity':main,'parts':[],'meshes':[]}
for e in rows:
 if not e['name'].startswith('ch2_09b_hs05'):continue
 f=HERE/'native'/(e['name']+'.ydr')
 if not f.exists():continue
 a=try_load_asset(f)
 with import_context_scope(ImportContext(f.stem,AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),texture_dir,ImportSettings(False,False,False,False))):o=create_drawable(a,name=f.stem)
 o.location=Vector(e['pos'])-origin
 for x in [o,*o.children_recursive]:
  for c in list(x.users_collection):c.objects.unlink(x)
  col.objects.link(x)
  if x.type=='MESH':
   x['native_reference']=True
   report['meshes'].append({'name':x.name,'bounds':[list(x.matrix_world@Vector(c)) for c in x.bound_box],'materials':[m.name for m in x.data.materials]})
 report['parts'].append({'entity':e,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
for mat in bpy.data.materials:
 if not mat.use_nodes:continue
 texnode=next((n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and 'Diffuse' in n.name),None)
 if texnode and texnode.image:
  n=texnode.image.name.split('.')[0];path=texture_dir/(n+'.dds')
  if path.exists():texnode.image=bpy.data.images.load(str(path),check_existing=True)
bpy.context.view_layer.update()
verts=[x.matrix_world@v.co for x in col.objects if x.type=='MESH' for v in x.data.vertices]
lo=Vector(tuple(min(v[i] for v in verts) for i in range(3)));hi=Vector(tuple(max(v[i] for v in verts) for i in range(3)));center=(lo+hi)/2;size=max(hi-lo)
report['bounds']={'min':list(lo),'max':list(hi)}
# Horizontal mesh faces and facade edge directions identify real dimensions.
faces=[]
for x in col.objects:
 if x.type!='MESH':continue
 for poly in x.data.polygons:
  if abs(poly.normal.z)>.98 and poly.area>.5:
   pts=[list(x.matrix_world@x.data.vertices[i].co) for i in poly.vertices]
   faces.append({'object':x.name,'material':x.data.materials[poly.material_index].name,'area':poly.area,'points':pts})
report['horizontal_faces']=faces
(HERE/'native_measurement.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
s=bpy.context.scene;s.unit_settings.system='METRIC';s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='TEXTURE';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.render.resolution_x=1100;s.render.resolution_y=800;s.render.resolution_percentage=100
for n,d in enumerate([(1,1,.45),(-1,-1,.45),(0,0,2)]):
 bpy.ops.object.camera_add(location=center+Vector(d)*size);c=bpy.context.object;c.rotation_euler=(center-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=size*1.2;s.camera=c;s.render.filepath=str(HERE/f'native_assembly_{n}.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'casa_nativa.blend'))
print('NATIVE ASSEMBLED',main,report['bounds'],flush=True)
