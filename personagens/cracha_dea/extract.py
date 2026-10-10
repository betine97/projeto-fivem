import sys,io,json
from pathlib import Path
sys.path.insert(0,str(Path('personagens/catalogo_nativo').resolve()))
import render_catalog as r
out=r.ROOT/'personagens/cracha_dea'
for kind in ('models','textures'):
 row=next(x for x in r.DATA[kind] if x['collection']=='mp_m_freemode_01_mp_m_heist3' and x['part']=='task' and x['index']==1 and (kind=='models' or x['variant']=='a_uni'))
 asset=r.try_load_asset(r.vpath(row['path']))
 from szio.gta5 import save_asset,AssetTarget,AssetFormat,AssetVersion
 name='task_001_u' if kind=='models' else 'task_diff_001_a_uni'
 save_asset(asset,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),out/'source',name)
 if kind=='textures':
  for name,tex in asset.textures.items():
   r.Image.open(io.BytesIO(tex.data.read_bytes())).save(out/'textures'/(name+'.png'))
   print(name,tex.width,tex.height)
