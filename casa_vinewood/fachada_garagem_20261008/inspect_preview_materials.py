import bpy
from pathlib import Path
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'mansao_entrada_garagem.blend'))
for m in bpy.data.materials:
    if not m.use_nodes:continue
    nodes=[(n.name,n.image.name if n.image else None,n.image.filepath if n.image else None) for n in m.node_tree.nodes if n.type=='TEX_IMAGE']
    if any('fach_' in str(n) or 'im_wall_brick_32' in str(n) for n in nodes):print('PREVIEW_MAT',m.name,nodes,flush=True)
