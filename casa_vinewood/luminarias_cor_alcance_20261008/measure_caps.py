exec((__import__('pathlib').Path(__file__).parent/'inspect_lights.py').read_text().split('for n in')[0])
a=try_load_asset(D/'stream/mansao_pendentes.ydr')
g=next(g for m in a.models[next(k for k in a.models if k.name=='HIGH')] for g in m.geometries if g.shader_index==1 and g.vertex_buffer['Position'][:,0].mean()<5)
p=g.vertex_buffer['Position'];tri=g.index_buffer.reshape(-1,3)
# Merge only coincident positions to reconnect UV/normal seams.
keys=np.round(p,5);_,inverse=np.unique(keys,axis=0,return_inverse=True)
parent=list(range(int(inverse.max())+1))
def root(i):
    while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
    return i
for t in inverse[tri]:
    a,b,c=map(root,t);parent[b]=a;parent[c]=a
groups={}
for t in tri:groups.setdefault(root(int(inverse[t[0]])),[]).append(t)
rows=[]
for ts in groups.values():
    t=p[np.array(ts)];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);area=np.linalg.norm(n,axis=1)/2
    if sum(area)<.0003:continue
    center=np.average(t.mean(1),axis=0,weights=area)
    row={'triangles':len(ts),'area':float(sum(area)),'center':center.tolist(),'min':t.min((0,1)).tolist(),'max':t.max((0,1)).tolist()}
    rows.append(row)
print(json.dumps(sorted(rows,key=lambda r:r['center'][1]),indent=2))
(P/'caps_medidas.json').write_text(json.dumps(rows,indent=2))
