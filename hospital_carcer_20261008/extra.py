from locate import *
base=open_rpf(game/'x64l.rpf');out=[]
for folder in ['beverly.rpf','bh1_lod.rpf','beverly_metadata.rpf','bh1_occl.rpf','bh1_22.rpf']:
 a=base.open_nested('levels/gta5/_cityw/beverly_01/'+folder)
 for name in a.list_dir(''):
  if ('22' in name or 'lod' in name or 'occl' in name) and name.endswith(('.ydd','.ymap','.ybn','.ytyp','.ydr')):
   (N/name).write_bytes(a.read_bytes(name));out.append(folder+'|'+name)
(P/'extra_sources.json').write_text(json.dumps(out,indent=2));print(out,flush=True)
for f in N.glob('*.ydd'):
 a=try_load_asset(f);print(f.name,list(a.drawables),flush=True)
# Catalogue variants so no DLC version restores the original block.
def walk(a,folder='',prefix='',depth=0):
 for name in a.list_dir(folder):
  p=folder+'/'+name if folder else name
  if a.is_dir(p):walk(a,p,prefix,depth)
  elif p.endswith('.rpf') and depth<5:
   try:walk(a.open_nested(p),'',prefix+'|'+p,depth+1)
   except Exception:pass
  elif ('bh1_22' in Path(p).name or 'bh1_occl' in Path(p).name) and p.endswith(('.ymap','.ybn','.ydr','.ydd')):
   f=N/Path(p).name
   if not f.exists():f.write_bytes(a.read_bytes(p))
   out.append(prefix+'|'+p)
for f in [game/'update/update.rpf',*list((game/'update/x64/dlcpacks').glob('*/dlc.rpf'))]:
 try:walk(open_rpf(f),prefix=str(f.relative_to(game)))
 except Exception as e:print('ERR',f.name,str(e)[:70],flush=True)
(P/'all_extra_sources.json').write_text(json.dumps(out,indent=2));print('VARIANT_SCAN_COMPLETE',len(out),flush=True)
