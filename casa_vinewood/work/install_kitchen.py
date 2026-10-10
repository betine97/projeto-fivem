import sys,json,shutil,hashlib,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';OUT=W/'cozinha_fivem';SERVER=R/'server-data/resources/cidade_mansao'
sys.path.insert(0,str(W/'work/lua_syntax_deps'));from luaparser import ast
report=json.loads((W/'verificacao_cozinha_completa.json').read_text());spec=json.loads((W/'cozinha_completa.json').read_text());assert report['passed'] and all(q['passed'] for q in report['walking_routes'].values())
lights=json.loads((W/'verificacao_luz_cozinha.json').read_text());assert lights['passed'] and lights['peak_calls']<=lights['budget'];assert hashlib.sha256((SERVER/'iluminacao_decorativa.lua').read_text().encode()).hexdigest()==lights['script_sha256']
for rel,sha in spec['baseline_hashes'].items():assert hashlib.sha256((SERVER/rel).read_bytes()).hexdigest()==sha,('Installed baseline changed during preparation',rel)
for name,sha in report['files'].items():assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==sha,('Verified source changed',name)
changes={('stream/'+name if Path(name).suffix in ('.ydr','.ymap','.ytyp') else name):OUT/name for name in report['files']}
changes['fxmanifest.lua']=None
before={p.relative_to(SERVER).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in SERVER.rglob('*') if p.is_file()}
backup=W/('backup_antes_cozinha_completa_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));backup.mkdir()
for rel in changes:
 if (SERVER/rel).exists():dest=backup/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SERVER/rel,dest)
manifest=(SERVER/'fxmanifest.lua').read_text()
if "'stream/mansao_cozinha_completa.ytyp'" not in manifest:manifest+="\nfiles { 'stream/mansao_cozinha_completa.ytyp' }\ndata_file 'DLC_ITYP_REQUEST' 'stream/mansao_cozinha_completa.ytyp'\n"
ast.parse(manifest)
for rel,source in changes.items():
 if source is not None:shutil.copy2(source,SERVER/rel)
(SERVER/'fxmanifest.lua').write_text(manifest,encoding='utf-8')
for rel,sha in before.items():
 if rel not in changes:assert hashlib.sha256((SERVER/rel).read_bytes()).hexdigest()==sha,('Unrelated resource changed',rel)
for rel,source in changes.items():
 if source is not None:assert hashlib.sha256((SERVER/rel).read_bytes()).hexdigest()==hashlib.sha256(source.read_bytes()).hexdigest(),rel
# Keep the prior authored decor inputs consistent with the single relocated pot.
for src,dest in [(OUT/'decoracao_iluminacao.json',W/'decoracao_iluminacao.json'),(OUT/'mansao_decoracao.ymap',W/'decor_fivem/mansao_decoracao.ymap')]:
 shutil.copy2(dest,backup/dest.name);shutil.copy2(src,dest)
result={'passed':True,'revision':spec['revision'],'installed_files':list(changes),'previous_resource_files_preserved':sum(rel not in changes for rel in before),'backup':str(backup),'walking_routes':len(report['walking_routes']),'resource_reload_required':True,'in_game_verified':False}
(W/'instalacao_cozinha_completa.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('KITCHEN_INSTALLED',len(changes),'scoped files;',result['previous_resource_files_preserved'],'existing files preserved; no server restart',flush=True)
