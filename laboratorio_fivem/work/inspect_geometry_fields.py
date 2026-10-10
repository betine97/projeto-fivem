import sys
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset
from szio.gta5.drawables import LodLevel
root=Path(__file__).resolve().parents[2]/'server-data/resources/cidade_laboratorio/stream'
for name in ('lab_racks','lab_piso','lab_planta_00','lab_ventilacao'):
 a=try_load_asset(root/(name+'.ydr'))
 g=a.models[LodLevel.HIGH][0].geometries[0]
 print(name,'dtype',g.vertex_buffer.dtype,'sample',g.vertex_buffer[0],flush=True)
 for key in list(a.shader_group.embedded_textures)[:3]:
  t=a.shader_group.embedded_textures[key]
  print('texture',key,'dim',t.width,t.height,'format',getattr(t,'format',None),'data',len(t.data.to_bytes()) if hasattr(t.data,'to_bytes') else type(t.data),flush=True)
