import bpy,sys,addon_utils,math,json,shutil
from pathlib import Path
from mathutils import Vector
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
out=Path(__file__).resolve().parent
base=out.parents[2]/'templates_freemode/source'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
shutil.copy2(base/'mp_m_freemode_01.yft',out/'mp_m_freemode_01.yft')
items=[(out,n) for n in ['jbib_015_u.ydd','berd_000_u.ydd','accs_000_u.ydd','task_000_u.ydd','decl_000_u.ydd','teef_015_u.ydd']]
items += [(base,n) for n in ['feet_005_r.ydd']]
items += [(out,'mp_m_freemode_01_male_freemode_beach^feet_000_r.ydd')]
rows=[]
for i,(folder,n) in enumerate(items):
 before=set(bpy.data.objects)
 bpy.ops.sollumz.import_assets(directory=str(folder),files=[{'name':n}],use_custom_settings=True,dwd_import_external_skeleton='FROM_DIR')
 objs=set(bpy.data.objects)-before
 meshes=[o for o in objs if o.type=='MESH']
 print('AUDIT',n,[(o.name,len(o.data.vertices),len(o.data.polygons)) for o in meshes])
 rows.append({'file':n,'meshes':[{'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'materials':[m.name for m in o.data.materials]} for o in meshes]})
 if i<6:
  for o in objs:o.hide_render=True
 else:
  for o in objs:
   if not o.parent:o.location.x+=(i-6)*.65;o.location.z+=.8
  bpy.ops.object.text_add(location=((i-6)*.65,-.35,-.3),rotation=(math.pi/2,0,0))
  t=bpy.context.object;t.data.body='Base 5 chinelo' if i==6 else 'Beach 0';t.data.size=.07;t.data.align_x='CENTER'
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.55,.55,.55)
sc.render.resolution_x=1200;sc.render.resolution_y=700;sc.render.resolution_percentage=100
cd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',cd);sc.collection.objects.link(cam);cam.location=(.325,-2,.2);cam.rotation_euler=(Vector((.325,0,-.1))-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=1.3;sc.camera=cam
sc.render.filepath=str(out/'feet_compare.png');bpy.ops.render.render(write_still=True)
(out/'base_components.json').write_text(json.dumps(rows,indent=2))
