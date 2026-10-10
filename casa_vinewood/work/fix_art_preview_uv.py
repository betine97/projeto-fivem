import bpy
from pathlib import Path
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_iluminada.blend'))
col=bpy.data.collections['20_TAPETE_E_QUADROS'];fixed=set()
for o in col.objects:
 if o.type!='MESH':continue
 for m in o.data.materials:
  if not m or m.name in fixed:continue
  if not m.use_nodes:continue
  uv=m.node_tree.nodes.get('UVMap 0')
  if uv:
   for sampler in ('DiffuseSampler','BumpSampler','SpecSampler'):
    tx=m.node_tree.nodes.get(sampler)
    if tx:m.node_tree.links.new(uv.outputs['UV'],tx.inputs['Vector'])
  fixed.add(m.name)
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_iluminada.blend'))
print('ART_PREVIEW_UV_FIXED',len(fixed),flush=True)
