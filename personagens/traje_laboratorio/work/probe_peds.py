exec(compile((__import__('pathlib').Path(__file__).parent/'probe_suit.py').read_text().split("for name in ['jbib")[0],__file__,'exec'))
for i,p in enumerate(sorted((root/'source/peds').glob('*/*.ydd'))):
 before=set(bpy.data.objects);bpy.ops.sollumz.import_assets(directory=str(p.parent),files=[{'name':p.name}],use_custom_settings=True,dwd_import_external_skeleton='FROM_DIR')
 for o in set(bpy.data.objects)-before:
  if not o.parent:o.location.x=i*1.4
exec(compile((__import__('pathlib').Path(__file__).parent/'probe_suit.py').read_text().split("sc=bpy.context.scene")[1].split("sc.render.filepath")[0].join(['sc=bpy.context.scene','']),__file__,'exec'))
cam.location.x=.7;cd.ortho_scale=3.5;sc.render.resolution_x=1100;sc.render.resolution_y=800
sc.render.filepath=str(root/'work/native_peds.png');bpy.ops.render.render(write_still=True)
