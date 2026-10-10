exec(open(__file__.replace('extract_hs.py','locate.py'),encoding='utf-8').read().split('for s in index:')[0])
for s in index:
 parts=s.split('|');stem=Path(parts[-1]).stem
 if s.endswith('.ydr') and re.match(r'ch2_(09|10)_hs',stem):
  f=assets/(stem+'.ydr')
  if not f.exists():f.write_bytes(archive(parts).read_bytes(parts[-1]))
print('EXTRACTED HS')
