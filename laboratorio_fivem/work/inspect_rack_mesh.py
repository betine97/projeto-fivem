import sys
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset
p=Path(__file__).resolve().parents[2]/'server-data/resources/cidade_laboratorio/stream/lab_racks.ydr'
a=try_load_asset(p)
for lod,models in a.models.items():
 print('LOD',lod,'models',len(models),'verts',sum(len(g.vertex_buffer) for m in models for g in m.geometries),'tris',sum(len(g.index_buffer)//3 for m in models for g in m.geometries),flush=True)
