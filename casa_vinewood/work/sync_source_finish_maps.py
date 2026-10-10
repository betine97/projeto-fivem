"""Refresh packed source maps, preserving the accepted room and furniture."""
import bpy,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_encaixada.blend'))
cfg=json.loads((W/'materiais_sala.json').read_text())
for m in bpy.data.materials:
 family=m.get('finish_family')
 if family not in ('marble','wall','brick','metal'):continue
 nodes=m.node_tree.nodes;links=m.node_tree.links
 for n in nodes:
  if n.type!='TEX_IMAGE':continue
  normal=any(l.to_node.type=='NORMAL_MAP' or l.to_node.type=='CURVE_RGB' for l in n.outputs['Color'].links)
  n.image=bpy.data.images.load(cfg[family]['normal' if normal else 'diffuse'],check_existing=False)
  if not normal:continue
  n.image.colorspace_settings.name='Non-Color'
  for link in list(n.outputs['Color'].links):
   if link.to_node.type=='NORMAL_MAP':
    target=link.to_socket;inv=nodes.new('ShaderNodeRGBCurve');curve=inv.mapping.curves[1];curve.points[0].location=(0,1);curve.points[1].location=(1,0);inv.mapping.update()
    links.new(n.outputs['Color'],inv.inputs['Color']);links.new(inv.outputs['Color'],target)
for im in bpy.data.images:
 if im.has_data:
  try:im.pack()
  except Exception:pass
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_encaixada.blend'));print('SOURCE_FINISH_MAPS_REFRESHED',flush=True)
