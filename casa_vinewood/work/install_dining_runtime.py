"""Install the validated light configuration and register it with the mansion resource."""
import json,shutil,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=R/'server-data/resources/cidade_mansao'
sys.path.insert(0,str(W/'work/lua_syntax_deps'))
from luaparser import ast
report=json.loads((W/'verificacao_jantar_cozinha.json').read_text());assert report['passed']
script=(W/'work/luzes_pendentes.lua').read_text();ast.parse(script)
shutil.copy2(W/'work/luzes_pendentes.lua',D/'luzes_pendentes.lua');shutil.copy2(W/'luzes_pendentes.json',D/'luzes_pendentes.json')
p=D/'fxmanifest.lua';s=p.read_text()
if "'luzes_pendentes.json'" not in s:s=s.replace("'portas_madeira.json' }","'portas_madeira.json', 'luzes_pendentes.json' }")
if "client_script 'luzes_pendentes.lua'" not in s:s+="\nclient_script 'luzes_pendentes.lua'\n"
ast.parse(s);p.write_text(s,encoding='utf-8')
for name in ('auditoria_client.lua','auditoria_server.lua'):
 p=D/name;s=p.read_text(encoding='utf-8').replace('piso-tv-portas-2026-10-07',report['revision']);ast.parse(s);p.write_text(s,encoding='utf-8')
for p in D.glob('*.lua'):ast.parse(p.read_text(encoding='utf-8'))
assert json.loads((D/'luzes_pendentes.json').read_text())==json.loads((W/'luzes_pendentes.json').read_text())
print('DINING_RUNTIME_INSTALLED 9 light points; all Lua files parsed; manifest registered',flush=True)
