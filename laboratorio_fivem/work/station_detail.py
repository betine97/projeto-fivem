import bpy,json
from pathlib import Path
bpy.ops.wm.open_mainfile(filepath=str(Path('laboratorio_fivem/work/station.blend').resolve()))
o=bpy.data.objects['ch3_08_ppbldg003.model'];r=[]
for i,m in enumerate(o.data.materials):
 vs=[o.data.vertices[v].co for p in o.data.polygons if p.material_index==i for v in p.vertices]
 r.append({'idx':i,'name':m.name,'images':[n.image.name for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image],'lo':[min(v[j] for v in vs) for j in range(3)],'hi':[max(v[j] for v in vs) for j in range(3)],'faces':sum(p.material_index==i for p in o.data.polygons)})
Path('laboratorio_fivem/work/station_mats.json').write_text(json.dumps(r,indent=2))
print(json.dumps(r))
