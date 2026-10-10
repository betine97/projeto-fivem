exec(__import__('pathlib').Path(__file__).with_name('inspect_assets.py').read_text().split('sources=')[0])
out=[];seen=set()
def walk(a,folder='',prefix='',depth=0):
 for name in a.list_dir(folder):
  p=folder+'/'+name if folder else name
  if a.is_dir(p):walk(a,p,prefix,depth)
  elif p.endswith('.rpf') and depth<5:
   try:walk(a.open_nested(p),'',prefix+'|'+p,depth+1)
   except Exception:pass
  elif ('bh1_45' in Path(p).name or 'bh1_occl' in Path(p).name) and p.endswith(('.ymap','.ybn','.ydr','.ydd','.ytyp')):
   out.append(prefix+'|'+p);f=N/Path(p).name
   if f.name not in seen:seen.add(f.name);f.write_bytes(a.read_bytes(p))
for f in [G/'update/update.rpf',*list((G/'update/x64/dlcpacks').glob('*/dlc.rpf'))]:
 try:walk(open_rpf(f),prefix=str(f.relative_to(G)))
 except Exception as e:print('ERR',f.name,str(e)[:80])
(W/'dlc_sources.json').write_text(json.dumps(out,indent=2));print('DLC_VARIANTS',len(out));print('\n'.join(out))
