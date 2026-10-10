import sys,json,bpy,addon_utils
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
from szio.gta5 import try_load_asset,AssetTarget,AssetFormat,AssetVersion
from Sollumz.ydr.ydrimport import create_drawable
from Sollumz.iecontext import ImportContext,ImportSettings,import_context_scope
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True
s.render.resolution_x=360;s.render.resolution_y=280;s.render.resolution_percentage=100
dest=HERE/'candidates';dest.mkdir(exist_ok=True)
for f in (HERE/'native').glob('*.ydr'):
 if any(x in f.stem for x in ('dtl','detail','wood','pool','ladder','carpark','_d')):continue
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 try:
  a=try_load_asset(f)
  with import_context_scope(ImportContext(f.stem,AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),f.parent,ImportSettings(False,False,False,False))):o=create_drawable(a,name=f.stem)
  verts=[x.matrix_world@v.co for x in o.children_recursive if x.type=='MESH' for v in x.data.vertices]
  lo=Vector(tuple(min(v[i] for v in verts) for i in range(3)));hi=Vector(tuple(max(v[i] for v in verts) for i in range(3)))
  center=(lo+hi)/2;size=max(hi-lo)
  bpy.ops.object.camera_add(location=center+Vector((1,-1,.65))*size);c=bpy.context.object;c.rotation_euler=(center-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=size*1.4;s.camera=c
  s.render.filepath=str(dest/(f.stem+'.png'));bpy.ops.render.render(write_still=True)
  print('RENDERED',f.stem,flush=True)
 except Exception as ex:print('ERROR',f.name,str(ex),flush=True)
