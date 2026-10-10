"""Keep opaque map extensions intact when removing building attachments."""
exec(__import__('pathlib').Path(__file__).with_name('build.py').read_text().split("names=['bh1_45")[0])
import pymateria.gta5 as pm
report=json.loads((W/'alteracoes.json').read_text())
# Prefer the newest base-map patch rather than earlier patchday revisions.
dlcs=json.loads((W/'dlc_sources.json').read_text())
for name in ['bh1_45_strm_1.ymap']:
 s=next(s for s in dlcs if 'patchday27ng' in s and s.endswith('|'+name));parts=s.split('|');arc=__import__('szio.rpf',fromlist=['open_rpf']).open_rpf(Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V')/parts[0])
 for p in parts[1:-1]:arc=arc.open_nested(p)
 (N/name).write_bytes(arc.read_bytes(parts[-1]))
for f in [N/'bh1_45_strm_1.ymap',N/'hei_bh1_45_strm_1.ymap']:
 a=pm.MapData.import_rsc(f).result;retained=[];removed=[];resolved=try_load_asset(f).entities
 for i,e in enumerate(a.entities):
  p=np.array([e.position.x,e.position.y,e.position.z]);name=str(resolved[i].archetype_name)
  if not name.startswith('bh1') and foot.covers(Point(p[:2])) and p[2]>floor-.5 and p[2]<90:
   assert e.parent_index==-1 and e.num_children==0,(name,e.parent_index,e.num_children)
   removed.append(dict(index=i,name=name,pos=p.tolist()));continue
  retained.append(e)
 a.entities=retained;pm.MapData.export_rsc(a,O/f.name);assert len(pm.MapData.import_rsc(O/f.name).result.entities)==len(retained)
 report['maps'].append(dict(file=f.name,attachments_removed=removed,unknown_extensions_preserved=True));print('ATTACHMENTS',f.name,len(removed))
# The farthest visible model is a region-wide SLOD3. Cut only the castle volume.
from szio.rpf import open_rpf
arc=open_rpf(Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V/x64l.rpf')).open_nested('levels/gta5/_cityw/beverly_01/bh1_lod.rpf')
f=N/'bh1_lod_slod3.ydr';f.write_bytes(arc.read_bytes(f.name));a=try_load_asset(f);n,total=patch_drawable(a,pos['bh1_lod_slod3'])
if n:save_asset(a,TARGET,O,f.stem);assert try_load_asset(O/f.name);report['render'].append(dict(file=f.name,cut=n,before=total));print('FARTHEST_LOD',n)
(W/'alteracoes.json').write_text(json.dumps(report,indent=2))
