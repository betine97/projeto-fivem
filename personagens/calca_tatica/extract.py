import sys,io
from pathlib import Path
sys.path.insert(0,str(Path('personagens/catalogo_nativo').resolve()))
import render_catalog as r
from szio.gta5 import save_asset,AssetTarget,AssetFormat,AssetVersion
out=r.ROOT/'personagens/calca_tatica'
for kind in ('models','textures'):
 row=next(x for x in r.DATA[kind] if x['collection']=='mp_m_freemode_01_male_freemode_business2' and x['part']=='lowr' and x['index']==1 and (kind=='models' or x['variant']=='a_whi'))
 a=r.try_load_asset(r.vpath(row['path'])); name='lowr_001_r' if kind=='models' else 'lowr_diff_001_a_whi'
 save_asset(a,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),out/'source',name)
 if kind=='textures':
  for name,t in a.textures.items():r.Image.open(io.BytesIO(t.data.read_bytes())).save(out/'textures'/(name+'.png'));print(name,t.width,t.height)
