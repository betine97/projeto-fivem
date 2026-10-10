import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';out=W/'work/decor_art';out.mkdir(exist_ok=True)
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset
a=open_rpf(Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V/update/x64/dlcpacks/mpapartment/dlc.rpf')).open_nested('x64/levels/gta5/props/high/int_mp_h_props.rpf')
names=['apa_mp_h_acc_artwallm_02','apa_mp_h_acc_artwallm_03','apa_mp_h_acc_artwallm_04','apa_mp_h_acc_artwalll_01']
p=out/'apa_int_mp_h_props.ytyp';p.write_bytes(a.read_bytes(p.name));typ=try_load_asset(p)
rows={}
for name in names:
 p=out/(name+'.ydr');p.write_bytes(a.read_bytes(p.name));d=try_load_asset(p)
 pts=np.concatenate([g.vertex_buffer['Position'] for lod in d.models.values() for m in lod for g in m.geometries])
 ar=next(ar for ar in typ.archetypes if str(ar.name)==name)
 rows[name]=dict(lo=pts.min(0).tolist(),hi=pts.max(0).tolist(),texture_dictionary=str(ar.texture_dictionary),shaders=[str(s.preset_filename) for s in d.shader_group.shaders])
 print(name,rows[name],flush=True)
 for key,tex in d.shader_group.embedded_textures.items():(out/(str(key).lower()+'.dds')).write_bytes(tex.data.read_bytes())
 for filename in [str(ar.texture_dictionary)+'.ytd',str(ar.texture_dictionary)+'+hidr.ytd']:
  try:
   p=out/filename;p.write_bytes(a.read_bytes(filename))
   for key,tex in try_load_asset(p).textures.items():(out/(str(key).lower()+'.dds')).write_bytes(tex.data.read_bytes())
  except (FileNotFoundError,KeyError):print('No separate dictionary',filename,flush=True)
(W/'work/decor_art_bounds.json').write_text(json.dumps(rows,indent=2))
