import json,hashlib,shutil,datetime,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';OUT=W/'piano_tapetes_fivem';SERVER=R/'server-data/resources/cidade_mansao'
sys.path.insert(0,str(W/'work/lua_syntax_deps'));from luaparser import ast
q=json.loads((W/'verificacao_piano_tapetes.json').read_text());assert q['passed']
for name,sha in q['files'].items():assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==sha,name
before={p.relative_to(SERVER).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in SERVER.rglob('*') if p.is_file()};changes={'stream/'+n for n in q['files']}|{'fxmanifest.lua'}
backup=W/('backup_antes_piano_tapetes_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));backup.mkdir()
for rel in changes:
 if (SERVER/rel).exists():p=backup/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SERVER/rel,p)
manifest=(SERVER/'fxmanifest.lua').read_text()
if "'stream/mansao_piano_tapetes.ytyp'" not in manifest:manifest+="\nfiles { 'stream/mansao_piano_tapetes.ytyp' }\ndata_file 'DLC_ITYP_REQUEST' 'stream/mansao_piano_tapetes.ytyp'\n"
ast.parse(manifest)
for n in q['files']:shutil.copy2(OUT/n,SERVER/'stream'/n)
(SERVER/'fxmanifest.lua').write_text(manifest,encoding='utf-8')
for rel,sha in before.items():
 if rel not in changes:assert hashlib.sha256((SERVER/rel).read_bytes()).hexdigest()==sha,('Unrelated resource changed',rel)
for n,sha in q['files'].items():assert hashlib.sha256((SERVER/'stream'/n).read_bytes()).hexdigest()==sha,n
result={'passed':True,'installed_files':list(q['files']),'backup':str(backup),'previous_resource_files_preserved':sum(k not in changes for k in before),'walking_routes':len(q['walking_routes']),'resource_reload_required':True,'in_game_verified':False}
(W/'instalacao_piano_tapetes.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('PIANO_AND_TWO_RUGS_INSTALLED',len(q['files']),'native assets;',result['previous_resource_files_preserved'],'previous files preserved',flush=True)
