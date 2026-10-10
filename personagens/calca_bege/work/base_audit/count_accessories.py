import sys,json
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset
from szio.gta5.drawables import LodLevel
out=Path(__file__).resolve().parent
rows=[]
for p in sorted(out.glob('accs_*.ydd')):
 a=try_load_asset(p);d=next(iter(a.drawables.values()))
 gs=[g for m in d.models[LodLevel.HIGH] for g in m.geometries]
 row={'file':p.name,'vertices':sum(len(g.vertex_buffer) for g in gs),'triangles':sum(len(g.index_buffer)//3 for g in gs)}
 rows.append(row)
 print(row)
(out/'accessories_inventory.json').write_text(json.dumps(rows,indent=2))
