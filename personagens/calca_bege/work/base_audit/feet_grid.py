import bpy,sys,addon_utils,math,json
from pathlib import Path
from mathutils import Vector
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
out=Path(__file__).resolve().parent
base=out.parents[2]/'templates_freemode/source'
heist=out.parents[2]/'traje_laboratorio/source'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
items=[(base,n.name) for n in sorted(base.glob('feet_*.ydd'))]+[(heist,n.name) for n in sorted(heist.glob('feet_*.ydd'))]
for i,(folder,n) in enumerate(items):
 before=set(bpy.data.objects)
 bpy.ops.sollumz.import_assets(directory=str(folder),files=[{'name':n}],use_custom_settings=True,dwd_import_external_skeleton='FROM_DIR')
 for o in set(bpy.data.objects)-before:
  if not o.parent:o.location.x+=(i%5)*.7;o.location.z+=(i//5)*.55+.8
 bpy.ops.object.text_add(location=((i%5)*.7,-.35,(i//5)*.55-.3),rotation=(math.pi/2,0,0))
 t=bpy.context.object;t.data.body=('base ' if folder==base else 'heist ')+n[5:8];t.data.size=.065;t.data.align_x='CENTER'
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.55,.55,.55)
sc.render.resolution_x=1400;sc.render.resolution_y=1100;sc.render.resolution_percentage=100
cd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',cd);sc.collection.objects.link(cam);cam.location=(1.4,-5,2.7);cam.rotation_euler=(Vector((1.4,0,.75))-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=3.65;sc.camera=cam
sc.render.filepath=str(out/'feet_grid.png');bpy.ops.render.render(write_still=True)
