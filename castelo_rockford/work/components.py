exec(__import__('pathlib').Path(__file__).with_name('remaining.py').read_text().split('for m in')[0])
from collections import defaultdict
for m in a.models[LodLevel.HIGH]:
 for g in m.geometries:
  if g.shader_index not in [8,13,15]:continue
  vv=g.vertex_buffer['Position']+p;ts=g.index_buffer.reshape(-1,3);d={};parent=list(range(len(ts)))
  def root(i):
   while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
   return i
  for j,ids in enumerate(ts):
   for q in vv[ids]:
    k=tuple(np.round(q,3))
    if k in d:parent[root(j)]=root(d[k])
    else:d[k]=j
  groups=defaultdict(list)
  for j,t in enumerate(ts):groups[root(j)].append(t)
  for ids in groups.values():
   v=vv[np.array(ids).reshape(-1)];mn,mx=v.min(0),v.max(0)
   if mx[2]>67 and -973<mn[0]<-915 and 185<mn[1]<227:print(g.shader_index,len(ids),np.round(mn,3),np.round(mx,3))
