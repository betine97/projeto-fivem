import sys,json,shutil,hashlib,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=R/'server-data/resources/cidade_mansao'
sys.path.insert(0,str(W/'work/lua_syntax_deps'))
from luaparser import ast
report=json.loads((W/'verificacao_decoracao_iluminacao.json').read_text());assert report['passed']
backup=W/('backup_antes_decoracao_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));backup.mkdir()
for name in ('client.lua','fxmanifest.lua','decoracao_iluminacao.json','iluminacao_decorativa.lua'):
 if (D/name).exists():shutil.copy2(D/name,backup/name)
original={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (D/'stream').iterdir() if p.is_file() and p.name not in report['files']}
for name,expected in report['files'].items():
 p=W/'decor_fivem'/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
 if (D/'stream'/name).exists():shutil.copy2(D/'stream'/name,backup/name)
 shutil.copy2(p,D/'stream'/name)
shutil.copy2(W/'decoracao_iluminacao.json',D/'decoracao_iluminacao.json')
script=(W/'work/iluminacao_decorativa.lua').read_text();ast.parse(script);(D/'iluminacao_decorativa.lua').write_text(script,encoding='utf-8')
p=D/'fxmanifest.lua';s=p.read_text()
if "'stream/mansao_decoracao.ytyp'" not in s:
 s+="\nfiles { 'stream/mansao_decoracao.ytyp', 'decoracao_iluminacao.json' }\ndata_file 'DLC_ITYP_REQUEST' 'stream/mansao_decoracao.ytyp'\nclient_script 'iluminacao_decorativa.lua'\n"
ast.parse(s);p.write_text(s,encoding='utf-8')
p=D/'client.lua';s=p.read_text();start=s.find('-- Local lights preserve');end=s.find('-- The native exterior',start)
if start>=0:
 assert end>start;s=s[:start]+'-- Visible ceiling fixtures and stair LEDs: iluminacao_decorativa.lua.\n\n'+s[end:]
ast.parse(s);p.write_text(s,encoding='utf-8')
for p in D.glob('*.lua'):ast.parse(p.read_text(encoding='utf-8'))
for name,old in original.items():assert hashlib.sha256((D/'stream'/name).read_bytes()).hexdigest()==old,name
for name,value in report['files'].items():assert hashlib.sha256((D/'stream'/name).read_bytes()).hexdigest()==value,name
result=dict(passed=True,revision=report['revision'],files=report['files'],existing_stream_files_preserved=len(original),backup=str(backup),resource_reload_required=True,in_game_verified=False)
(W/'instalacao_decoracao_iluminacao.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('DECOR_INSTALLED',len(report['files']),'new native assets;',len(original),'existing stream files preserved',flush=True)
