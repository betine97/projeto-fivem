exec(__import__('pathlib').Path(__file__).with_name('inspect_assets.py').read_text().split('sources=')[0])
base=open_rpf(G/'x64l.rpf');report=[]
for p in ['levels/gta5/_cityw/beverly_01/beverly.rpf','levels/gta5/_cityw/beverly_01/bh1_lod.rpf','levels/gta5/_cityw/beverly_01/beverly_metadata.rpf','levels/gta5/_cityw/beverly_01/bh1_occl.rpf']:
 a=base.open_nested(p)
 for name in a.list_dir(''):
  if ((name.endswith('.ydd') or name.endswith('.ytyp')) and ('45' in name or 'lod' in name)) or ('bh1_occl' in name and not (N/name).exists()):
   (N/name).write_bytes(a.read_bytes(name));report.append(p+'|'+name)
(W/'lod_sources.json').write_text(json.dumps(report,indent=2));print('\n'.join(report))
for f in N.glob('*.ydd'):
 a=try_load_asset(f);print('DICTIONARY',f.name,type(a),[str(d.name) for d in a.drawables][:25])
