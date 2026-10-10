import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset
out=W/'work/decor_native';out.mkdir(exist_ok=True)
names=['v_res_m_palmplant1','prop_plant_int_02a','prop_plant_int_05a','prop_pot_plant_02a','prop_pot_plant_02b']
rows={}
for line in (R/'laboratorio_fivem/work/assets_index.txt').read_text().splitlines():
 parts=line.split('|');name=Path(parts[-1]).stem
 if name not in names or not line.endswith('.ydr'):continue
 p=out/(name+'.ydr')
 if not p.exists():
  a=open_rpf(Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V')/parts[0])
  for sub in parts[1:-1]:a=a.open_nested(sub)
  p.write_bytes(a.read_bytes(parts[-1]))
 a=try_load_asset(p)
 pts=[v for lod in a.models.values() for m in lod for g in m.geometries for v in g.vertex_buffer['Position']]
 lo=[float(min(v[i] for v in pts)) for i in range(3)];hi=[float(max(v[i] for v in pts)) for i in range(3)]
 rows[name]=dict(lo=lo,hi=hi,height=hi[2]-lo[2]);print(name,rows[name],flush=True)
(W/'work/decor_plant_bounds.json').write_text(json.dumps(rows,indent=2))
arch=open_rpf(Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V/x64i.rpf')).open_nested('levels/gta5/props/vegetation/v_potted.rpf')
for name in ('prop_plant_int_02a.ytd','prop_plant_int_02a+hi.ytd','prop_pots_2.ytd','prop_pots_2+hi.ytd'):
 p=out/name;p.write_bytes(arch.read_bytes(name))
 for key,tex in try_load_asset(p).textures.items():
  (out/(str(key).lower()+'.dds')).write_bytes(tex.data.read_bytes())
print('NATIVE_PREVIEW_TEXTURES_EXTRACTED',flush=True)
