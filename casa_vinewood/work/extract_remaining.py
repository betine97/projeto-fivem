from pathlib import Path
exec(open(str(Path(__file__).with_name('locate.py')),encoding='utf-8').read().split('for s in index:')[0])
for s in index:
 parts=s.split('|');stem=Path(parts[-1]).stem
 if s.endswith('.ydr') and ('cityhills_02' in s and ('hs' in stem or 'nwbld' in stem)):
  f=assets/(stem+'.ydr')
  if not f.exists():f.write_bytes(archive(parts).read_bytes(parts[-1]))
print('EXTRACTED HS')



