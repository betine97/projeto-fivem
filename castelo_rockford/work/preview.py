import sys,bpy,addon_utils
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1]
sys.path[:0]=[r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz']
addon_utils.enable('Sollumz',default_set=True)
from szio.gta5 import try_load_asset,AssetTarget,AssetFormat,AssetVersion
from Sollumz.ydr.ydrimport import create_drawable
from Sollumz.iecontext import ImportContext,ImportSettings,import_context_scope
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.65,.6,.5);s.display.shading.show_shadows=True;s.display.shading.show_cavity=True
s.render.resolution_x=900;s.render.resolution_y=650;s.render.resolution_percentage=100
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
name=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'bh1_46_mansion01'
after='--after' in sys.argv
f=W/('package/stream' if after else 'originais')/(name+'.ydr');a=try_load_asset(f)
with import_context_scope(ImportContext(f.stem,AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),f.parent,ImportSettings(False,False,False,False))):o=create_drawable(a,name=f.stem)
vs=[x.matrix_world@v.co for x in o.children_recursive if x.type=='MESH' for v in x.data.vertices];lo=Vector(tuple(min(v[i] for v in vs) for i in range(3)));hi=Vector(tuple(max(v[i] for v in vs) for i in range(3)));c0=(lo+hi)/2;size=max(hi-lo)
bpy.ops.object.camera_add(location=c0+Vector((1,-1,.9))*size);c=bpy.context.object;c.rotation_euler=(c0-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=size*1.45;s.camera=c;s.render.filepath=str(W/(name+('_depois' if after else '')+'.png'));bpy.ops.render.render(write_still=True)
