import bpy
from pathlib import Path
W=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_iluminada.blend'))
for o in bpy.data.collections['19_VASOS_NATIVOS'].objects:
 if o.type!='MESH':continue
 for m in o.data.materials:
  if not m or not m.use_nodes:continue
  for n in m.node_tree.nodes:
   if n.type=='TEX_IMAGE' and n.image:print('PLANT_IMAGE',n.name,n.image.name,n.image.filepath,n.image.has_data,len(n.image.pixels),flush=True)
 break
