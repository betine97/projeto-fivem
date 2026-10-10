import bpy
from pathlib import Path
W=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_iluminada.blend'))
count=0
for m in bpy.data.materials:
 if not m.use_nodes:continue
 for n in m.node_tree.nodes:
  if n.type!='TEX_IMAGE' or not n.image:continue
  name=Path(n.image.filepath.replace('//','')).stem.lower()
  p=W/'work/decor_native'/(name+'.dds')
  if p.exists():
   im=bpy.data.images.load(str(p),check_existing=False)
   if n.name!='DiffuseSampler':im.colorspace_settings.name='Non-Color'
   assert len(im.pixels)>0,(name,p);im.pack();n.image=im;count+=1
assert count>10
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_iluminada.blend'))
print('NATIVE_PLANT_PREVIEW_TEXTURES_PACKED',count,flush=True)
