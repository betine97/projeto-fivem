import bpy,sys,addon_utils,math,json
from pathlib import Path
from mathutils import Vector
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
root=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
names=sorted(p.name for p in (root/'source').glob('*.ydd'))
for i,name in enumerate(names):
 before=set(bpy.data.objects)
 bpy.ops.sollumz.import_assets(directory=str(root/'source'),files=[{'name':name}],use_custom_settings=True,dwd_import_external_skeleton='FROM_DIR')
 for o in set(bpy.data.objects)-before:
  if not o.parent:o.location.x+=(i%8)*1.4;o.location.z-=(i//8)*2.0
 bpy.ops.object.text_add(location=((i%8)*1.4,-.5,-1.12-(i//8)*2.0),rotation=(math.pi/2,0,0))
 t=bpy.context.object;t.data.body=name[:-4];t.data.size=.12;t.data.align_x='CENTER'
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.55,.55,.55)
rows=math.ceil(len(names)/8);sc.render.resolution_x=2000;sc.render.resolution_y=rows*400;sc.render.resolution_percentage=100
cd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',cd);sc.collection.objects.link(cam);cam.location=(4.9,-20,-(rows-1)-.2);cam.rotation_euler=(math.pi/2,0,0);cd.type='ORTHO';cd.ortho_scale=max(11.6,rows*2.0);sc.camera=cam
sc.render.filepath=str(root/'work/catalog.png');bpy.ops.render.render(write_still=True)
print('CATALOG',names)
