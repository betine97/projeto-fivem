import bpy,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_fivem_preparada.blend'))
rows=[]
for m in bpy.data.materials:
 if not m.use_nodes:continue
 for node in m.node_tree.nodes:
  if node.type!='TEX_IMAGE' or not node.image:continue
  im=node.image
  if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file():
   objects=[o.name for o in bpy.data.objects if o.type=='MESH' and m.name in o.data.materials]
   rows.append(dict(material=m.name,image=im.name,path=im.filepath,size=list(im.size),node_linked=any(q.is_linked for q in node.outputs),objects=objects))
(W/'work/blender_missing_image_links.json').write_text(json.dumps(rows,indent=2))
print('MISSING_BLENDER_IMAGE_LINKS',rows,flush=True)
