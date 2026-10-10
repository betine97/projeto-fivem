import bpy
from pathlib import Path
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_fivem_preparada.blend'))
for m in bpy.data.materials:
 if not m.get('finish_family'):continue
 print('MATERIAL',m.name,m.get('finish_family'),flush=True)
 for n in m.node_tree.nodes:
  if n.type=='UVMAP':print('UV_NODE',n.name,n.uv_map,flush=True)
  if n.type=='TEX_IMAGE':print('TEXTURE_NODE',n.name,n.extension,n.image.name if n.image else None,[(l.from_node.name,l.from_socket.name) for l in n.inputs['Vector'].links],flush=True)
for name in ('Piso terreo contorno nativo','Revestimento continuo terreo 00 0','Sofa e mesa de centro Meshy'):
 ob=bpy.data.objects[name]
 print('OBJECT',name,[(uv.name,uv.active_render,uv.data[0].uv[:]) for uv in ob.data.uv_layers],flush=True)
