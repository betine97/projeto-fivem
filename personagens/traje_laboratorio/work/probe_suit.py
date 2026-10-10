import bpy,sys,addon_utils,math,json
from pathlib import Path
from mathutils import Vector
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
from szio.gta5 import try_load_asset
root=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for name in ['jbib_000_u','lowr_000_r','berd_020_u','feet_000_u']:
 bpy.ops.sollumz.import_assets(directory=str(root/'source'),files=[{'name':name+'.ydd'}],use_custom_settings=True,dwd_import_external_skeleton='FROM_DIR')
texdir=root/'work/textures';texdir.mkdir(exist_ok=True)
for pat in ['jbib_diff_000_a*','lowr_diff_000_a*','berd_diff_020_a*','feet_diff_000_a*']:
 for p in (root/'source').glob(pat):
  for name,t in try_load_asset(p).textures.items():
   with t.data.open() as f:(texdir/(name+'.dds')).write_bytes(f.read())
   img=bpy.data.images.load(str(texdir/(name+'.dds')));img.pack()
   for m in bpy.data.materials:
    if m.node_tree:
     for n in m.node_tree.nodes:
      if n.type=='TEX_IMAGE' and n.image and n.image.name.lower().split('.')[0]==name.lower():n.image=img
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=16;sc.render.resolution_x=650;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
cd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',cd);sc.collection.objects.link(cam);cam.location=(0,-5,0);cam.rotation_euler=(math.pi/2,0,0);cd.type='ORTHO';cd.ortho_scale=2.25;sc.camera=cam
for pos in [(-3,-4,4),(3,-2,1)]:
 d=bpy.data.lights.new('Soft','AREA');o=bpy.data.objects.new('Soft',d);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler();d.energy=400;d.size=4
sc.render.filepath=str(root/'work/native_suit.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/native_suit.blend'))
