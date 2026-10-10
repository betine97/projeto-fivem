import sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path('personagens/catalogo_nativo').resolve()))
import render_catalog as r
base=r.ROOT/'personagens/calca_tatica';stream=r.ROOT/'server-data/resources/cidade_roupas/stream'
d=next(iter(r.try_load_asset(base/'exports/lowr_006_r.ydd').drawables.values()))
for models in d.models.values():
 for model in models:
  for geom in model.geometries:
   v=geom.vertex_buffer
   assert r.np.isfinite(v['Position']).all() and r.np.isfinite(v['Normal']).all()
   assert geom.index_buffer.max()<len(v)
   assert (v['BlendWeights'].sum(1)==255).all()
for name in ['lowr_006_r.ydd','lowr_diff_006_a_whi.ytd','ct_strap_l.ydr','ct_strap_r.ydr','ct_strap_belt.ydr','ct_straps.ytyp']:
 installed=('mp_m_freemode_01_male_heist^'+name) if name.startswith('lowr_') else name
 assert hashlib.sha256((base/'exports'/name).read_bytes()).digest()==hashlib.sha256((stream/installed).read_bytes()).digest()
print('NATIVE_VERIFY_OK: valid indices, finite geometry, normalized skin weights, six installed files match exports')
