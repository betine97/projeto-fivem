from locate import *
for e in json.loads((P/'entities.json').read_text()):
 if e['map'].startswith('bh1_22'):
  f=N/(e['name']+'.ydr');s=''
  if f.exists():
   a=try_load_asset(f);ps=np.concatenate([g.vertex_buffer['Position'] for ms in a.models.values() for m in ms for g in m.geometries])+e['pos'];s='bounds '+str(np.round(ps.min(0),2))+' '+str(np.round(ps.max(0),2))
  print(e['map'],e['index'],e['name'],np.round(e['pos'],2),e['parent'],e['lod'],s)
print('OTHER FILES')
for s in index:
 if ('.ydd' in s and 'bh1_' in s) or ('bh1_22' in s and not s.endswith('.ydr')):print(s)
