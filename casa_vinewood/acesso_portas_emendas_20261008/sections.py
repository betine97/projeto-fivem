from diagnose import *
a=try_load_asset(S/'mansao_paredes.ydr')
out=[]
for m in a.models[LodLevel.HIGH]:
 for g in m.geometries:
  ts=g.vertex_buffer['Position'][g.index_buffer.reshape(-1,3)]
  for t in ts:
   seg=[]
   for v,w in zip(t,np.roll(t,-1,axis=0)):
    if (v[2]<1)!=(w[2]<1):seg.append(v+(w-v)*(1-v[2])/(w[2]-v[2]))
   if len(seg)==2 and all(-1.5<q[1]<3 for q in seg):out.append(np.round(seg,4).tolist())
print(json.dumps(out));(P/'wall_sections.json').write_text(json.dumps(out))
