import bpy,sys,addon_utils,json,math
from pathlib import Path
from mathutils import Vector
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
root=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
names=['uppr_015_r','feet_005_r']+[f'lowr_{i:03}_r' for i in range(16)]
report=[]
for i,name in enumerate(names):
    before=set(bpy.data.objects)
    bpy.ops.sollumz.import_assets(directory=str(root/'source'),files=[{'name':name+'.ydd'}],use_custom_settings=True,dwd_import_external_skeleton='FROM_DIR')
    objs=set(bpy.data.objects)-before
    report.append({'file':name,'objects':[{'name':o.name,'type':o.type,'sollum':o.sollum_type,'verts':len(o.data.vertices) if o.type=='MESH' else 0,'bounds':[list(o.matrix_world@Vector(c)) for c in o.bound_box] if o.type=='MESH' else []} for o in objs]})
    for o in objs:
        if not o.parent:o.location.x+=(i%6)*1.1;o.location.z-=(i//6)*2.2
    bpy.ops.object.text_add(location=((i%6)*1.1,-.4,-1.2-(i//6)*2.2),rotation=(math.pi/2,0,0))
    t=bpy.context.object;t.data.body=name;t.data.size=.10;t.data.align_x='CENTER'
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.55,.55,.55)
sc.render.resolution_x=1600;sc.render.resolution_y=1300;sc.render.resolution_percentage=100
camd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camd);sc.collection.objects.link(cam);cam.location=(2.75,-15,-2.1);cam.rotation_euler=(math.pi/2,0,0);camd.type='ORTHO';camd.ortho_scale=8;sc.camera=cam
sc.render.filepath=str(root/'work/component_grid.png');bpy.ops.render.render(write_still=True)
(root/'work/components.json').write_text(json.dumps(report,indent=2))
