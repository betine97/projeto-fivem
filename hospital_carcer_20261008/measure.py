from locate import *
rows=json.loads((P/'entities.json').read_text());out=[]
for e in rows:
 f=N/(e['name']+'.ydr')
 if not f.exists() or e['rot']!=[1.,0.,0.,0.]:continue
 a=try_load_asset(f)
 if not a.models.get(LodLevel.HIGH):continue
 ps=np.concatenate([g.vertex_buffer['Position'] for m in a.models[LodLevel.HIGH] for g in m.geometries])+e['pos'];lo=ps.min(0);hi=ps.max(0)
 if hi[2]-lo[2]>18 and max(hi[:2]-lo[:2])>20:
  q=dict(**e,lo=lo.tolist(),hi=hi.tolist(),tris=sum(len(g.index_buffer)//3 for m in a.models[LodLevel.HIGH] for g in m.geometries));out.append(q)
print(json.dumps(out,indent=2));(P/'building_bounds.json').write_text(json.dumps(out,indent=2))
