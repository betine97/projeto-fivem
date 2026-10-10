import sys,json,bpy
from pathlib import Path
from mathutils import Vector
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset,AssetTarget,AssetFormat,AssetVersion
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
from Sollumz.ydr.ydrimport import create_drawable
from Sollumz.iecontext import ImportContext,ImportSettings,import_context_scope
out=Path('laboratorio_fivem/work/base_assets').resolve();r=open_rpf(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V\x64p.rpf').open_nested('levels/gta5/_hills/cityhills_03/ch3_08.rpf')
for n in r.list_dir(''):
 if n.endswith(('.ybn','.ytd')) or 'pp' in n:
  (out/n).write_bytes(r.read_bytes(n))
print('BLDGS',[n for n in r.list_dir('') if 'ppbld' in n])
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
name='ch3_08_ppbldg003'
a=try_load_asset(out/(name+'.ydr'))
with import_context_scope(ImportContext(name,AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),out,ImportSettings(False,False,False,False))):o=create_drawable(a,name=name)
print('BOUNDS',[(x.name,list(x.dimensions)) for x in o.children])
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True
bpy.ops.object.camera_add(location=(-65,45,38));c=bpy.context.object;c.rotation_euler=(Vector((0,0,0))-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=85;s.camera=c
s.render.resolution_x=1100;s.render.resolution_y=800;s.render.resolution_percentage=100;s.render.filepath=str(out.parent/'station.png')
bpy.ops.wm.save_as_mainfile(filepath=str(out.parent/'station.blend'));bpy.ops.render.render(write_still=True)

