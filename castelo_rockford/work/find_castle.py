exec(__import__('pathlib').Path(__file__).with_name('inspect_assets.py').read_text().split('sources=')[0])
found=[]
for s in (R/'laboratorio_fivem/work/assets_index.txt').read_text().splitlines():
 if 'beverly_metadata.rpf|' not in s or not s.endswith('.ymap'):continue
 p=s.split('|');k='|'.join(p[:-1])
 if k not in cache:cache[k]=open_rpf(G/p[0]).open_nested(p[1])
 f=N/Path(p[-1]).name
 if not f.exists():f.write_bytes(cache[k].read_bytes(p[-1]))
 a=try_load_asset(f)
 for i,e in enumerate(a.entities):
  x,y,z=e.position
  if -1100<x<-700 and 140<y<430:
   found.append(dict(map=f.name,index=i,name=str(e.archetype_name),pos=list(e.position),rot=list(e.rotation),scale=[e.scale_xy,e.scale_xy,e.scale_z],parent=e.parent_index))
(W/'castle_candidates.json').write_text(json.dumps(found,indent=2))
for e in found:
 if 'strm' in e['map'] and e['name'].startswith('bh1') and not any(k in e['name'] for k in ('decal','dtl','detail','ovl','hedg','grass','fur','tree','plnt','plant','ovly')):print(e['map'],e['name'],np.round(e['pos'],2))
