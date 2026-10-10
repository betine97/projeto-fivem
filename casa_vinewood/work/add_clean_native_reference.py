import bpy,sys,json,addon_utils,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz']
addon_utils.enable('Sollumz',default_set=True)
from szio.gta5 import try_load_asset,AssetTarget,AssetFormat,AssetVersion
from Sollumz.ydr.ydrimport import create_drawable
from Sollumz.iecontext import ImportContext,ImportSettings,import_context_scope
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_fivem_preparada.blend'))
for c in list(bpy.data.collections):
 if c.name.startswith('91_'):
  for o in list(c.objects):bpy.data.objects.remove(o,do_unlink=True)
  bpy.data.collections.remove(c)
col=bpy.data.collections.new('91_FACHADA_NATIVA_CORRIGIDA_INSTALADA (oculta)');bpy.context.scene.collection.children.link(col)
origin=Vector(json.loads((W/'medidas_estudo.json').read_text())['native_origin'])
for e in json.loads((W/'work/near_house_entities.json').read_text()):
 if not e['name'].startswith('ch2_09b_hs05') or 'lod' in e['name']:continue
 f=W/'fivem'/(e['name']+'.ydr')
 if not f.exists():f=W/'work/native'/(e['name']+'.ydr')
 a=try_load_asset(f)
 with import_context_scope(ImportContext(f.stem,AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),W/'work/textures',ImportSettings(False,False,False,False))):o=create_drawable(a,name='Corrigido '+f.stem)
 o.location=Vector(e['pos'])-origin;o['source_native_file']=str(f);o['sha256']=hashlib.sha256(f.read_bytes()).hexdigest()
 for child in [o,*o.children_recursive]:
  for c in list(child.users_collection):c.objects.unlink(child)
  col.objects.link(child);child['native_reference']=True
for im in bpy.data.images:
 if im.has_data:
  try:im.pack()
  except Exception:pass
col.hide_viewport=True;col.hide_render=True
bpy.context.scene['status']='Revisao jantar-cozinha-2026-10-07: mesa com oito cadeiras, ilha com quatro banquetas, pendente de seis cilindros e pendente linear; sofa, TV, mezanino e cinco portas preservados. Conferencia visual FiveM apos recarregar pendente.'
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_fivem_preparada.blend'))
if '--no-render' in sys.argv:
 print('CLEAN_NATIVE_REFERENCE_SAVED',flush=True)
 sys.exit(0)
# Inspect the actual cut support against the original reference in identical views.
for c in bpy.data.collections:
 if c.name.startswith(('06_','07_','09_','90_','91_')):c.hide_render=True
for o in bpy.data.objects:
 if o.name.startswith('Vidros'):o.hide_render=True
s=bpy.context.scene
bpy.ops.object.camera_add(location=(-6.4,-8.4,.65));cam=bpy.context.object;cam.rotation_euler=(Vector((-6.4,-6.45,-.75))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=32;s.camera=cam
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='TEXTURE';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH'
s.render.resolution_x=1100;s.render.resolution_y=800;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
original=next(c for c in bpy.data.collections if c.name.startswith('90_'))
for name,c in [('antes',original),('depois',col)]:
 c.hide_viewport=False;c.hide_render=False;bpy.context.view_layer.update();s.render.filepath=str(W/('inspecao_suporte_'+name+'.png'));bpy.ops.render.render(write_still=True);c.hide_render=True
print('CLEAN_NATIVE_REFERENCE_SAVED_AND_INSPECTED',flush=True)
