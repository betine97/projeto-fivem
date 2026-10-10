import bpy,sys,addon_utils,math,json
from pathlib import Path
from mathutils import Vector
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
out=Path(__file__).resolve().parent
base=out.parents[2]/'templates_freemode/source'
heist=out.parents[2]/'traje_laboratorio/source'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
items=[(out,n.name) for n in sorted(out.glob('mp*^feet*.ydd'))]
for i,(folder,n) in enumerate(items):
 before=set(bpy.data.objects)
 bpy.ops.sollumz.import_assets(directory=str(folder),files=[{'name':n}],use_custom_settings=True,dwd_import_external_skeleton='FROM_DIR')
 for o in set(bpy.data.objects)-before:
  if not o.parent:o.location.x+=(i%4)*.7;o.location.z+=(i//4)*.55+.8
 bpy.ops.object.text_add(location=((i%4)*.7,-.35,(i//4)*.55-.3),rotation=(math.pi/2,0,0))
 t=bpy.context.object;t.data.body=n.replace('mp_m_freemode_01_','').replace('^feet_',' ')[:-4];t.data.size=.035;t.data.align_x='CENTER'
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.55,.55,.55)
sc.render.resolution_x=1400;sc.render.resolution_y=1100;sc.render.resolution_percentage=100
cd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',cd);sc.collection.objects.link(cam);cam.location=(1.05,-3,1.5);cam.rotation_euler=(Vector((1.05,0,.25))-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=3.1;sc.camera=cam
sc.render.filepath=str(out/'feet_candidates.png');bpy.ops.render.render(write_still=True)

