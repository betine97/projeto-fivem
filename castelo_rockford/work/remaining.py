exec(__import__('pathlib').Path(__file__).with_name('inspect_assets.py').read_text().split('sources=')[0])
from szio.gta5 import LodLevel
a=try_load_asset(W/'package/stream/bh1_45_plot4a_ter_dcs.ydr');p=np.array([-955.2085571289062,209.95240783691406,66.17019653320312])
for m in a.models[LodLevel.HIGH]:
 for g in m.geometries:
  v=g.vertex_buffer['Position']+p;t=v[g.index_buffer.reshape(-1,3)];q=t[t[:,:,2].max(1)>67.3]
  if len(q):print(g.shader_index,len(q),np.round(q.min((0,1)),2),np.round(q.max((0,1)),2))
