import bpy,json
from pathlib import Path
bpy.ops.wm.open_mainfile(filepath=str(Path('preparacao_fivem_stage18/warehouse_stage18_preparacao.blend').resolve()))
r={}
for m in bpy.data.materials:
 if not m.users:continue
 r[m.name]={'images':[n.image.name for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image] if m.use_nodes else [],'color':list(m.diffuse_color),'users':m.users}
Path('laboratorio_fivem/work/materials.json').write_text(json.dumps(r,indent=2))
print('MATERIALS',len(r))
