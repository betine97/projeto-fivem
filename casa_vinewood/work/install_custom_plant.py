import sys,json,shutil,hashlib,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=R/'server-data/resources/cidade_mansao';sys.path.insert(0,str(W/'work/lua_syntax_deps'))
from luaparser import ast
report=json.loads((W/'verificacao_vasos_autorais.json').read_text());assert report['passed'] and report['instances']==2
backup=W/('backup_antes_vasos_autorais_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));backup.mkdir();shutil.copy2(D/'fxmanifest.lua',backup/'fxmanifest.lua')
original={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (D/'stream').iterdir() if p.is_file() and p.name not in report['files']}
for name,value in report['files'].items():
 p=W/'vaso_fivem'/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==value
 if (D/'stream'/name).exists():shutil.copy2(D/'stream'/name,backup/name)
 shutil.copy2(p,D/'stream'/name)
p=D/'fxmanifest.lua';s=p.read_text()
if "'stream/mansao_vasos_autorais.ytyp'" not in s:s+="\nfiles { 'stream/mansao_vasos_autorais.ytyp' }\ndata_file 'DLC_ITYP_REQUEST' 'stream/mansao_vasos_autorais.ytyp'\n"
ast.parse(s);p.write_text(s,encoding='utf-8')
for name,value in original.items():assert hashlib.sha256((D/'stream'/name).read_bytes()).hexdigest()==value,name
for name,value in report['files'].items():assert hashlib.sha256((D/'stream'/name).read_bytes()).hexdigest()==value,name
result=dict(passed=True,instances=2,files=report['files'],previous_stream_files_preserved=len(original),backup=str(backup),resource_reload_required=True,in_game_verified=False)
(W/'instalacao_vasos_autorais.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('CUSTOM_PLANTS_INSTALLED',len(report['files']),'assets;',len(original),'previous files preserved',flush=True)
